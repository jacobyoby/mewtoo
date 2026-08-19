"""Deterministic handling for Pokemon Red's early-game naming screens.

Version: 0.0.7

The generic "always press A during character creation" policy cannot complete
the game's naming sequence: pressing A on the NAME? menu (cursor on NEW NAME)
enters the letter grid, where further A presses just type letters forever.
Baseline validation measured 0% success for the get_starter goal because no
run ever finished naming the player and rival.

This module recognizes the two naming screens from (possibly garbled) OCR text
and issues short scripted button sequences that complete them deterministically:

- NAME? preset menu (NEW NAME / RED / ASH / JACK):
    DOWN, A  -> selects the first preset name. Fastest reliable exit.
- Letter grid (reached if the menu was missed and NEW NAME was entered):
    A, START, A  -> type one letter, jump the cursor to ED, confirm.
- YES/NO confirmation boxes while the party is still empty (e.g. "Do you want
  CHARMANDER?"):
    A  -> cursor defaults to YES in Gen 1.

The handler disables itself permanently once the party is non-empty (starter
obtained), so these text heuristics cannot misfire later in the game.
"""


class EarlyGameHandler:
    """Recognizes early-game naming screens and returns scripted actions."""

    # Screen types, in priority order (grid is checked before menu because a
    # garbled grid screen can also contain menu-like fragments).
    GRID = "letter_grid"
    NAMING_MENU = "naming_menu"
    CONFIRM = "yes_no_confirm"

    # Scripted button sequence per screen type.
    SCRIPTS = {
        NAMING_MENU: ["DOWN", "A"],
        GRID: ["A", "START", "A"],
        CONFIRM: ["A"],
    }

    # If the same screen type persists, replay its script at most this many
    # times before yielding control back to the normal decision logic (the
    # screen evidently isn't what we thought it was).
    MAX_REPLAYS = 2

    # OCR-tolerant fragments identifying the NAME? preset menu. The full
    # marker is "NEW NAME"; partial matches cover common OCR dropouts.
    _MENU_FRAGMENTS = ("NEWNAME", "EWNAME", "NEWNAM", "NEWMAME", "NEVNAME")

    # Alphabet runs identifying the letter-grid screen. OCR only needs to get
    # one row's worth of consecutive letters right.
    _GRID_FRAGMENTS = ("ABCDEF", "GHIJKL", "MNOPQR", "STUVWX", "UVWXYZ")

    def __init__(self):
        self._active_type: str | None = None
        self._script_index = 0
        self._replays = 0
        self._done = False  # Latched once the party is non-empty

    @staticmethod
    def _normalize(text: str) -> str:
        """Uppercase and strip everything but letters, so OCR spacing/
        punctuation noise doesn't break substring matching."""
        return "".join(c for c in text.upper() if c.isalpha())

    def _classify(self, norm_text: str, game_state: str) -> str | None:
        """Classify the current screen from normalized OCR text."""
        if any(frag in norm_text for frag in self._GRID_FRAGMENTS):
            return self.GRID
        if any(frag in norm_text for frag in self._MENU_FRAGMENTS):
            return self.NAMING_MENU
        # YES/NO boxes only matter pre-starter; require YES explicitly and a
        # dialog/menu-ish state so plain overworld text can't trigger it.
        if "YES" in norm_text and game_state in ("dialog", "menu", "unknown"):
            return self.CONFIRM
        return None

    def next_action(self, screen_text: str, game_state: str,
                    party_size: int) -> str | None:
        """Return a scripted action for a recognized naming screen, or None.

        Args:
            screen_text: Raw OCR text from the screen (may be garbled).
            party_size: Current party size; any Pokemon means naming and
                starter selection are behind us, so the handler latches off.

        Returns:
            A button action string, or None to fall through to normal logic.
        """
        if self._done:
            return None
        if party_size > 0:
            self._done = True
            self._active_type = None
            return None

        screen_type = self._classify(self._normalize(screen_text or ""), game_state)

        if screen_type is None:
            self._active_type = None
            return None

        if screen_type != self._active_type:
            # New screen type: start its script from the top.
            self._active_type = screen_type
            self._script_index = 0
            self._replays = 0

        script = self.SCRIPTS[screen_type]

        if self._script_index >= len(script):
            # Script finished but the screen didn't change. Replay a couple of
            # times (button presses can be dropped mid-animation), then give up
            # and let the normal decision logic take over.
            if self._replays >= self.MAX_REPLAYS:
                return None
            self._replays += 1
            self._script_index = 0

        action = script[self._script_index]
        self._script_index += 1
        return action

    @property
    def is_done(self) -> bool:
        """True once the starter has been obtained and the handler is off."""
        return self._done
