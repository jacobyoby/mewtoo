"""Main entry point for Mewtwo.

Version: 0.0.5.1
"""
import argparse
import os
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from pyboy import PyBoy
from llm_provider import OllamaProvider, ClaudeProvider, LLMProvider
from game_state import GameState
from pokemon_agent import PokemonAgent
from config import setup_tesseract, get_config


def create_llm_provider(provider: str, model: Optional[str] = None, config=None) -> LLMProvider:
    """Create LLM provider based on configuration.
    
    Args:
        provider: Provider name ('ollama' or 'claude')
        model: Optional model name
        config: Optional Config instance (uses global config if not provided)
    
    Returns:
        LLMProvider instance
    """
    if config is None:
        config = get_config()
    
    llm_config = config.get_llm_config()
    
    if provider.lower() == "ollama":
        default_model = model or llm_config.get("ollama_model", "llama3.2")
        return OllamaProvider(model=default_model)
    elif provider.lower() == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        default_model = model or llm_config.get("claude_model", "claude-3-5-sonnet-20241022")
        return ClaudeProvider(api_key=api_key, model=default_model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def main():
    """Main function."""
    load_dotenv()
    
    # Load configuration
    config = get_config()
    
    # Apply profile if specified via command line (will be applied after args parsing)
    # For now, just load config
    
    # Setup Tesseract OCR
    setup_tesseract()
    
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
        help=f"Model name (default: {config.get('llm.ollama_model', 'llama3.2')} for Ollama, {config.get('llm.claude_model', 'claude-3-5-sonnet-20241022')} for Claude)"
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
    
    args = parser.parse_args()
    
    # Apply profile if specified
    if args.profile:
        applied_settings = config.apply_profile(args.profile)
        if applied_settings:
            print(f"Applied profile '{args.profile}': {applied_settings}")
    elif config.get("active_profile"):
        # Apply default profile from config
        profile_name = config.get_active_profile()
        applied_settings = config.apply_profile(profile_name)
        if applied_settings and profile_name != "balanced":
            print(f"Using profile '{profile_name}' from config.yaml")
    
    # Validate ROM file
    rom_path = Path(args.rom)
    
    # Check for placeholder or invalid paths
    if args.rom == "..." or args.rom.strip() == "":
        print("Error: Invalid ROM path provided.")
        print("Please provide the actual path to your ROM file.")
        print(f"Example: python main.py --rom \"Pokemon - Red Version (USA, Europe) (SGB Enhanced).gb\" --model llama3.2:1b --llm-provider ollama")
        sys.exit(1)
    
    if not rom_path.exists():
        print(f"Error: ROM file not found: {args.rom}")
        print(f"Current directory: {Path.cwd()}")
        print(f"Looking for: {rom_path.absolute()}")
        # Check if file exists in current directory with different case
        current_dir = Path.cwd()
        if current_dir.exists():
            gb_files = list(current_dir.glob("*.gb"))
            if gb_files:
                print(f"\nFound .gb files in current directory:")
                for gb_file in gb_files:
                    print(f"  - {gb_file.name}")
        sys.exit(1)
    
    # Check if ROM file is readable
    if not rom_path.is_file():
        print(f"Error: ROM path is not a file: {args.rom}")
        sys.exit(1)
    
    try:
        # Test file permissions
        with open(rom_path, 'rb') as f:
            f.read(1)
    except PermissionError as e:
        print(f"Error: Permission denied accessing ROM file: {args.rom}")
        print(f"Details: {e}")
        print("\nPossible solutions:")
        print("1. Check file permissions")
        print("2. Make sure the file is not open in another program")
        print("3. Run as administrator if needed")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot read ROM file: {args.rom}")
        print(f"Details: {e}")
        sys.exit(1)
    
    # Initialize PyBoy
    print(f"Loading ROM: {args.rom}")
    window = "null" if args.headless else "SDL2" if args.display else "null"
    pyboy_kwargs = {
        "window": window,
        "debug": False,
        "sound_emulated": False,  # Disable sound by default
        "sound": False  # Also disable sound output
    }
    if args.sound:
        pyboy_kwargs["sound_emulated"] = True
        pyboy_kwargs["sound"] = True
    
    try:
        pyboy = PyBoy(str(rom_path), **pyboy_kwargs)
    except PermissionError as e:
        print(f"Error: Permission denied when initializing PyBoy with ROM: {args.rom}")
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
        print(f"Error: Failed to initialize PyBoy with ROM: {args.rom}")
        print(f"Details: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Wait for game to load
    for _ in range(60):
        pyboy.tick()
    
    print("Game loaded!")
    
    # Initialize components
    print(f"Initializing LLM provider: {args.llm_provider}")
    try:
        llm_provider = create_llm_provider(args.llm_provider, args.model, config)
    except Exception as e:
        print(f"Error initializing LLM provider: {e}")
        pyboy.stop()
        sys.exit(1)
    
    # Configure OCR settings (command line args override config file)
    ocr_enabled = not (args.no_ocr or args.fast) and config.get("ocr.enabled", True)
    ocr_interval = 100 if args.fast else max(args.ocr_interval, 10)
    memory_interval = 10 if args.fast else max(args.memory_interval, 1)
    goal_interval = 10 if args.fast else max(args.goal_interval, 1)
    
    # Get performance config
    perf_config = config.get_performance_config()
    frames_per_step = 1 if args.fast else perf_config.get("frames_per_step", 3)
    
    ocr_scale_factor = args.ocr_scale if hasattr(args, 'ocr_scale') else config.get("ocr.scale_factor", 6)
    game_state = GameState(pyboy, ocr_enabled=ocr_enabled, ocr_interval=ocr_interval,
                          memory_check_interval=memory_interval, ocr_scale_factor=ocr_scale_factor)
    
    # Get agent config
    agent_config = config.get_agent_config()
    agent = PokemonAgent(
        llm_provider, 
        game_state, 
        use_cache=agent_config.get("use_cache", True),
        use_strategy=agent_config.get("use_strategy", True),
        goal_check_interval=goal_interval
    )
    
    # Setup logging
    if args.log:
        log_path = Path(args.log)
    else:
        log_dir = Path(args.log_dir)
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"pokemon_agent_{timestamp}.json"
    
    # Get active profile name
    active_profile = args.profile or config.get_active_profile()
    
    log_data = {
        "rom": str(rom_path),
        "steps": args.steps,
        "llm_provider": args.llm_provider,
        "model": args.model,
        "profile": active_profile,
        "ocr_enabled": ocr_enabled,
        "ocr_interval": ocr_interval,
        "start_time": datetime.now().isoformat(),
        "steps_log": []
    }
    
    print(f"Starting agent for {args.steps} steps...")
    print(f"Logging to: {log_path}")
    print("Press Ctrl+C to stop early\n")
    
    try:
        for step in range(args.steps):
            result = agent.step()
            
            # Log this step
            step_log = {
                "step": step + 1,
                "action": result['action'],
                "success": result['success'],
                "frame_count": result['game_info']['frame_count'],
                "screen_text": result['game_info']['screen_text'],
                "game_state": result['game_info'].get('game_state'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add progress info if available
            if result.get('progress'):
                step_log["progress"] = result['progress']
            
            # Add memory-based info if available
            if result['game_info'].get('current_map'):
                step_log["location"] = result['game_info']['current_map'].get('map_name')
            if result['game_info'].get('player_position'):
                step_log["position"] = result['game_info']['player_position']
            if result['game_info'].get('party'):
                step_log["party_size"] = len(result['game_info']['party'])
                if result['game_info']['party']:
                    step_log["first_pokemon_level"] = result['game_info']['party'][0].get('level')
            
            log_data["steps_log"].append(step_log)
            
            # Save log after each step (in case of crash)
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"Step {step + 1}/{args.steps}")
            print(f"  Action: {result['action']}")
            print(f"  Success: {result['success']}")
            game_info = result['game_info']
            if game_info.get('game_state'):
                print(f"  Game State: {game_info['game_state']}")
            
            # Show progress if available
            if result.get('progress'):
                progress = result['progress']
                print(f"  Progress: {progress['completed_goals']}/{progress['total_goals']} goals "
                      f"({progress['progress_percent']:.1f}%)")
                if progress['completed_goal_names']:
                    recent_completed = progress['completed_goal_names'][-3:]
                    print(f"  Recent Goals: {', '.join(recent_completed)}")
            
            # Show memory-based info if available
            if game_info.get('current_map'):
                map_info = game_info['current_map']
                if map_info.get('map_name') and map_info.get('map_name') != 'Unknown':
                    print(f"  Location: {map_info['map_name']}")
            if game_info.get('player_position'):
                pos = game_info['player_position']
                if pos and pos != (0, 0):
                    print(f"  Position: ({pos[0]}, {pos[1]})")
            if game_info.get('party'):
                party = game_info['party']
                if party:
                    print(f"  Party: {len(party)} Pokemon")
                    if party[0].get('level'):
                        print(f"  First Pokemon: Level {party[0]['level']}, "
                              f"HP {party[0].get('hp_current', 0)}/{party[0].get('hp_max', 0)}")
            
            if result.get('state_changed') is False:
                print(f"  Warning: State unchanged - action may not have had effect")
            if result.get('stuck_count', 0) > 3:
                print(f"  Warning: Stuck for {result['stuck_count']} steps")
            if game_info.get('screen_text'):
                text_preview = game_info['screen_text'][:80].replace('\n', ' ')
                print(f"  Screen Text: {text_preview}...")
            print()
            
            # Let game run for multiple frames to smooth out gameplay
            for _ in range(frames_per_step):
                pyboy.tick()
    
    except KeyboardInterrupt:
        print("\nStopped by user")
        log_data["end_time"] = datetime.now().isoformat()
        log_data["stopped_by_user"] = True
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        log_data["end_time"] = datetime.now().isoformat()
        log_data["error"] = str(e)
        log_data["traceback"] = traceback.format_exc()
    finally:
        # Finalize log
        log_data["end_time"] = log_data.get("end_time", datetime.now().isoformat())
        log_data["total_steps_completed"] = len(log_data["steps_log"])
        
        # Add final progress summary
        if hasattr(agent, 'strategy') and agent.strategy:
            log_data["final_progress"] = agent.strategy.get_progress_summary()
            print("\n" + "=" * 60)
            print("Final Progress Summary")
            print("=" * 60)
            progress = agent.strategy.get_progress_summary()
            print(f"Completed Goals: {progress['completed_goals']}/{progress['total_goals']} "
                  f"({progress['progress_percent']:.1f}%)")
            print(f"Current Phase: {progress['current_phase']}")
            print(f"Total Steps: {progress['step_count']}")
            if progress['completed_goal_names']:
                print(f"Completed: {', '.join(progress['completed_goal_names'])}")
            print("=" * 60)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nLog saved to: {log_path}")
        print("Shutting down...")
        pyboy.stop()


if __name__ == "__main__":
    main()

