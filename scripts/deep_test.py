"""Script for testing agent deeper into the game with extended runs."""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import main as main_func
import sys as sys_module


def main():
    """Run extended test with more steps and better progress tracking."""
    parser = argparse.ArgumentParser(description="Deep test - extended agent run")
    parser.add_argument(
        "--rom",
        type=str,
        required=True,
        help="Path to Pokemon Red ROM file (.gb)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=500,
        help="Number of steps to run (default: 500 for deep testing)"
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default="ollama",
        choices=["ollama", "claude"],
        help="LLM provider to use (default: ollama)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name"
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Enable display window"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: disable OCR and reduce LLM calls"
    )
    
    args = parser.parse_args()
    
    # Build sys.argv for main function
    sys_module.argv = [
        "main.py",
        "--rom", args.rom,
        "--steps", str(args.steps),
        "--llm-provider", args.llm_provider,
    ]
    
    if args.model:
        sys_module.argv.extend(["--model", args.model])
    if args.display:
        sys_module.argv.append("--display")
    if args.headless:
        sys_module.argv.append("--headless")
    if args.fast:
        sys_module.argv.append("--fast")
    
    print("=" * 60)
    print("Deep Test Mode - Extended Agent Run")
    print("=" * 60)
    print(f"Steps: {args.steps}")
    print(f"Provider: {args.llm_provider}")
    print("=" * 60)
    print()
    
    # Run main function
    main_func()


if __name__ == "__main__":
    main()

