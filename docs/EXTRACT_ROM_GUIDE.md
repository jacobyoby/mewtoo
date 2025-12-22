# How to Extract ROM from Pokemon Red Cartridge

Since you have a physical Pokemon Red cartridge, you'll need to extract the ROM file from it. Here's how:

## Option 1: Using GBxCart RW (Recommended)

**GBxCart RW** is a popular device for dumping Game Boy cartridges:

1. **Purchase GBxCart RW:**
   - Available from: https://www.gbxcart.com/
   - Or search for "GBxCart RW" on online retailers

2. **Connect and Extract:**
   - Connect the GBxCart RW to your computer via USB
   - Insert your Pokemon Red cartridge
   - Use the provided software to dump the ROM
   - Save as `pokemon_red.gb` in your project folder

## Option 2: Using Joey Joebags

**Joey Joebags** is another option:

1. Purchase from: https://bennvenn.myshopify.com/
2. Follow the same process as GBxCart RW

## Option 3: Using a Retrode 2

**Retrode 2** supports multiple cartridge types:

1. Purchase Retrode 2 adapter
2. Use with appropriate Game Boy adapter
3. Extract ROM using provided software

## Option 4: Local Game Store

Some retro game stores offer ROM dumping services for a small fee.

## After Extraction

Once you have the ROM file:

1. Place it in your project directory: `C:\Users\pikachu\pokemon\`
2. Name it something like: `pokemon_red.gb`
3. Run: `python main.py --rom pokemon_red.gb --steps 100 --display`

## Legal Note

Since you own the physical cartridge, extracting a ROM for personal use is generally considered legal under fair use in many jurisdictions, as long as you:
- Own the original cartridge
- Use the ROM only for personal backup/archival purposes
- Don't distribute the ROM file

