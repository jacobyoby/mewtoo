"""Analyze Pokemon agent log files."""
import json
import sys
from collections import Counter
from pathlib import Path


def analyze_log(log_path: str):
    """Analyze a log file and print statistics."""
    with open(log_path, encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 70)
    print(f"Log Analysis: {Path(log_path).name}")
    print("=" * 70)
    print()
    
    # Basic info
    print("Run Information:")
    print(f"  ROM: {data.get('rom', 'Unknown')}")
    print(f"  Steps Requested: {data.get('steps', 'Unknown')}")
    print(f"  Steps Completed: {data.get('total_steps_completed', 0)}")
    print(f"  LLM Provider: {data.get('llm_provider', 'Unknown')}")
    print(f"  Model: {data.get('model', 'Default')}")
    print(f"  OCR Enabled: {data.get('ocr_enabled', 'Unknown')}")
    print(f"  OCR Interval: {data.get('ocr_interval', 'Unknown')}")
    print(f"  Start Time: {data.get('start_time', 'Unknown')}")
    print(f"  End Time: {data.get('end_time', 'Unknown')}")
    if data.get('stopped_by_user'):
        print("  Status: Stopped by user")
    if data.get('error'):
        print(f"  Error: {data.get('error')}")
    print()
    
    # Action statistics
    steps_log = data.get('steps_log', [])
    if steps_log:
        actions = [step['action'] for step in steps_log]
        action_counts = Counter(actions)
        
        print("Action Statistics:")
        for action, count in action_counts.most_common():
            percentage = (count / len(actions)) * 100
            print(f"  {action}: {count} times ({percentage:.1f}%)")
        print()
        
        # Success rate
        successes = sum(1 for step in steps_log if step.get('success', False))
        success_rate = (successes / len(steps_log)) * 100
        print(f"Success Rate: {success_rate:.1f}% ({successes}/{len(steps_log)})")
        print()
        
        # Screen text analysis
        steps_with_text = [s for s in steps_log if s.get('screen_text')]
        print(f"Steps with Screen Text: {len(steps_with_text)}/{len(steps_log)} ({len(steps_with_text)/len(steps_log)*100:.1f}%)")
        if steps_with_text:
            print("\nSample Screen Texts:")
            for step in steps_with_text[:5]:
                text = step['screen_text'][:80]
                print(f"  Step {step['step']}: {text}...")
        print()
        
        # Action sequence
        print("Action Sequence (first 20 steps):")
        for step in steps_log[:20]:
            success_marker = "OK" if step.get('success') else "FAIL"
            print(f"  Step {step['step']:3d}: {step['action']:15s} {success_marker}")
        if len(steps_log) > 20:
            print(f"  ... ({len(steps_log) - 20} more steps)")
        print()
        
        # Frame count progression
        if len(steps_log) > 1:
            frame_counts = [s['frame_count'] for s in steps_log]
            print(f"Frame Count Range: {min(frame_counts)} - {max(frame_counts)}")
            print(f"Average Frames per Step: {sum(frame_counts)/len(frame_counts):.1f}")
    
    print("=" * 70)

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_log.py <log_file.json>")
        print("\nOr analyze the most recent log:")
        print("  python analyze_log.py --latest")
        sys.exit(1)
    
    if sys.argv[1] == "--latest":
        # Look for logs directory relative to project root (parent of scripts/)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        log_dir = project_root / "logs"
        if not log_dir.exists():
            print("No logs directory found!")
            sys.exit(1)
        
        log_files = list(log_dir.glob("*.json"))
        if not log_files:
            print("No log files found!")
            sys.exit(1)
        
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"Analyzing latest log: {latest_log.name}\n")
        analyze_log(str(latest_log))
    else:
        log_path = sys.argv[1]
        if not Path(log_path).exists():
            print(f"Log file not found: {log_path}")
            sys.exit(1)
        
        analyze_log(log_path)

if __name__ == "__main__":
    main()

