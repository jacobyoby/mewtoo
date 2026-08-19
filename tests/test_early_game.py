"""Unit tests for the early-game naming-screen handler."""
from early_game import EarlyGameHandler


class TestScreenClassification:
    """Screen-type detection from (possibly garbled) OCR text."""

    def test_detects_naming_menu(self):
        handler = EarlyGameHandler()
        norm = handler._normalize("NEW NAME\nRED\nASH\nJACK")
        assert handler._classify(norm, "menu") == EarlyGameHandler.NAMING_MENU

    def test_detects_naming_menu_with_ocr_noise(self):
        handler = EarlyGameHandler()
        # Garbled spacing/punctuation and a dropped leading character
        norm = handler._normalize("~EW NAME. r3D A5H")
        assert handler._classify(norm, "menu") == EarlyGameHandler.NAMING_MENU

    def test_detects_letter_grid(self):
        handler = EarlyGameHandler()
        norm = handler._normalize("A B C D E F G H I\nJ K L M N O P Q R")
        assert handler._classify(norm, "menu") == EarlyGameHandler.GRID

    def test_grid_takes_priority_over_menu(self):
        # A garbled grid screen can also contain menu-like fragments
        handler = EarlyGameHandler()
        norm = handler._normalize("NEW NAME U V W X Y Z")
        assert handler._classify(norm, "menu") == EarlyGameHandler.GRID

    def test_detects_yes_no_confirm_in_dialog(self):
        handler = EarlyGameHandler()
        norm = handler._normalize("Do you want CHARMANDER? YES NO")
        assert handler._classify(norm, "dialog") == EarlyGameHandler.CONFIRM

    def test_yes_ignored_in_overworld_state(self):
        handler = EarlyGameHandler()
        norm = handler._normalize("YES")
        assert handler._classify(norm, "overworld") is None

    def test_plain_dialog_not_classified(self):
        handler = EarlyGameHandler()
        norm = handler._normalize("OAK: Hello there! Welcome to the world of POKEMON!")
        assert handler._classify(norm, "dialog") is None


class TestScriptedSequences:
    """Action sequences returned for recognized screens."""

    def test_naming_menu_sequence_selects_preset(self):
        handler = EarlyGameHandler()
        text = "NEW NAME RED ASH JACK"
        # DOWN to move off NEW NAME onto the first preset, A to select it
        assert handler.next_action(text, "menu", 0) == "DOWN"
        assert handler.next_action(text, "menu", 0) == "A"

    def test_letter_grid_sequence_types_and_confirms(self):
        handler = EarlyGameHandler()
        text = "ABCDEFGHI JKLMNOPQR STUVWXYZ ED"
        # A types a letter, START jumps to ED, A confirms
        assert handler.next_action(text, "menu", 0) == "A"
        assert handler.next_action(text, "menu", 0) == "START"
        assert handler.next_action(text, "menu", 0) == "A"

    def test_confirm_screen_presses_a(self):
        handler = EarlyGameHandler()
        assert handler.next_action("Do you want BULBASAUR? YES NO", "dialog", 0) == "A"

    def test_unrecognized_screen_returns_none(self):
        handler = EarlyGameHandler()
        assert handler.next_action("PALLET TOWN", "overworld", 0) is None

    def test_screen_change_resets_script(self):
        handler = EarlyGameHandler()
        menu_text = "NEW NAME RED ASH JACK"
        grid_text = "ABCDEFGHI JKLMNOPQR"
        assert handler.next_action(menu_text, "menu", 0) == "DOWN"
        # Screen switches to the grid mid-script: grid script starts fresh
        assert handler.next_action(grid_text, "menu", 0) == "A"
        assert handler.next_action(grid_text, "menu", 0) == "START"
        # Back to a menu (rival naming): menu script starts fresh too
        assert handler.next_action(menu_text, "menu", 0) == "DOWN"

    def test_persistent_screen_replays_then_gives_up(self):
        handler = EarlyGameHandler()
        text = "NEW NAME RED ASH JACK"
        script_len = len(EarlyGameHandler.SCRIPTS[EarlyGameHandler.NAMING_MENU])
        total_scripted = script_len * (1 + EarlyGameHandler.MAX_REPLAYS)
        actions = [handler.next_action(text, "menu", 0) for _ in range(total_scripted)]
        assert all(a is not None for a in actions)
        # Screen never changed despite initial run + MAX_REPLAYS: yield control
        assert handler.next_action(text, "menu", 0) is None

    def test_gap_between_naming_screens_resets(self):
        """Dialog between player and rival naming re-arms the menu script."""
        handler = EarlyGameHandler()
        menu_text = "NEW NAME RED ASH JACK"
        assert handler.next_action(menu_text, "menu", 0) == "DOWN"
        assert handler.next_action(menu_text, "menu", 0) == "A"
        # Ordinary dialog in between (falls through to normal logic)
        assert handler.next_action("OAK: This is my grandson.", "dialog", 0) is None
        # Rival naming menu: script starts from the top again
        assert handler.next_action(menu_text, "menu", 0) == "DOWN"
        assert handler.next_action(menu_text, "menu", 0) == "A"


class TestLatchOff:
    """Handler disables itself permanently once the starter is obtained."""

    def test_nonempty_party_latches_off(self):
        handler = EarlyGameHandler()
        text = "Do you want to give a nickname? YES NO"
        assert handler.next_action(text, "dialog", 1) is None
        assert handler.is_done

    def test_stays_off_even_if_party_reads_empty_later(self):
        """A transient bad memory read must not re-arm the handler."""
        handler = EarlyGameHandler()
        assert handler.next_action("YES NO", "dialog", 1) is None
        assert handler.next_action("NEW NAME RED ASH JACK", "menu", 0) is None

    def test_active_before_latch(self):
        handler = EarlyGameHandler()
        assert not handler.is_done
        assert handler.next_action("NEW NAME RED", "menu", 0) == "DOWN"


class TestAgentIntegration:
    """The agent consults the handler before its generic policies."""

    def test_agent_uses_scripted_action_on_naming_menu(self, mock_llm_provider, mock_pyboy):
        from unittest.mock import Mock

        from game_state import GameState
        from pokemon_agent import PokemonAgent

        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)

        game_state.get_game_info = Mock(return_value={
            "screen_text": "NEW NAME RED ASH JACK",
            "frame_count": 100,
            "game_state": "menu",
            "party": [],
        })

        # Generic character-creation policy would return A here; the scripted
        # handler must win and return DOWN (move to the first preset name).
        assert agent.get_action() == "DOWN"

    def test_agent_falls_through_when_handler_declines(self, mock_llm_provider, mock_pyboy):
        from unittest.mock import Mock

        from game_state import GameState
        from pokemon_agent import PokemonAgent

        game_state = GameState(mock_pyboy, ocr_enabled=False)
        agent = PokemonAgent(mock_llm_provider, game_state)

        game_state.get_game_info = Mock(return_value={
            "screen_text": "",
            "frame_count": 100,
            "game_state": "overworld",
            "party": [{"species": 1, "level": 5}],
        })

        # No naming screen: normal logic runs and returns something valid
        action = agent.get_action()
        assert action is not None
        assert action != "DOWN" or action in ("UP", "DOWN", "LEFT", "RIGHT")
