"""Tests for game_state module."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from game_state import GameState
from memory_reader import MemoryReader


class TestGameState:
    """Test GameState class."""
    
    def test_init(self, mock_pyboy):
        """Test GameState initialization."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        assert game_state.pyboy == mock_pyboy
        assert game_state.screen_width == 160
        assert game_state.screen_height == 144
        assert not game_state.ocr_enabled
        assert game_state.memory_enabled
    
    def test_init_memory_disabled(self, mock_pyboy):
        """Test GameState initialization with memory disabled."""
        game_state = GameState(mock_pyboy, memory_enabled=False)
        
        assert not game_state.memory_enabled
        assert game_state.memory_reader is None
    
    def test_get_screen_image(self, mock_pyboy):
        """Test getting screen image."""
        # Mock screen image
        mock_image = np.array([[0, 1, 2], [3, 4, 5]])
        mock_pyboy.screen.image = mock_image
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        image = game_state.get_screen_image()
        
        assert isinstance(image, np.ndarray)
        np.testing.assert_array_equal(image, mock_image)
    
    @patch('game_state.pytesseract')
    def test_get_screen_text_ocr_disabled(self, mock_tesseract, mock_pyboy):
        """Test getting screen text with OCR disabled."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        text = game_state.get_screen_text()
        
        assert text == ""
        mock_tesseract.image_to_string.assert_not_called()
    
    def test_get_game_info_memory_enabled(self, mock_pyboy):
        """Test getting game info with memory enabled."""
        # Setup mock memory reader
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_full_game_state.return_value = {
            "player_position": (10, 5),
            "current_map": {"map_id": 0x00, "map_bank": 0x00},
            "player_name": "TEST",
            "party": [],
            "health": {"total_hp": 0, "total_max_hp": 0, "total_hp_percent": 0, "party_size": 0, "fainted_count": 0},
            "inventory": [],
            "menu": {"menu_type": 0x00, "menu_name": "none", "menu_state": 0, "text_box_open": False},
            "battle": {"in_battle": False, "battle_type": 0, "battle_type_name": "none", "wild_pokemon_species": 0},
        }
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        info = game_state.get_game_info()
        
        assert 'player_position' in info
        assert 'current_map' in info
        assert 'game_state' in info
        assert info['player_position'] == (10, 5)
    
    def test_get_game_info_memory_disabled(self, mock_pyboy):
        """Test getting game info with memory disabled."""
        game_state = GameState(mock_pyboy, ocr_enabled=False, memory_enabled=False)
        
        info = game_state.get_game_info()
        
        assert 'game_state' in info
        assert 'memory_enabled' in info
        assert not info['memory_enabled']
    
    def test_press_button(self, mock_pyboy):
        """Test pressing a button."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        game_state.press_button("A", hold_frames=1)
        
        mock_pyboy.button_press.assert_called_once_with("a")
        mock_pyboy.button_release.assert_called_once_with("a")
        assert mock_pyboy.tick.call_count >= 2
    
    def test_press_button_invalid(self, mock_pyboy):
        """Test pressing an invalid button."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        with pytest.raises(ValueError):
            game_state.press_button("INVALID")
    
    def test_execute_action_single(self, mock_pyboy):
        """Test executing a single action."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        result = game_state.execute_action("A")
        
        assert result is True
        mock_pyboy.button_press.assert_called_once_with("a")
    
    def test_execute_action_multiple(self, mock_pyboy):
        """Test executing multiple actions."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        result = game_state.execute_action("A, B")
        
        assert result is True
        assert mock_pyboy.button_press.call_count == 2
    
    def test_execute_action_wait(self, mock_pyboy):
        """Test executing WAIT action."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        result = game_state.execute_action("WAIT 5")
        
        assert result is True
        assert mock_pyboy.tick.call_count == 5
    
    def test_execute_action_invalid(self, mock_pyboy):
        """Test executing invalid action."""
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        
        result = game_state.execute_action("INVALID")
        
        assert result is False
    
    def test_get_player_position(self, mock_pyboy):
        """Test getting player position."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_player_position.return_value = (10, 5)
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        pos = game_state.get_player_position()
        
        assert pos == (10, 5)
    
    def test_get_player_position_memory_disabled(self, mock_pyboy):
        """Test getting player position with memory disabled."""
        game_state = GameState(mock_pyboy, ocr_enabled=False, memory_enabled=False)
        
        pos = game_state.get_player_position()
        
        assert pos == (0, 0)
    
    def test_get_current_map(self, mock_pyboy):
        """Test getting current map."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_current_map.return_value = {
            "map_id": 0x00,
            "map_bank": 0x00
        }
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        map_info = game_state.get_current_map()
        
        assert map_info['map_id'] == 0x00
        assert 'map_name' in map_info
    
    def test_get_pokemon_party(self, mock_pyboy):
        """Test getting Pokemon party."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_pokemon_party.return_value = [
            {"slot": 1, "species": 25, "level": 50, "hp_current": 800, "hp_max": 800}
        ]
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        party = game_state.get_pokemon_party()
        
        assert len(party) == 1
        assert party[0]['species'] == 25
    
    def test_get_health_hp(self, mock_pyboy):
        """Test getting health/HP."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_health_hp.return_value = {
            "party": [],
            "total_hp": 800,
            "total_max_hp": 800,
            "total_hp_percent": 100.0,
            "party_size": 1,
            "fainted_count": 0,
        }
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        health = game_state.get_health_hp()
        
        assert health['total_hp'] == 800
        assert health['total_hp_percent'] == 100.0
    
    def test_get_inventory(self, mock_pyboy):
        """Test getting inventory."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_inventory.return_value = [
            {"slot": 1, "item_id": 1, "quantity": 5}
        ]
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        inventory = game_state.get_inventory()
        
        assert len(inventory) == 1
        assert inventory[0]['item_id'] == 1
    
    def test_get_menu_state(self, mock_pyboy):
        """Test getting menu state."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.detect_menu_state.return_value = {
            "menu_type": 0x01,
            "menu_name": "start_menu",
            "menu_state": 0,
            "text_box_open": False,
        }
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        menu = game_state.get_menu_state()
        
        assert menu['menu_name'] == "start_menu"
    
    def test_get_battle_state(self, mock_pyboy):
        """Test getting battle state."""
        mock_memory_reader = Mock(spec=MemoryReader)
        mock_memory_reader.read_battle_state.return_value = {
            "in_battle": True,
            "battle_type": 0x01,
            "battle_type_name": "wild",
            "wild_pokemon_species": 16,
        }
        
        game_state = GameState(mock_pyboy, ocr_enabled=False)
        game_state.memory_reader = mock_memory_reader
        
        battle = game_state.get_battle_state()
        
        assert battle['in_battle']
        assert battle['battle_type_name'] == "wild"

