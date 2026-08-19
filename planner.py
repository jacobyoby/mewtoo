"""Two-tier brain: a slower planner model that guides the fast action model.

Version: 0.0.8

The per-step actor (small, fast model) picks one button press at a time and
has no long-horizon view. The PlannerAgent runs a bigger model on a slow
cadence -- every N steps, or immediately on meaningful events (map change,
stuck streak, goal completion) -- and produces a short strategy directive.
That directive is injected into the actor's prompt as extra context, so the
fast lane stays fast while inheriting long-term direction.

Planner output is plain text (2-4 sentences). Reasoning-model preambles
(<think>...</think> blocks, e.g. from qwen3) are stripped before use.
"""
import logging
import re
import time

from llm_provider import LLMProvider

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the strategic planner for an agent playing Pokemon Red.
A separate fast model presses buttons; you set its direction.
Reply with a SHORT directive (2-4 sentences, no markdown):
1. The current objective and the concrete next milestone.
2. Which direction/area to head for, if known.
3. One thing to avoid (e.g. "do not press B in menus", "stop re-entering the house").
Be specific to the situation described. No preamble, no explanations of your reasoning."""

# qwen3-style reasoning block, possibly unterminated when truncated by the
# token limit
_THINK_RE = re.compile(r"<think>.*?(?:</think>|\Z)", re.DOTALL)


class PlannerAgent:
    """Slow-cadence strategy planner feeding directives to the fast actor."""

    def __init__(self, llm_provider: LLMProvider, interval: int = 25,
                 min_gap: int = 10, max_tokens: int = 700, metrics=None):
        """Initialize the planner.

        Args:
            llm_provider: Provider for the (bigger) planning model.
            interval: Plan at least every N steps.
            min_gap: Never plan more often than every N steps, even when
                triggers fire back to back.
            max_tokens: Token budget per planning call. Generous by default
                because reasoning models (qwen3) spend tokens in a stripped
                <think> block before the directive.
            metrics: Optional metrics collector (records planner LLM calls).
        """
        self.llm_provider = llm_provider
        self.interval = max(1, interval)
        self.min_gap = max(1, min_gap)
        self.max_tokens = max_tokens
        self.metrics = metrics

        self.current_plan: str | None = None
        self.last_plan_step: int | None = None
        # Trigger-state tracking
        self._last_map_id: int | None = None
        self._last_completed_count = 0

    def _should_plan(self, step_count: int, game_info: dict,
                     stuck_count: int, completed_goals: int) -> str | None:
        """Return the trigger reason if a plan is due, else None."""
        map_id = (game_info.get('current_map') or {}).get('map_id')

        # Rate limit: never plan twice within min_gap steps
        if self.last_plan_step is not None and step_count - self.last_plan_step < self.min_gap:
            # Still record trigger state so a suppressed event doesn't
            # re-fire forever once the gap opens
            if map_id is not None:
                self._last_map_id = map_id
            self._last_completed_count = max(self._last_completed_count, completed_goals)
            return None

        if self.last_plan_step is None:
            return "initial"
        if map_id is not None and self._last_map_id is not None and map_id != self._last_map_id:
            return "map_change"
        if completed_goals > self._last_completed_count:
            return "goal_completed"
        if stuck_count >= 8:
            return "stuck"
        if step_count - self.last_plan_step >= self.interval:
            return "interval"
        return None

    def maybe_plan(self, step_count: int, game_info: dict, stuck_count: int = 0,
                   strategy_summary: str = "", completed_goals: int = 0) -> str | None:
        """Produce a new plan if one is due; return the current plan either way.

        Never raises: a planner failure logs a warning and the actor keeps
        running on the previous plan (or none).
        """
        reason = self._should_plan(step_count, game_info, stuck_count, completed_goals)
        if reason is None:
            return self.current_plan

        prompt = self._build_prompt(step_count, game_info, stuck_count,
                                    strategy_summary, reason)
        try:
            start = time.time()
            raw = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=PLANNER_SYSTEM_PROMPT,
                max_tokens=self.max_tokens,
            )
            plan = self._clean(raw)
            if plan:
                self.current_plan = plan
                logger.info(f"[PLANNER] Step {step_count} ({reason}): {plan}")
            else:
                logger.warning(f"[PLANNER] Step {step_count} ({reason}): empty plan after cleaning, keeping previous")
            logger.debug(f"[PLANNER] call took {time.time() - start:.1f}s")
        except Exception as e:
            logger.warning(f"[PLANNER] Planning failed ({reason}): {e}; keeping previous plan")

        # Mark the attempt even on failure so errors don't retry every step
        self.last_plan_step = step_count
        map_id = (game_info.get('current_map') or {}).get('map_id')
        if map_id is not None:
            self._last_map_id = map_id
        self._last_completed_count = completed_goals
        return self.current_plan

    def _build_prompt(self, step_count: int, game_info: dict, stuck_count: int,
                      strategy_summary: str, reason: str) -> str:
        map_info = game_info.get('current_map') or {}
        party = game_info.get('party') or []
        parts = [
            f"Step {step_count}. Planning trigger: {reason}.",
            f"Game state: {game_info.get('game_state', 'unknown')}.",
        ]
        if map_info.get('map_name'):
            parts.append(f"Location: {map_info['map_name']}.")
        pos = game_info.get('player_position')
        if pos:
            parts.append(f"Position: {pos}.")
        if party:
            lead = party[0]
            parts.append(f"Party: {len(party)} Pokemon, lead level {lead.get('level', '?')}.")
        else:
            parts.append("Party: empty (starter not obtained yet).")
        if stuck_count:
            parts.append(f"Actor has been stuck for {stuck_count} steps.")
        if strategy_summary:
            parts.append(f"Progress: {strategy_summary}")
        screen_text = (game_info.get('screen_text') or "").strip()
        if screen_text:
            parts.append(f"Screen text: {screen_text[:150]}")
        parts.append("Give the directive.")
        return "\n".join(parts)

    @staticmethod
    def _clean(raw: str) -> str:
        """Strip reasoning blocks and whitespace from planner output."""
        text = _THINK_RE.sub("", raw or "")
        return text.strip()
