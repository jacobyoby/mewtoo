"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Generator


@pytest.fixture
def mock_pyboy():
    """Create a mock PyBoy instance."""
    pyboy = Mock()
    
    # Mock memory access
    memory_dict = {}
    memory_mock = Mock()
    
    def getitem(address):
        return memory_dict.get(address, 0)
    
    def setitem(address, value):
        memory_dict[address] = value
    
    memory_mock.__getitem__ = Mock(side_effect=getitem)
    memory_mock.__setitem__ = Mock(side_effect=setitem)
    pyboy.memory = memory_mock
    
    # Mock other PyBoy attributes
    pyboy.frame_count = 0
    pyboy.screen = Mock()
    pyboy.screen.image = Mock()
    
    # Mock button methods
    pyboy.button_press = Mock()
    pyboy.button_release = Mock()
    pyboy.tick = Mock()
    pyboy.stop = Mock()
    
    return pyboy


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate = Mock(return_value="A")
    provider.check_available = Mock(return_value=True)
    return provider


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        # Player position
        0xD362: 10,  # Player X
        0xD361: 5,   # Player Y
        
        # Current map
        0xD35E: 0x00,  # Map ID (Pallet Town)
        0xD35F: 0x00,  # Map bank
        
        # Player name (ASCII-like encoding)
        0xD158: 0x80,  # 'A'
        0xD159: 0x8C,  # 'M'
        0xD15A: 0x8F,  # 'P'
        0xD15B: 0x7F,  # Space
        0xD15C: 0x50,  # End marker
        
        # Party count
        0xD163: 1,  # 1 Pokemon in party
        
        # First Pokemon data (simplified)
        0xD16B: 25,  # Species (Pikachu)
        0xD16C: 0x20,  # HP current low byte
        0xD16D: 0x03,  # HP current high byte (0x0320 = 800)
        0xD16E: 0x20,  # HP max low byte
        0xD16F: 0x03,  # HP max high byte (0x0320 = 800)
        0xD19C: 50,  # Level (0xD16B + 33 = 0xD19C)
        
        # Inventory
        0xD31D: 2,  # 2 items
        0xD31E: 1,  # Item 1 ID
        0xD31F: 5,  # Item 1 quantity
        0xD320: 2,  # Item 2 ID
        0xD321: 3,  # Item 2 quantity
        
        # Menu state
        0xCC26: 0x00,  # No menu
        0xCC28: 0x00,  # Menu state
        0xD730: 0x00,  # Text box closed
        
        # Battle state
        0xD057: 0x00,  # No battle
        0xCFD8: 0x00,  # Wild Pokemon species
    }

