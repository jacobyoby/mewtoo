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
