"""Play the ROM yourself in a PyBoy window — no agent competing for input.

Useful for getting past a scripted sequence the agent cannot yet handle,
then saving that point for the agent to start from.

    python scripts/play_manual.py --rom roms/pokemon_red.gb \
        --load-state roms/pallet_town.state --save-to roms/has_starter.state

Controls: arrow keys, A = a, B = s, START = enter, SELECT = backspace.
Press Z in the window to write the save state, then close the window.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyboy import PyBoy  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--load-state", default=None)
    parser.add_argument("--save-to", default=None,
                        help="Where Z writes the state (default: <rom>.state)")
    args = parser.parse_args()

    pyboy = PyBoy(args.rom, window="SDL2")
    pyboy.set_emulation_speed(1)

    if args.load_state:
        with open(args.load_state, "rb") as f:
            pyboy.load_state(f)
        print(f"Loaded {args.load_state}")

    save_to = Path(args.save_to or f"{args.rom}.state")
    print(f"Play in the window. Press Z to save state -> {save_to}")
    print("Controls: arrows, A = a, B = s, START = enter, SELECT = backspace")

    party_addr = 0xD163
    last_party = pyboy.memory[party_addr]
    while pyboy.tick():
        party = pyboy.memory[party_addr]
        if party != last_party:
            print(f"Party size changed: {last_party} -> {party}")
            last_party = party
            if party > 0:
                with open(save_to, "wb") as f:
                    pyboy.save_state(f)
                print(f"Starter detected — auto-saved state to {save_to}")

    pyboy.stop()


if __name__ == "__main__":
    main()
