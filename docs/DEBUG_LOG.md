# Live-ROM Debug Log

## 2026-08-18 — first real-hardware session (v0.0.8 work)

Fix chain, in discovery order. Each was masked by the one before it.

| # | Symptom (visible in window) | Root cause | Fix (commit) |
|---|---|---|---|
| 1 | Frozen on white boot screen | Agent started at frame 60; content appears ~600. ~3 frames/step | boot wait 600, hold 8f, WAIT=15f units (f4faaae) |
| 2 | Stuck at title "loading" | >=80% white counted as blank even with text; menus unreadable | blank needs <2% dark pixels too (96650ce) |
| 3 | Cursor roulette in menus | forced exploration mashed arrows outside overworld | overworld-only (96650ce) |
| 4 | Walking in place in bedroom | 8-frame d-pad hold only turns; a tile step needs ~16 held frames | directional hold 18f (784f2d8) |
| 5 | Arrow-mashing at Oak's speech | OCR dead all along: tesseract off PATH -> TesseractNotFoundError every call | probe /opt/homebrew/bin etc. (e5b0…) |
| 6 | Same, after OCR fix | memory path called any valid-position screen "overworld", never checked for a dialog box | dialog check in memory path (commit "Oak cutscene fix") |
| 7 | Camped in START menu | memory reports "start_menu"; escape policy matched only "menu"; B blocked by re-arming creation window | substring match + creation window closes on first overworld |
| 8 | B-mashing at nothing (bedroom) | Gen 1 never zeroes menu RAM; memory says "pokemon_menu" forever after a menu closes | phantom-menu latch: 7 futile B presses -> treat as overworld |

Also this session: two-tier brain (gemma3:4b actor + qwen3:8b planner),
scripted naming handler validated on hardware, --load-state resume flag,
save state at roms/pokemon_red.gb.state (bedroom, post-naming).

Diagnostic pattern that worked every time: pull the newest
logs/screenshots/stuck_*.png and compare what the screen SHOWS against
what the JSON log SAYS the state was. Every bug was a perception gap,
not a decision gap.

| 9 | A/B alternation vs invisible menu | 0xCC26 "MENU_TYPE" is a stale menu cursor index — read 2 ("pokemon_menu") for all 800 steps of overworld walking | classify dialog/menu by pixels (detect_text_box) |
| 10 | 330 dialog steps parked at one tile | facing the bedroom TV: A re-opens its text box the instant it closes, so "dialog -> A" loops forever | dialog-loop breaker: 25 same-tile dialog steps -> B, then step away |
| 11 | Every bedroom step logged "dialog" with no text box on screen | the Oak-cutscene fix keyed on OCR text length > 10; the bedroom wallpaper OCRs as ~40 chars of garbage every frame | dialog = detect_text_box() pixels only |
| 12 | Still "dialog" everywhere after #11 | the "ALWAYS validate overworld" block re-added dialog via detect_dialog_box_visually(), which reads the wallpaper as a text box | all 8 classification call sites -> detect_text_box() |
| 13 | Outdoors in Pallet Town, every step "dialog" again | text-box detector keyed on brightness alone; outdoor ground tiles are 67% white | add mid-tone test: box 3% mid-greys vs tiles 28% |
| 14 | Reaches Oak's Lab, stalls at the ball table, never gets a starter | game rule, not a bug: the balls are untakeable until Oak's cutscene fires, which requires trying to leave Pallet Town north to Route 1 | get_starter leaves the lab until Route 1 (0x0B) has been visited |
| 15 | Route encoded correctly but runs still wandered into the lab | the route was only a *suggestion*, competing with random exploration and the LLM for control | promote it to _route_policy in the chain: on a known map it wins, yielding only when stuck or blocked |
| 16 | Oscillates Pallet Town <-> Red's House 1F | leaving a building drops you directly below its door facing south, so "head north" walks straight back inside | door-exit maneuver: step DOWN then LEFT clear of the doorway before resuming north |
| 17 | Door-exit maneuver never fired | strategy.update_phase() ran only inside get_prompt(), i.e. only when the chain reached the LLM — the route policy short-circuits before that, so map transitions went unseen | update_phase() now runs every step() |
| 18 | Touches Pallet Town's north edge (y=1) then drifts back to the lab | Route 1's exit is one column in the north fence; the route yielded whenever UP was blocked, handing control to random exploration | edge-scan: a blocked route direction sweeps laterally along the wall looking for the gap |

Note: test_metrics_track_cache_operations flaked once during a live emulator
run (passed in isolation and on re-run) — resource contention, not a defect.
| 19 | Edge-scan swept the whole north fence (x=1,3,6..10) but never crossed to Route 1 | blocked_directions is global, not per-tile: once UP was marked blocked at one fence tile it stayed blocked at every column, so the gap column was never tried | retry the route direction every third scan step |
| 20 | Navigation never lands on a target tile; three ticks of fence-sweeping failed | measured on the real ROM: an 18-frame directional hold commits **two** tile steps per press (x moved by 2 each time). Holds of 8-16 frames move exactly one | directional hold 18 -> 12 frames; scripts/probe_pallet_exit.py added for ground-truth probing |

Probe findings (scripts/probe_pallet_exit.py, from a Pallet Town save state):
- 0xD361 = Y, 0xD362 = X; the agent's reported (x, y) orientation is correct.
- Walking north from columns 1-5 enters Red's House; 6-11 stay in town.
- Coordinates only read coherently with a >=24-frame settle after release.

## Blocked: Pallet Town exit (as of 2026-08-18 22:40)

Re-probed with correct single-tile movement (hold 12). Walking north from
each column of Pallet Town:

    x=5   -> Red's House door
    x=10  -> reaches the top row (10,1), then a hard wall: 7 further UP
             presses do not move the player
    others-> blocked at y=2 or y=6 by buildings/fences

No column crossed into Route 1. A follow-up sweep along the top edge
returned self-contradictory coordinates (x jumped 10 -> 7 after a single
RIGHT), so blind coordinate probing has hit its limit: interior maps use
their own coordinate frame and the reads are only trustworthy on a
settled overworld frame.

Next approaches, in order of promise:
1. Vision — gemma3:4b is a multimodal model. Feed it the screenshot so it
   can see the map instead of navigating by coordinate heuristics.
2. Map data — read Pallet Town's connection table from the ROM header
   rather than probing for the exit tile.
3. Keep probing with a settle-and-verify wrapper around every move.

## Vision lane added (2026-08-18, after the Pallet Town blocker)

gemma3:4b is multimodal, verified on a real frame: given the Oak dialog
screenshot it answered "a dialog text box is open... 'Okay! It's time to
go!'" — it read the actual text. ~7.6s per call, far too slow for
per-step use, so VisionAdvisor runs only on a genuine stall
(stuck_count >= 6) with a 12-step cooldown, and answers one narrow
question: which direction is open. Failures are non-fatal (returns None).

## Vision evaluated (2026-08-19)

Measured, not assumed:
- gemma3:4b **does** read these frames — it transcribed Oak's dialog from
  a screenshot, and scene descriptions differ correctly per frame
  ("storefront with shelves" vs "small town with paths, fences").
- It **cannot** do 4-way spatial navigation. Asked which direction is
  open, it returns a constant regardless of the frame: "RIGHT" for every
  screen under the one-word prompt, "DOWN" for every screen under a
  describe-then-decide prompt.

So visual navigation is a capability limit of a 4B model at 160x144, not
a prompting problem. The advisor now retires itself after 4 identical
answers rather than dragging the agent one direction into a wall.

Vision remains valuable for what it demonstrably does well (reading text
and identifying screen contents). For the Pallet Town exit specifically,
the ROM map-connection data (option 2 in the earlier blocker note) is the
approach that can actually settle it.

## SOLVED: the Pallet Town "wall" was Oak (2026-08-19)

There was never a wall. Driving the emulator directly and screenshotting
the pinned tile showed **"OAK: Hey!"** — stepping onto (10, 1) fires the
cutscene. Every probe had been pressing UP into a scripted dialog and
reading the resulting no-op as a fence.

Measured facts now encoded:
- Pallet Town is 20x18 tiles. The map header's width/height are in
  BLOCKS (2x2 tiles), so the earlier "bounded" probe searched half the map.
- Oak's trigger tile is (10, 1), the top-right corner of walkable ground.
  Every other column walls out at y=2 or y=6; x=5 is Red's house door.
- Pressing A through the cutscene carries the player into Oak's Lab
  automatically (~40 presses), ending at (5, 3) with Oak asking
  "Now, RED, which POKEMON do you want?".
- Movement is locked during that prompt, and pressing A while facing Oak
  just replays it — the ball grab needs the player to step aside first.

## Lab ball-grab: characterized, not yet solved

After the Oak cutscene the player is free (movement unlocks ~25 A presses
in, with settle >= 30 frames — shorter settles silently swallow presses).
But every attempt to take a ball snaps back to (5, 3):

    press A anywhere near Oak -> his "which POKEMON do you want?" prompt
    re-opens -> player is locked at (5, 3) again

So the ball approach must avoid pressing A while adjacent to Oak: walk
clear of him first (down/right), approach a ball from below, and only
then interact. That is the next thing to encode.

Input timing note worth keeping: dialog advance needs hold=8 with
settle>=30. At settle=18 presses are dropped and long cutscenes appear to
hang.

## Where the starter stands (end of 2026-08-19 session)

The agent reaches Oak's Lab autonomously; the ball grab is unsolved.
Tried and rejected this session:
- approach from each side / each facing at (5,3)
- pure movement with no A presses (script still pulls the player back)
- 14 randomized 45-press sequences from the post-cutscene state

Every path ends the same way: the player is returned to (5, 3) with
Oak's "which POKEMON do you want?" prompt re-opened. Something in that
script is consuming input in a way the probes have not modelled.

Save states available for the next session:
- roms/pokemon_red.gb.state  bedroom, post-naming
- roms/pallet_town.state     outside, in Pallet Town
- roms/lab_free.state        mid Oak cutscene

Next approach worth trying: instrument WHY input is ignored — log
wJoyIgnore / the script-state bytes each press, instead of guessing button
sequences. Or have a human take the starter once (scripts/play_manual.py
auto-saves to roms/has_starter.state the moment party size changes) and
let the agent resume from there.
