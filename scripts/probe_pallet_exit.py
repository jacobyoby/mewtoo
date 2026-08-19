"""Find Pallet Town's Route 1 exit empirically, with scripted input.

Three live runs swept the north fence without ever crossing to Route 1,
so the encoded route was working from an assumed exit location. This
probe answers the question with the game itself: drive the agent to
Pallet Town, snapshot that state, then from the snapshot try walking
north from every column and record which map each attempt lands on.

Usage:
    python scripts/probe_pallet_exit.py --rom roms/pokemon_red.gb
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyboy import PyBoy  # noqa: E402

from config import setup_tesseract  # noqa: E402
from game_state import GameState  # noqa: E402
from llm_provider import OllamaProvider  # noqa: E402
from memory_reader import get_map_name  # noqa: E402
from pokemon_agent import PokemonAgent  # noqa: E402

PALLET_TOWN = 0x00


def read_state(gs: GameState) -> tuple[int | None, tuple | None]:
    info = gs.get_game_info()
    map_id = (info.get("current_map") or {}).get("map_id")
    return map_id, info.get("player_position")


def reach_pallet_town(pyboy: PyBoy, rom_path: str, max_steps: int) -> bytes | None:
    """Run the agent until it stands in Pallet Town; return a save state."""
    gs = GameState(pyboy, ocr_enabled=False)
    agent = PokemonAgent(OllamaProvider(), gs, use_cache=False)
    for step in range(max_steps):
        agent.step()
        map_id, pos = read_state(gs)
        if map_id == PALLET_TOWN:
            print(f"Reached Pallet Town at step {step}, position {pos}")
            snapshot = Path("roms/pallet_town.state")
            with open(snapshot, "wb") as f:
                pyboy.save_state(f)
            print(f"Snapshot saved: {snapshot}")
            return snapshot
    print(f"Never reached Pallet Town in {max_steps} steps")
    return None


def press(pyboy: PyBoy, button: str, times: int = 1, hold: int = 18) -> None:
    for _ in range(times):
        pyboy.button_press(button)
        for _ in range(hold):
            pyboy.tick()
        pyboy.button_release(button)
        for _ in range(4):
            pyboy.tick()


def scan_columns(rom_path: str, snapshot: Path, width: int = 12) -> None:
    """From the snapshot, walk north out of each column and log where it lands."""
    print(f"\n{'column':>7} {'landed on':<20} {'position'}")
    print("-" * 45)
    for target_x in range(width):
        pyboy = PyBoy(rom_path, window="null")
        pyboy.set_emulation_speed(0)
        with open(snapshot, "rb") as f:
            pyboy.load_state(f)
        for _ in range(10):
            pyboy.tick()

        gs = GameState(pyboy, ocr_enabled=False)
        _, pos = read_state(gs)
        if not pos:
            pyboy.stop()
            continue

        # Walk to the target column, then push north repeatedly
        dx = target_x - pos[0]
        press(pyboy, "right" if dx > 0 else "left", abs(dx))
        press(pyboy, "up", 14)

        map_id, end_pos = read_state(gs)
        name = get_map_name(map_id) if map_id is not None else "?"
        marker = "  <-- LEAVES TOWN" if map_id != PALLET_TOWN else ""
        print(f"{target_x:>7} {name:<20} {end_pos}{marker}")
        pyboy.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--max-steps", type=int, default=600)
    parser.add_argument("--snapshot", default="roms/pallet_town.state")
    args = parser.parse_args()

    setup_tesseract()
    snapshot = Path(args.snapshot)

    if not snapshot.exists():
        pyboy = PyBoy(args.rom, window="null")
        pyboy.set_emulation_speed(0)
        with open(f"{args.rom}.state", "rb") as f:
            pyboy.load_state(f)
        for _ in range(10):
            pyboy.tick()
        snapshot = reach_pallet_town(pyboy, args.rom, args.max_steps)
        pyboy.stop()
        if snapshot is None:
            sys.exit(1)
    else:
        print(f"Using existing snapshot: {snapshot}")

    scan_columns(args.rom, snapshot)


if __name__ == "__main__":
    main()
