"""Tests for memory_reader module."""
import pytest
from unittest.mock import Mock, MagicMock
from memory_reader import MemoryReader, MemoryAddresses, get_map_name


class TestMemoryAddresses:
    """Test MemoryAddresses constants."""
    
    def test_memory_addresses_defined(self):
        """Test that all memory addresses are defined."""
        assert hasattr(MemoryAddresses, 'PLAYER_X')
        assert hasattr(MemoryAddresses, 'PLAYER_Y')
        assert hasattr(MemoryAddresses, 'CURRENT_MAP')
        assert hasattr(MemoryAddresses, 'PARTY_COUNT')
        assert hasattr(MemoryAddresses, 'INVENTORY_COUNT')
        assert hasattr(MemoryAddresses, 'MENU_TYPE')
        assert hasattr(MemoryAddresses, 'BATTLE_TYPE')
    
    def test_memory_addresses_values(self):
        """Test that memory addresses have valid values."""
        assert MemoryAddresses.PLAYER_X == 0xD362
        assert MemoryAddresses.PLAYER_Y == 0xD361
        assert MemoryAddresses.CURRENT_MAP == 0xD35E
        assert MemoryAddresses.PARTY_COUNT == 0xD163


class TestMemoryReader:
    """Test MemoryReader class."""
    
    def test_init(self, mock_pyboy):
        """Test MemoryReader initialization."""
        reader = MemoryReader(mock_pyboy)
        assert reader.pyboy == mock_pyboy
    
    def test_read_byte(self, mock_pyboy, sample_memory_data):
        """Test reading a single byte from memory."""
        # Setup mock memory
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        
        # Test reading player X
        x = reader.read_byte(MemoryAddresses.PLAYER_X)
        assert x == 10
        
        # Test reading player Y
        y = reader.read_byte(MemoryAddresses.PLAYER_Y)
        assert y == 5
    
    def test_read_byte_fallback(self, mock_pyboy):
        """Test read_byte fallback when memory access fails."""
        # Remove memory attribute
        delattr(mock_pyboy, 'memory')
        
        reader = MemoryReader(mock_pyboy)
        result = reader.read_byte(0xD362)
        assert result == 0
    
    def test_read_word(self, mock_pyboy, sample_memory_data):
        """Test reading a 16-bit word from memory."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        
        # Test reading HP (little-endian)
        # 0xD16C = 0x20, 0xD16D = 0x03 -> 0x0320 = 800
        hp = reader.read_word(0xD16C)
        assert hp == 0x0320  # 800 in decimal
    
    def test_read_bytes(self, mock_pyboy, sample_memory_data):
        """Test reading multiple bytes from memory."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        
        # Read player name bytes
        name_bytes = reader.read_bytes(0xD158, 5)
        assert len(name_bytes) == 5
        assert name_bytes[0] == 0x80  # 'A'
    
    def test_read_player_position(self, mock_pyboy, sample_memory_data):
        """Test reading player position."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        x, y = reader.read_player_position()
        
        assert x == 10
        assert y == 5
    
    def test_read_current_map(self, mock_pyboy, sample_memory_data):
        """Test reading current map."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        map_info = reader.read_current_map()
        
        assert map_info['map_id'] == 0x00
        assert map_info['map_bank'] == 0x00
    
    def test_read_player_name(self, mock_pyboy, sample_memory_data):
        """Test reading player name."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        name = reader.read_player_name()
        
        # Should decode Game Boy characters
        assert isinstance(name, str)
        assert len(name) > 0
    
    def test_read_pokemon_party(self, mock_pyboy, sample_memory_data):
        """Test reading Pokemon party."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        party = reader.read_pokemon_party()
        
        assert len(party) == 1
        assert party[0]['species'] == 25
        assert party[0]['level'] == 50
        assert party[0]['hp_current'] == 800
        assert party[0]['hp_max'] == 800
        assert party[0]['hp_percent'] == 100.0
        assert not party[0]['fainted']
    
    def test_read_pokemon_party_empty(self, mock_pyboy):
        """Test reading empty party."""
        def getitem(address):
            if address == MemoryAddresses.PARTY_COUNT:
                return 0
            return 0
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        party = reader.read_pokemon_party()
        
        assert len(party) == 0
    
    def test_read_health_hp(self, mock_pyboy, sample_memory_data):
        """Test reading health/HP values."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        health = reader.read_health_hp()
        
        assert health['party_size'] == 1
        assert health['total_hp'] == 800
        assert health['total_max_hp'] == 800
        assert health['total_hp_percent'] == 100.0
        assert health['fainted_count'] == 0
    
    def test_read_inventory(self, mock_pyboy, sample_memory_data):
        """Test reading inventory."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        inventory = reader.read_inventory()
        
        assert len(inventory) == 2
        assert inventory[0]['item_id'] == 1
        assert inventory[0]['quantity'] == 5
        assert inventory[1]['item_id'] == 2
        assert inventory[1]['quantity'] == 3
    
    def test_read_inventory_empty(self, mock_pyboy):
        """Test reading empty inventory."""
        def getitem(address):
            if address == MemoryAddresses.INVENTORY_COUNT:
                return 0
            return 0
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        inventory = reader.read_inventory()
        
        assert len(inventory) == 0
    
    def test_detect_menu_state(self, mock_pyboy, sample_memory_data):
        """Test detecting menu state."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        menu = reader.detect_menu_state()
        
        assert menu['menu_type'] == 0x00
        assert menu['menu_name'] == 'none'
        assert not menu['text_box_open']
    
    def test_read_battle_state(self, mock_pyboy, sample_memory_data):
        """Test reading battle state."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        battle = reader.read_battle_state()
        
        assert not battle['in_battle']
        assert battle['battle_type'] == 0x00
        assert battle['battle_type_name'] == 'none'
    
    def test_read_battle_state_in_battle(self, mock_pyboy):
        """Test reading battle state when in battle."""
        def getitem(address):
            if address == MemoryAddresses.BATTLE_TYPE:
                return 0x01  # Wild battle
            elif address == MemoryAddresses.WILD_POKEMON_SPECIES:
                return 16  # Pidgey
            return 0
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        battle = reader.read_battle_state()
        
        assert battle['in_battle']
        assert battle['battle_type'] == 0x01
        assert battle['battle_type_name'] == 'wild'
        assert battle['wild_pokemon_species'] == 16
    
    def test_read_full_game_state(self, mock_pyboy, sample_memory_data):
        """Test reading full game state."""
        def getitem(address):
            return sample_memory_data.get(address, 0)
        mock_pyboy.memory.__getitem__ = Mock(side_effect=getitem)
        
        reader = MemoryReader(mock_pyboy)
        state = reader.read_full_game_state()
        
        assert 'player_position' in state
        assert 'current_map' in state
        assert 'player_name' in state
        assert 'party' in state
        assert 'health' in state
        assert 'inventory' in state
        assert 'menu' in state
        assert 'battle' in state


class TestMapNames:
    """Test map name functions."""
    
    def test_get_map_name(self):
        """Test getting map name from ID."""
        assert get_map_name(0x00) == "Pallet Town"
        assert get_map_name(0x01) == "Viridian City"
        assert get_map_name(0x0B) == "Route 1"
    
    def test_get_map_name_unknown(self):
        """Test getting name for unknown map ID."""
        name = get_map_name(0xFF)
        assert "Map FF" in name or "Map 255" in name

