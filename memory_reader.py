"""Memory reader for Pokemon Red game state.

This module provides functions to read game state directly from Pokemon Red's
memory addresses using PyBoy. All addresses are for Pokemon Red (USA) version.

Memory addresses reference:
- Based on Pokemon Red disassembly and Game Boy memory mapping
- WRAM addresses (0xC000-0xDFFF) are used for game state
"""

from typing import Dict, List, Optional, Tuple
from pyboy import PyBoy


# Memory addresses for Pokemon Red
class MemoryAddresses:
    """Pokemon Red memory addresses."""
    
    # Player position and map
    PLAYER_X = 0xD362  # Player X coordinate on current map
    PLAYER_Y = 0xD361  # Player Y coordinate on current map
    CURRENT_MAP = 0xD35E  # Current map ID
    MAP_HEADER_BANK = 0xD35F  # Map header bank
    
    # Player info
    PLAYER_NAME_START = 0xD158  # Player name (11 bytes, terminated by 0x50)
    PLAYER_NAME_END = 0xD162
    
    # Party Pokemon (up to 6 Pokemon)
    PARTY_COUNT = 0xD163  # Number of Pokemon in party (0-6)
    PARTY_POKEMON_START = 0xD16B  # First Pokemon data structure
    POKEMON_DATA_SIZE = 44  # Size of each Pokemon data structure
    
    # Pokemon data structure offsets (relative to party Pokemon start)
    POKEMON_SPECIES = 0  # Pokemon species ID
    POKEMON_HP_CURRENT = 1  # Current HP (2 bytes, little-endian)
    POKEMON_HP_MAX = 3  # Max HP (2 bytes, little-endian)
    POKEMON_STATUS = 5  # Status condition (0x00 = normal)
    POKEMON_TYPE1 = 6
    POKEMON_TYPE2 = 7
    POKEMON_LEVEL = 33  # Level
    POKEMON_EXP = 34  # Experience (3 bytes)
    
    # Inventory
    INVENTORY_COUNT = 0xD31D  # Number of items in inventory
    INVENTORY_START = 0xD31E  # Inventory items (each item is 2 bytes: item_id, quantity)
    INVENTORY_MAX = 20  # Maximum number of inventory slots
    
    # Menu state
    MENU_TYPE = 0xCC26  # Current menu type
    MENU_STATE = 0xCC28  # Menu state/cursor position
    
    # Battle state
    BATTLE_TYPE = 0xD057  # Battle type (0x00 = no battle, 0x01 = wild, 0x02 = trainer)
    WILD_POKEMON_SPECIES = 0xCFD8  # Wild Pokemon species (if in battle)
    
    # Game state flags
    GAME_STATE = 0xD72C  # Various game state flags
    TEXT_BOX_FLAG = 0xD730  # Text box open flag


class MemoryReader:
    """Reads game state from Pokemon Red memory."""
    
    def __init__(self, pyboy: PyBoy):
        """Initialize memory reader with PyBoy instance.
        
        Args:
            pyboy: PyBoy emulator instance
        """
        self.pyboy = pyboy
    
    def read_byte(self, address: int) -> int:
        """Read a single byte from memory.
        
        Args:
            address: Memory address (0x0000-0xFFFF)
            
        Returns:
            Byte value (0-255)
        """
        try:
            # Try different PyBoy API methods for memory access
            # PyBoy 2.0+ uses memory[address]
            if hasattr(self.pyboy, 'memory'):
                if isinstance(self.pyboy.memory, (list, tuple)) or hasattr(self.pyboy.memory, '__getitem__'):
                    return self.pyboy.memory[address]
            
            # Alternative: PyBoy might use mb (memory bank)
            if hasattr(self.pyboy, 'mb'):
                if hasattr(self.pyboy.mb, 'getitem'):
                    return self.pyboy.mb.getitem(address)
                elif hasattr(self.pyboy.mb, '__getitem__'):
                    return self.pyboy.mb[address]
            
            # Fallback: try direct attribute access
            if hasattr(self.pyboy, 'get_memory_value'):
                return self.pyboy.get_memory_value(address)
            
            return 0
        except (IndexError, AttributeError, TypeError, KeyError) as e:
            # Return 0 on any error (address might not be accessible yet)
            return 0
    
    def read_word(self, address: int) -> int:
        """Read a 16-bit word (little-endian) from memory.
        
        Args:
            address: Memory address of first byte
            
        Returns:
            16-bit value
        """
        try:
            low = self.read_byte(address)
            high = self.read_byte(address + 1)
            return low | (high << 8)
        except (IndexError, AttributeError):
            return 0
    
    def read_bytes(self, address: int, count: int) -> List[int]:
        """Read multiple bytes from memory.
        
        Args:
            address: Starting memory address
            count: Number of bytes to read
            
        Returns:
            List of byte values
        """
        try:
            return [self.read_byte(address + i) for i in range(count)]
        except (IndexError, AttributeError):
            return [0] * count
    
    def read_player_position(self) -> Tuple[int, int]:
        """Read player position (X, Y coordinates).
        
        Returns:
            Tuple of (x, y) coordinates
        """
        x = self.read_byte(MemoryAddresses.PLAYER_X)
        y = self.read_byte(MemoryAddresses.PLAYER_Y)
        return (x, y)
    
    def read_current_map(self) -> Dict[str, int]:
        """Read current map/location information.
        
        Returns:
            Dictionary with map_id and map_bank
        """
        map_id = self.read_byte(MemoryAddresses.CURRENT_MAP)
        map_bank = self.read_byte(MemoryAddresses.MAP_HEADER_BANK)
        return {
            "map_id": map_id,
            "map_bank": map_bank,
        }
    
    def read_player_name(self) -> str:
        """Read player name from memory.
        
        Returns:
            Player name string
        """
        name_bytes = self.read_bytes(
            MemoryAddresses.PLAYER_NAME_START,
            MemoryAddresses.PLAYER_NAME_END - MemoryAddresses.PLAYER_NAME_START + 1
        )
        
        # Convert Game Boy character encoding to ASCII
        # Game Boy uses a custom character set
        name = ""
        for byte in name_bytes:
            if byte == 0x50:  # End marker
                break
            if 0x80 <= byte <= 0x99:  # A-Z
                name += chr(ord('A') + (byte - 0x80))
            elif 0x9A <= byte <= 0xB3:  # a-z
                name += chr(ord('a') + (byte - 0x9A))
            elif 0xB4 <= byte <= 0xBD:  # 0-9
                name += chr(ord('0') + (byte - 0xB4))
            elif byte == 0x7F:  # Space
                name += " "
            elif byte == 0xE0:  # Period
                name += "."
            elif byte == 0xE1:  # Comma
                name += ","
            elif byte == 0xE2:  # Exclamation
                name += "!"
            elif byte == 0xE3:  # Question
                name += "?"
            elif byte == 0xE8:  # Apostrophe
                name += "'"
            elif byte == 0xE9:  # Hyphen
                name += "-"
        
        return name
    
    def read_pokemon_party(self) -> List[Dict]:
        """Read Pokemon party status.
        
        Returns:
            List of dictionaries, each containing Pokemon data
        """
        party = []
        party_count = self.read_byte(MemoryAddresses.PARTY_COUNT)
        
        if party_count == 0 or party_count > 6:
            return party
        
        for i in range(party_count):
            pokemon_addr = MemoryAddresses.PARTY_POKEMON_START + (i * MemoryAddresses.POKEMON_DATA_SIZE)
            
            species = self.read_byte(pokemon_addr + MemoryAddresses.POKEMON_SPECIES)
            hp_current = self.read_word(pokemon_addr + MemoryAddresses.POKEMON_HP_CURRENT)
            hp_max = self.read_word(pokemon_addr + MemoryAddresses.POKEMON_HP_MAX)
            status = self.read_byte(pokemon_addr + MemoryAddresses.POKEMON_STATUS)
            level = self.read_byte(pokemon_addr + MemoryAddresses.POKEMON_LEVEL)
            
            pokemon_data = {
                "slot": i + 1,
                "species": species,
                "hp_current": hp_current,
                "hp_max": hp_max,
                "hp_percent": (hp_current / hp_max * 100) if hp_max > 0 else 0,
                "status": status,
                "level": level,
                "fainted": hp_current == 0,
            }
            
            party.append(pokemon_data)
        
        return party
    
    def read_health_hp(self) -> Dict[str, any]:
        """Read health/HP values for party Pokemon.
        
        Returns:
            Dictionary with party HP information
        """
        party = self.read_pokemon_party()
        
        total_hp = sum(p["hp_current"] for p in party)
        total_max_hp = sum(p["hp_max"] for p in party)
        
        return {
            "party": party,
            "total_hp": total_hp,
            "total_max_hp": total_max_hp,
            "total_hp_percent": (total_hp / total_max_hp * 100) if total_max_hp > 0 else 0,
            "party_size": len(party),
            "fainted_count": sum(1 for p in party if p["fainted"]),
        }
    
    def read_inventory(self) -> List[Dict[str, int]]:
        """Read inventory items.
        
        Returns:
            List of dictionaries with item_id and quantity
        """
        inventory = []
        item_count = self.read_byte(MemoryAddresses.INVENTORY_COUNT)
        
        if item_count == 0 or item_count > MemoryAddresses.INVENTORY_MAX:
            return inventory
        
        for i in range(item_count):
            item_addr = MemoryAddresses.INVENTORY_START + (i * 2)
            item_id = self.read_byte(item_addr)
            quantity = self.read_byte(item_addr + 1)
            
            if item_id == 0:  # Empty slot
                continue
            
            inventory.append({
                "slot": i + 1,
                "item_id": item_id,
                "quantity": quantity,
            })
        
        return inventory
    
    def detect_menu_state(self) -> Dict[str, any]:
        """Detect current menu state.
        
        Returns:
            Dictionary with menu type and state information
        """
        menu_type = self.read_byte(MemoryAddresses.MENU_TYPE)
        menu_state = self.read_byte(MemoryAddresses.MENU_STATE)
        text_box_flag = self.read_byte(MemoryAddresses.TEXT_BOX_FLAG)
        
        # Determine menu type
        menu_name = "none"
        if menu_type == 0x00:
            menu_name = "none"
        elif menu_type == 0x01:
            menu_name = "start_menu"
        elif menu_type == 0x02:
            menu_name = "pokemon_menu"
        elif menu_type == 0x03:
            menu_name = "item_menu"
        elif menu_type == 0x04:
            menu_name = "save_menu"
        else:
            menu_name = f"unknown_{menu_type}"
        
        return {
            "menu_type": menu_type,
            "menu_name": menu_name,
            "menu_state": menu_state,
            "text_box_open": text_box_flag != 0,
        }
    
    def read_battle_state(self) -> Dict[str, any]:
        """Read battle state information.
        
        Returns:
            Dictionary with battle state information
        """
        battle_type = self.read_byte(MemoryAddresses.BATTLE_TYPE)
        wild_species = self.read_byte(MemoryAddresses.WILD_POKEMON_SPECIES)
        
        in_battle = battle_type != 0
        
        battle_info = {
            "in_battle": in_battle,
            "battle_type": battle_type,
            "battle_type_name": "none" if battle_type == 0 else ("wild" if battle_type == 1 else "trainer"),
            "wild_pokemon_species": wild_species if in_battle and battle_type == 1 else 0,
        }
        
        return battle_info
    
    def read_full_game_state(self) -> Dict[str, any]:
        """Read complete game state from memory.
        
        Returns:
            Dictionary with all game state information
        """
        return {
            "player_position": self.read_player_position(),
            "current_map": self.read_current_map(),
            "player_name": self.read_player_name(),
            "party": self.read_pokemon_party(),
            "health": self.read_health_hp(),
            "inventory": self.read_inventory(),
            "menu": self.detect_menu_state(),
            "battle": self.read_battle_state(),
        }


# Map ID to name mapping (common maps in Pokemon Red)
MAP_NAMES = {
    0x00: "Pallet Town",
    0x01: "Viridian City",
    0x02: "Pewter City",
    0x03: "Cerulean City",
    0x04: "Lavender Town",
    0x05: "Vermilion City",
    0x06: "Celadon City",
    0x07: "Fuchsia City",
    0x08: "Cinnabar Island",
    0x09: "Indigo Plateau",
    0x0A: "Saffron City",
    0x0B: "Route 1",
    0x0C: "Route 2",
    0x0D: "Route 3",
    0x0E: "Route 4",
    0x0F: "Route 5",
    0x10: "Route 6",
    0x11: "Route 7",
    0x12: "Route 8",
    0x13: "Route 9",
    0x14: "Route 10",
    0x15: "Route 11",
    0x16: "Route 12",
    0x17: "Route 13",
    0x18: "Route 14",
    0x19: "Route 15",
    0x1A: "Route 16",
    0x1B: "Route 17",
    0x1C: "Route 18",
    0x1D: "Route 19",
    0x1E: "Route 20",
    0x1F: "Route 21",
    0x20: "Route 22",
    0x21: "Route 23",
    0x22: "Route 24",
    0x23: "Route 25",
}


def get_map_name(map_id: int) -> str:
    """Get map name from map ID.
    
    Args:
        map_id: Map ID number
        
    Returns:
        Map name string
    """
    return MAP_NAMES.get(map_id, f"Map {map_id:02X}")

