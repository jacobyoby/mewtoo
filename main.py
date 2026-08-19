"""Main entry point for Mewtwo.

Version: 0.0.7
"""
import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pyboy import PyBoy

from config import get_config, setup_tesseract
from game_state import GameState
from llm_provider import ClaudeProvider, LLMProvider, OllamaProvider
from metrics import MetricsCollector
from planner import PlannerAgent
from pokemon_agent import PokemonAgent


def create_llm_provider(provider: str, model: str | None = None, config=None, metrics=None) -> LLMProvider:
    """Create LLM provider based on configuration.

    Args:
        provider: Provider name ('ollama' or 'claude')
        model: Optional model name
        config: Optional Config instance (uses global config if not provided)
        metrics: Optional metrics collector instance

    Returns:
        LLMProvider instance
    """
    if config is None:
        config = get_config()

    llm_config = config.get_llm_config()

    if provider.lower() == "ollama":
        default_model = model or llm_config.get("ollama_model", "gemma3:4b")
        return OllamaProvider(model=default_model, metrics=metrics)
    elif provider.lower() == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        default_model = model or llm_config.get("claude_model", "claude-sonnet-5")
        return ClaudeProvider(api_key=api_key, model=default_model, metrics=metrics)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def build_parser(config) -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Mewtwo - AI Agent for Pokemon Red")
    parser.add_argument(
        "--rom",
        type=str,
        required=True,
        help="Path to Pokemon Red ROM file (.gb)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=config.get("game.default_steps", 100),
        help=f"Number of steps to run (default: {config.get('game.default_steps', 100)})"
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default="ollama",
        choices=["ollama", "claude"],
        help="LLM provider to use (default: ollama). Can also be configured in config.yaml"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model name (default: {config.get('llm.ollama_model', 'gemma3:4b')} for Ollama, {config.get('llm.claude_model', 'claude-sonnet-5')} for Claude)"
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Enable display window"
    )
    parser.add_argument(
        "--sound",
        action="store_true",
        help="Enable sound"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no display)"
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR (much faster, but agent won't see screen text)"
    )
    parser.add_argument(
        "--ocr-interval",
        type=int,
        default=config.get("ocr.interval", 50),
        help=f"Run OCR every N frames (default: {config.get('ocr.interval', 50)}, higher = less frequent checks). Can also be configured in config.yaml"
    )
    parser.add_argument(
        "--ocr-scale",
        type=int,
        default=config.get("ocr.scale_factor", 6),
        help=f"OCR scale factor (default: {config.get('ocr.scale_factor', 6)}, higher = better OCR accuracy but slower). In headless mode, higher values (6-8) significantly improve OCR accuracy"
    )
    parser.add_argument(
        "--memory-interval",
        type=int,
        default=config.get("memory.check_interval", 3),
        help=f"Check memory every N steps (default: {config.get('memory.check_interval', 3)}, higher = less frequent checks). Can also be configured in config.yaml"
    )
    parser.add_argument(
        "--goal-interval",
        type=int,
        default=config.get("agent.goal_check_interval", 5),
        help=f"Check goal completion every N steps (default: {config.get('agent.goal_check_interval', 5)}, higher = less frequent checks). Can also be configured in config.yaml"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: disable OCR and reduce LLM calls"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="Log file path (default: logs/pokemon_agent_YYYYMMDD_HHMMSS.json)"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files (default: logs)"
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        choices=["aggressive", "conservative", "balanced"],
        help="Strategy profile to use (aggressive, conservative, balanced). Overrides config.yaml active_profile."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show debug-level diagnostics (stuck details, screenshot skips)"
    )
    parser.add_argument(
        "--planner-model",
        type=str,
        default=None,
        help=f"Model for the slow-lane strategy planner (default: {config.get('planner.model', 'qwen3:8b')}). Planner directives are injected into the fast actor's prompts."
    )
    parser.add_argument(
        "--no-planner",
        action="store_true",
        help="Disable the two-tier planner (actor model only)"
    )
    return parser


def apply_profile(config, args) -> None:
    """Apply a strategy profile from the CLI or config.yaml."""
    if args.profile:
        applied_settings = config.apply_profile(args.profile)
        if applied_settings:
            print(f"Applied profile '{args.profile}': {applied_settings}")
    elif config.get("active_profile"):
        profile_name = config.get_active_profile()
        applied_settings = config.apply_profile(profile_name)
        if applied_settings and profile_name != "balanced":
            print(f"Using profile '{profile_name}' from config.yaml")


def validate_rom(rom_arg: str) -> Path:
    """Validate the ROM path and readability; exit with guidance on failure."""
    rom_path = Path(rom_arg)

    # Check for placeholder or invalid paths
    if rom_arg == "..." or rom_arg.strip() == "":
        print("Error: Invalid ROM path provided.")
        print("Please provide the actual path to your ROM file.")
        print("Example: python main.py --rom \"Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb\" --model llama3.2:1b --llm-provider ollama")
        sys.exit(1)

    if not rom_path.exists():
        print(f"Error: ROM file not found: {rom_arg}")
        print(f"Current directory: {Path.cwd()}")
        print(f"Looking for: {rom_path.absolute()}")
        # Help the user spot a near-miss in the current directory
        gb_files = list(Path.cwd().glob("*.gb"))
        if gb_files:
            print("\nFound .gb files in current directory:")
            for gb_file in gb_files:
                print(f"  - {gb_file.name}")
        sys.exit(1)

    if not rom_path.is_file():
        print(f"Error: ROM path is not a file: {rom_arg}")
        sys.exit(1)

    try:
        # Test file permissions
        with open(rom_path, 'rb') as f:
            f.read(1)
    except PermissionError as e:
        print(f"Error: Permission denied accessing ROM file: {rom_arg}")
        print(f"Details: {e}")
        print("\nPossible solutions:")
        print("1. Check file permissions")
        print("2. Make sure the file is not open in another program")
        print("3. Run as administrator if needed")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot read ROM file: {rom_arg}")
        print(f"Details: {e}")
        sys.exit(1)

    return rom_path


def init_pyboy(rom_path: Path, args) -> PyBoy:
    """Initialize PyBoy with the ROM and wait for the game to load."""
    print(f"Loading ROM: {rom_path}")
    window = "null" if args.headless else "SDL2" if args.display else "null"
    pyboy_kwargs = {
        "window": window,
        "debug": False,
        "sound_emulated": args.sound,
        "sound": args.sound,
    }

    try:
        pyboy = PyBoy(str(rom_path), **pyboy_kwargs)
    except PermissionError as e:
        print(f"Error: Permission denied when initializing PyBoy with ROM: {rom_path}")
        print(f"Details: {e}")
        print("\nPossible causes:")
        print("1. The ROM file is locked by another process")
        print("2. PyBoy is trying to create/access a save state file (.gb.ram) that is locked")
        print("3. Insufficient file permissions")
        print("\nTry:")
        print("1. Close any other programs that might be using the ROM file")
        print("2. Delete the .gb.ram file if it exists and is causing issues")
        print("3. Run as administrator if needed")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to initialize PyBoy with ROM: {rom_path}")
        print(f"Details: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Wait for game to load
    for _ in range(60):
        pyboy.tick()

    print("Game loaded!")
    return pyboy


def build_agent(pyboy: PyBoy, args, config, metrics: MetricsCollector) -> tuple[PokemonAgent, int]:
    """Build the LLM provider, game state, and agent.

    Returns:
        (agent, frames_per_step) tuple
    """
    print(f"Initializing LLM provider: {args.llm_provider}")
    try:
        llm_provider = create_llm_provider(args.llm_provider, args.model, config, metrics=metrics)
    except Exception as e:
        print(f"Error initializing LLM provider: {e}")
        pyboy.stop()
        sys.exit(1)

    # Configure OCR settings (command line args override config file)
    ocr_enabled = not (args.no_ocr or args.fast) and config.get("ocr.enabled", True)
    ocr_interval = 100 if args.fast else max(args.ocr_interval, 10)
    memory_interval = 10 if args.fast else max(args.memory_interval, 1)
    goal_interval = 10 if args.fast else max(args.goal_interval, 1)

    perf_config = config.get_performance_config()
    frames_per_step = 1 if args.fast else perf_config.get("frames_per_step", 3)

    game_state = GameState(pyboy, ocr_enabled=ocr_enabled, ocr_interval=ocr_interval,
                           memory_check_interval=memory_interval, ocr_scale_factor=args.ocr_scale,
                           metrics=metrics)

    # Two-tier brain: a slower planner model whose directives are injected
    # into the fast actor's prompts. Ollama-only for now (local, free).
    planner = None
    planner_enabled = config.get("planner.enabled", True) and not args.no_planner
    if planner_enabled:
        planner_model = args.planner_model or config.get("planner.model", "qwen3:8b")
        try:
            planner_provider = OllamaProvider(
                model=planner_model, metrics=metrics,
                think=config.get("planner.think", False),
                timeout=config.get("planner.timeout", 60),
            )
            planner = PlannerAgent(
                planner_provider,
                interval=config.get("planner.interval", 25),
                min_gap=config.get("planner.min_gap", 10),
                max_tokens=config.get("planner.max_tokens", 700),
                metrics=metrics,
            )
            print(f"Planner enabled: {planner_provider.model} every ~{planner.interval} steps")
        except Exception as e:
            print(f"Warning: planner disabled ({e})")

    agent_config = config.get_agent_config()
    agent = PokemonAgent(
        llm_provider,
        game_state,
        use_cache=agent_config.get("use_cache", True),
        use_strategy=agent_config.get("use_strategy", True),
        goal_check_interval=goal_interval,
        metrics=metrics,
        planner=planner
    )
    return agent, frames_per_step


def make_log_path(args) -> Path:
    """Resolve the JSON run-log path."""
    if args.log:
        return Path(args.log)
    log_dir = Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"pokemon_agent_{timestamp}.json"


def build_step_log(step: int, result: dict) -> dict:
    """Assemble the JSON log record for one step."""
    game_info = result['game_info']
    step_log = {
        "step": step + 1,
        "action": result['action'],
        "success": result['success'],
        "frame_count": game_info['frame_count'],
        "screen_text": game_info['screen_text'],
        "game_state": game_info.get('game_state'),
        "timestamp": datetime.now().isoformat()
    }
    if result.get('progress'):
        step_log["progress"] = result['progress']
    if game_info.get('current_map'):
        step_log["location"] = game_info['current_map'].get('map_name')
    if game_info.get('player_position'):
        step_log["position"] = game_info['player_position']
    if game_info.get('party'):
        step_log["party_size"] = len(game_info['party'])
        step_log["first_pokemon_level"] = game_info['party'][0].get('level')
    return step_log


def print_step_report(step: int, total_steps: int, result: dict) -> None:
    """Print the per-step console report."""
    game_info = result['game_info']
    print(f"Step {step + 1}/{total_steps}")
    print(f"  Action: {result['action']}")
    print(f"  Success: {result['success']}")
    if game_info.get('game_state'):
        print(f"  Game State: {game_info['game_state']}")

    if result.get('progress'):
        progress = result['progress']
        print(f"  Progress: {progress['completed_goals']}/{progress['total_goals']} goals "
              f"({progress['progress_percent']:.1f}%)")
        if progress['completed_goal_names']:
            recent_completed = progress['completed_goal_names'][-3:]
            print(f"  Recent Goals: {', '.join(recent_completed)}")

    if game_info.get('current_map'):
        map_name = game_info['current_map'].get('map_name')
        if map_name and map_name != 'Unknown':
            print(f"  Location: {map_name}")
    pos = game_info.get('player_position')
    if pos and pos != (0, 0):
        print(f"  Position: ({pos[0]}, {pos[1]})")
    party = game_info.get('party')
    if party:
        print(f"  Party: {len(party)} Pokemon")
        if party[0].get('level'):
            print(f"  First Pokemon: Level {party[0]['level']}, "
                  f"HP {party[0].get('hp_current', 0)}/{party[0].get('hp_max', 0)}")

    if result.get('state_changed') is False:
        print("  Warning: State unchanged - action may not have had effect")
    if result.get('stuck_count', 0) > 3:
        print(f"  Warning: Stuck for {result['stuck_count']} steps")
    if game_info.get('screen_text'):
        text_preview = game_info['screen_text'][:80].replace('\n', ' ')
        print(f"  Screen Text: {text_preview}...")
    print()


def sync_cache_metrics(agent: PokemonAgent, metrics: MetricsCollector) -> None:
    """Copy action-cache counters into the metrics collector."""
    if agent.action_cache:
        cache_stats = agent.action_cache.get_stats()
        metrics.cache.hits = cache_stats['hits']
        metrics.cache.misses = cache_stats['misses']
        metrics.cache.evictions = cache_stats.get('evictions', 0)
        metrics.cache.update_size(cache_stats['size'], cache_stats.get('max_size', 100))


def run_loop(agent: PokemonAgent, pyboy: PyBoy, args, metrics: MetricsCollector,
             log_data: dict, log_path: Path, frames_per_step: int) -> None:
    """Run the agent loop, logging and reporting each step."""
    for step in range(args.steps):
        result = agent.step()

        log_data["steps_log"].append(build_step_log(step, result))
        sync_cache_metrics(agent, metrics)

        # Save log after each step (in case of crash)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print_step_report(step, args.steps, result)

        # Let game run for multiple frames to smooth out gameplay
        for _ in range(frames_per_step):
            pyboy.tick()


def print_final_progress(agent: PokemonAgent) -> None:
    """Print the end-of-run goal progress summary."""
    progress = agent.strategy.get_progress_summary()
    print("\n" + "=" * 60)
    print("Final Progress Summary")
    print("=" * 60)
    print(f"Completed Goals: {progress['completed_goals']}/{progress['total_goals']} "
          f"({progress['progress_percent']:.1f}%)")
    print(f"Current Phase: {progress['current_phase']}")
    print(f"Total Steps: {progress['step_count']}")
    if progress['completed_goal_names']:
        print(f"Completed: {', '.join(progress['completed_goal_names'])}")
    print("=" * 60)


def main():
    """Main function."""
    load_dotenv()
    config = get_config()
    setup_tesseract()

    args = build_parser(config).parse_args()

    # Library modules (agent, game state, providers) log diagnostics through
    # the logging module; per-step gameplay output stays on stdout via print.
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    apply_profile(config, args)
    rom_path = validate_rom(args.rom)
    pyboy = init_pyboy(rom_path, args)

    metrics = MetricsCollector()
    agent, frames_per_step = build_agent(pyboy, args, config, metrics)

    log_path = make_log_path(args)
    ocr_enabled = not (args.no_ocr or args.fast) and config.get("ocr.enabled", True)
    log_data = {
        "rom": str(rom_path),
        "steps": args.steps,
        "llm_provider": args.llm_provider,
        "model": args.model,
        "profile": args.profile or config.get_active_profile(),
        "ocr_enabled": ocr_enabled,
        "ocr_interval": 100 if args.fast else max(args.ocr_interval, 10),
        "start_time": datetime.now().isoformat(),
        "steps_log": []
    }

    print(f"Starting agent for {args.steps} steps...")
    print(f"Logging to: {log_path}")
    print("Press Ctrl+C to stop early\n")

    try:
        run_loop(agent, pyboy, args, metrics, log_data, log_path, frames_per_step)
    except KeyboardInterrupt:
        print("\nStopped by user")
        log_data["end_time"] = datetime.now().isoformat()
        log_data["stopped_by_user"] = True
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        log_data["end_time"] = datetime.now().isoformat()
        log_data["error"] = str(e)
        log_data["traceback"] = traceback.format_exc()
    finally:
        log_data["end_time"] = log_data.get("end_time", datetime.now().isoformat())
        log_data["total_steps_completed"] = len(log_data["steps_log"])

        if agent.strategy:
            log_data["final_progress"] = agent.strategy.get_progress_summary()
            print_final_progress(agent)

        sync_cache_metrics(agent, metrics)
        log_data["metrics"] = metrics.get_all_stats()
        print("\n" + metrics.get_summary())

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"\nLog saved to: {log_path}")
        print("Shutting down...")
        pyboy.stop()


if __name__ == "__main__":
    main()
