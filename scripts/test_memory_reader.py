"""Test script for memory reader functionality."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyboy import PyBoy

from memory_reader import MemoryReader, get_map_name


def test_memory_reader(rom_path: str):
    """Test memory reader with Pokemon Red ROM."""
    print("=" * 60)
    print("Testing Memory Reader")
    print("=" * 60)
    
    try:
        # Initialize PyBoy
        print(f"\nLoading ROM: {rom_path}")
        pyboy = PyBoy(rom_path, window="null", sound=False)
        
        # Run a few frames to initialize game
        print("Initializing game (running 60 frames)...")
        for _ in range(60):
            pyboy.tick()
        
        # Create memory reader
        memory_reader = MemoryReader(pyboy)
        
        print("\n" + "=" * 60)
        print("Testing Memory Reading Functions")
        print("=" * 60)
        
        # Test player position
        print("\n1. Player Position:")
        try:
            x, y = memory_reader.read_player_position()
            print(f"   X: {x}, Y: {y}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test current map
        print("\n2. Current Map:")
        try:
            map_info = memory_reader.read_current_map()
            map_id = map_info.get("map_id", 0)
            map_name = get_map_name(map_id)
            print(f"   Map ID: {map_id:02X} ({map_id})")
            print(f"   Map Bank: {map_info.get('map_bank', 0)}")
            print(f"   Map Name: {map_name}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test player name
        print("\n3. Player Name:")
        try:
            name = memory_reader.read_player_name()
            print(f"   Name: '{name}'")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test party
        print("\n4. Pokemon Party:")
        try:
            party = memory_reader.read_pokemon_party()
            print(f"   Party Size: {len(party)}")
            for i, pokemon in enumerate(party):
                print(f"   Slot {pokemon['slot']}: Species {pokemon['species']}, "
                      f"Level {pokemon['level']}, "
                      f"HP {pokemon['hp_current']}/{pokemon['hp_max']} "
                      f"({pokemon['hp_percent']:.1f}%)")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test health
        print("\n5. Health/HP:")
        try:
            health = memory_reader.read_health_hp()
            print(f"   Total HP: {health['total_hp']}/{health['total_max_hp']} "
                  f"({health['total_hp_percent']:.1f}%)")
            print(f"   Fainted: {health['fainted_count']}/{health['party_size']}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test inventory
        print("\n6. Inventory:")
        try:
            inventory = memory_reader.read_inventory()
            print(f"   Items: {len(inventory)}")
            for item in inventory[:5]:  # Show first 5 items
                print(f"   Slot {item['slot']}: Item ID {item['item_id']}, "
                      f"Quantity {item['quantity']}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test menu state
        print("\n7. Menu State:")
        try:
            menu = memory_reader.detect_menu_state()
            print(f"   Menu Type: {menu['menu_type']} ({menu['menu_name']})")
            print(f"   Menu State: {menu['menu_state']}")
            print(f"   Text Box Open: {menu['text_box_open']}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test battle state
        print("\n8. Battle State:")
        try:
            battle = memory_reader.read_battle_state()
            print(f"   In Battle: {battle['in_battle']}")
            print(f"   Battle Type: {battle['battle_type']} ({battle['battle_type_name']})")
            if battle['in_battle']:
                print(f"   Wild Pokemon Species: {battle['wild_pokemon_species']}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test full game state
        print("\n9. Full Game State:")
        try:
            full_state = memory_reader.read_full_game_state()
            print(f"   Keys: {list(full_state.keys())}")
            print(f"   Player Position: {full_state.get('player_position')}")
            print(f"   Current Map: {full_state.get('current_map')}")
            print(f"   Party Size: {len(full_state.get('party', []))}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test raw memory access
        print("\n10. Raw Memory Access Test:")
        try:
            # Test reading some addresses directly
            test_addresses = [
                (0xD362, "Player X"),
                (0xD361, "Player Y"),
                (0xD35E, "Map ID"),
                (0xD163, "Party Count"),
            ]
            for addr, name in test_addresses:
                try:
                    value = memory_reader.read_byte(addr)
                    print(f"   {name} (0x{addr:04X}): {value} (0x{value:02X})")
                except Exception as e:
                    print(f"   {name} (0x{addr:04X}): Error - {e}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n" + "=" * 60)
        print("Test Complete")
        print("=" * 60)
        
        pyboy.stop()
        return True
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_memory_reader.py <rom_path>")
        print("\nExample:")
        print('  python test_memory_reader.py "Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb"')
        sys.exit(1)
    
    rom_path = sys.argv[1]
    success = test_memory_reader(rom_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

