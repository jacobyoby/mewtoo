"""Script to verify a Pokemon Red ROM file."""
import sys
from pathlib import Path

def verify_rom(rom_path: str):
    """Verify if a ROM file is valid."""
    rom_file = Path(rom_path)
    
    if not rom_file.exists():
        print(f"Error: ROM file not found: {rom_path}")
        return False
    
    # Check file extension
    if rom_file.suffix.lower() not in ['.gb', '.gbc']:
        print(f"Warning: File extension is {rom_file.suffix}, expected .gb or .gbc")
    
    # Check file size (Pokemon Red should be around 1MB)
    size_mb = rom_file.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")
    
    if size_mb < 0.5 or size_mb > 2.0:
        print("Warning: File size seems unusual for Pokemon Red")
    
    # Try to read the ROM header
    try:
        with open(rom_file, 'rb') as f:
            header = f.read(0x150)  # Read ROM header
            
            # Check for Game Boy header signature
            if header[0x104:0x134] == b'\x00' * 48:
                print("Warning: ROM header looks suspicious")
            
            # Try to read title (Pokemon Red should have "POKEMON RED" or similar)
            title_bytes = header[0x134:0x144]
            title = title_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
            print(f"Detected title: {title}")
            
    except Exception as e:
        print(f"Warning: Could not read ROM header: {e}")
    
    # Try to load with PyBoy
    try:
        print("\nTesting with PyBoy...")
        from pyboy import PyBoy
        
        pyboy = PyBoy(str(rom_file), window="null", sound=False)
        print("ROM loads successfully in PyBoy!")
        
        # Run a few frames to make sure it works
        for _ in range(60):
            pyboy.tick()
        
        print("ROM appears to be working!")
        pyboy.stop()
        return True
        
    except Exception as e:
        print(f"Error loading ROM in PyBoy: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python verify_rom.py <path_to_rom.gb>")
        print("\nExample:")
        print("  python verify_rom.py pokemon_red.gb")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    print(f"Verifying ROM: {rom_path}\n")
    
    if verify_rom(rom_path):
        print("\nROM file is valid and ready to use!")
        print(f"\nRun the agent with:")
        print(f"  python main.py --rom {rom_path} --steps 100 --display")
    else:
        print("\nROM file verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

