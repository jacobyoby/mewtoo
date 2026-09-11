#!/usr/bin/env python3
"""Claude Code PreToolUse hook: keep the commit-msg hook from being bypassed.

Reads the Bash tool call from stdin (Claude Code hook JSON) and exits 2 with a
reason when the command would skip git hooks for a commit. Exit 0 lets the
call through. Nothing here rewrites the command; it only refuses the evasions.

Blocked, in commands that invoke `git commit`:
  --no-verify / -n (and -n inside a flag cluster such as -anm)
  -c core.hooksPath=... / --config-env / core.hooksPath overrides
  HOME=, GIT_DIR=, GIT_CONFIG_GLOBAL= prefixes that relocate the hooks
  git config ... core.hooksPath (changing where hooks live)
Also blocked: writing over .git/hooks/commit-msg or a .githooks/commit-msg.

Wire it in .claude/settings.json:
  {"hooks": {"PreToolUse": [{"matcher": "Bash",
     "hooks": [{"type": "command", "command": "python3 <path>/guard.py"}]}]}}
"""
import json
import re
import shlex
import sys


def deny(reason: str) -> None:
    # Exit code 2 = block the tool call; stderr is shown to Claude as feedback.
    sys.stderr.write(f"commit-cleaner guard: {reason}\n")
    sys.exit(2)


def segments(cmd: str):
    """Split a shell command into simple-command word lists, unwrapping one
    layer of `bash -c '...'`, `sh -c`, `eval`, and $(...)/backtick bodies."""
    # Pull out substitution bodies so nested commands are inspected too.
    bodies = [cmd]
    bodies += re.findall(r"\$\(([^()]*)\)", cmd)
    bodies += re.findall(r"`([^`]*)`", cmd)
    out = []
    for body in bodies:
        for piece in re.split(r"(?<!\\)(?:&&|\|\||;|\||\n)", body):
            piece = piece.strip()
            if not piece:
                continue
            try:
                words = shlex.split(piece, posix=True)
            except ValueError:
                words = piece.split()
            if not words:
                continue
            out.append(words)
            # one layer of wrapper: bash -c "...", sh -lc "...", eval "..."
            low = [w.lower() for w in words]
            if low[0] in ("bash", "sh", "zsh", "dash") and any(
                a.startswith("-") and "c" in a for a in low[1:3]
            ):
                inner = next((w for w in words[1:] if not w.startswith("-")), "")
                out.extend(segments(inner))
            elif low[0] == "eval":
                out.extend(segments(" ".join(words[1:])))
    return out


def check(words):
    # Strip leading VAR=value assignments but remember them.
    env = {}
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        k, _, v = words[0].partition("=")
        env[k] = v
        words = words[1:]
    if not words:
        return
    if words[0] in ("env",):
        words = words[1:]
        while words and ("=" in words[0] or words[0].startswith("-")):
            if "=" in words[0]:
                k, _, v = words[0].partition("=")
                env[k] = v
            words = words[1:]
    if not words or words[0] != "git":
        # Tampering with the hook file itself.
        joined = " ".join(words)
        if re.search(r"hooks/commit-msg|\.githooks/commit-msg", joined) and words[0] in (
            "rm", "mv", "cp", "chmod", "truncate", "tee", "sed", "install", "ln",
        ):
            deny("refusing to modify or remove the commit-msg hook")
        return

    # Locate the git subcommand and its global options.
    opts, i = [], 1
    while i < len(words) and words[i].startswith("-"):
        opts.append(words[i])
        if words[i] in ("-c", "-C", "--git-dir", "--work-tree", "--config-env", "--exec-path"):
            if i + 1 < len(words):
                opts.append(words[i + 1])
            i += 1
        i += 1
    if i >= len(words):
        return
    sub, args = words[i], words[i + 1:]

    if sub == "config" and any("hookspath" in a.lower() for a in args):
        deny("changing core.hooksPath would disable the commit-msg hook")

    if sub != "commit":
        return

    for a in args:
        if a in ("--no-verify",) or a.startswith("--no-verif"):
            deny("`--no-verify` skips the commit-msg hook; commit without it")
        if re.match(r"^-[a-zA-Z]*n[a-zA-Z]*$", a):  # -n, -an, -anm ...
            deny("`-n` (--no-verify) skips the commit-msg hook; commit without it")
    for o in opts:
        if "hookspath" in o.lower():
            deny("overriding core.hooksPath on the command line skips the hook")
    if any(o == "--git-dir" or o.startswith("--git-dir=") for o in opts):
        deny("relocating --git-dir for a commit bypasses the repository hooks")
    for k in ("HOME", "GIT_DIR", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_PARAMETERS", "XDG_CONFIG_HOME"):
        if k in env:
            deny(f"setting {k} for a commit can relocate the hooks; commit without it")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if payload.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if "commit" not in cmd and "hooks" not in cmd.lower():
        sys.exit(0)
    for words in segments(cmd):
        check(list(words))
    sys.exit(0)


if __name__ == "__main__":
    main()
