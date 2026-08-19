"""Check for stuck patterns in Pokemon agent logs."""
import json
import sys
from collections import Counter
from pathlib import Path


def analyze_stuck_patterns(log_path: str):
    """Analyze log file for stuck patterns."""
    with open(log_path, encoding='utf-8') as f:
        data = json.load(f)
    
    steps_log = data.get('steps_log', [])
    if not steps_log:
        print("No steps found in log!")
        return
    
    print("=" * 70)
    print(f"Stuck Pattern Analysis: {Path(log_path).name}")
    print("=" * 70)
    print()
    
    # Find repetitive action patterns (7+ same action in 10-step window)
    print("1. REPETITIVE ACTION PATTERNS (7+ same action in 10 steps):")
    print("-" * 70)
    stuck_windows = []
    for i in range(len(steps_log) - 9):
        window = steps_log[i:i+10]
        actions = [s['action'] for s in window]
        counts = Counter(actions)
        most_common = counts.most_common(1)[0]
        
        if most_common[1] >= 7:
            step_num = window[0]['step']
            state = window[0].get('game_state', 'unknown')
            text = window[0].get('screen_text', '')[:40]
            position = window[0].get('position', [0, 0])
            
            stuck_windows.append({
                'start_step': step_num,
                'end_step': step_num + 9,
                'action': most_common[0],
                'count': most_common[1],
                'state': state,
                'text': text,
                'position': position
            })
    
    if stuck_windows:
        for stuck in stuck_windows:
            print(f"  Steps {stuck['start_step']}-{stuck['end_step']}: "
                  f"{stuck['action']} appears {stuck['count']}/10 times")
            print(f"    State: {stuck['state']} | Position: {stuck['position']} | Text: '{stuck['text']}'")
    else:
        print("  No repetitive patterns found (7+ same action in 10 steps)")
    print()
    
    # Find same state persistence (same state for 10+ consecutive steps)
    print("2. SAME STATE PERSISTENCE (10+ consecutive steps):")
    print("-" * 70)
    same_state_runs = []
    current_state = None
    current_run_start = None
    current_run_length = 0
    
    for step in steps_log:
        state = step.get('game_state', 'unknown')
        if state == current_state:
            current_run_length += 1
        else:
            if current_run_length >= 10:
                same_state_runs.append({
                    'start_step': current_run_start,
                    'end_step': current_run_start + current_run_length - 1,
                    'length': current_run_length,
                    'state': current_state
                })
            current_state = state
            current_run_start = step['step']
            current_run_length = 1
    
    # Check last run
    if current_run_length >= 10:
        same_state_runs.append({
            'start_step': current_run_start,
            'end_step': current_run_start + current_run_length - 1,
            'length': current_run_length,
            'state': current_state
        })
    
    if same_state_runs:
        for run in same_state_runs:
            print(f"  Steps {run['start_step']}-{run['end_step']}: "
                  f"{run['state']} for {run['length']} consecutive steps")
    else:
        print("  No long same-state runs found (10+ consecutive steps)")
    print()
    
    # Find position stuck (same position for 10+ steps)
    print("3. POSITION STUCK (same position for 10+ steps):")
    print("-" * 70)
    position_runs = []
    current_pos = None
    current_pos_start = None
    current_pos_length = 0
    
    for step in steps_log:
        pos = tuple(step.get('position', [0, 0]))
        if pos == current_pos:
            current_pos_length += 1
        else:
            if current_pos_length >= 10:
                position_runs.append({
                    'start_step': current_pos_start,
                    'end_step': current_pos_start + current_pos_length - 1,
                    'length': current_pos_length,
                    'position': current_pos
                })
            current_pos = pos
            current_pos_start = step['step']
            current_pos_length = 1
    
    # Check last run
    if current_pos_length >= 10:
        position_runs.append({
            'start_step': current_pos_start,
            'end_step': current_pos_start + current_pos_length - 1,
            'length': current_pos_length,
            'position': current_pos
        })
    
    if position_runs:
        for run in position_runs:
            print(f"  Steps {run['start_step']}-{run['end_step']}: "
                  f"Position {run['position']} for {run['length']} consecutive steps")
    else:
        print("  No position stuck found (10+ steps at same position)")
    print()
    
    # Find A button spam in overworld (indicates dialogue not detected)
    print("4. A BUTTON SPAM IN OVERWORLD (likely undetected dialogue):")
    print("-" * 70)
    a_spam_windows = []
    for i in range(len(steps_log) - 9):
        window = steps_log[i:i+10]
        actions = [s['action'] for s in window]
        states = [s.get('game_state', 'unknown') for s in window]
        a_count = sum(1 for a in actions if a == 'A')
        
        # If 7+ A presses and state is overworld, likely stuck in dialogue
        if a_count >= 7 and all(s == 'overworld' for s in states):
            step_num = window[0]['step']
            text = window[0].get('screen_text', '')[:40]
            position = window[0].get('position', [0, 0])
            
            a_spam_windows.append({
                'start_step': step_num,
                'end_step': step_num + 9,
                'a_count': a_count,
                'text': text,
                'position': position
            })
    
    if a_spam_windows:
        for spam in a_spam_windows:
            print(f"  Steps {spam['start_step']}-{spam['end_step']}: "
                  f"{spam['a_count']}/10 A presses in overworld state")
            print(f"    Position: {spam['position']} | Text: '{spam['text']}'")
    else:
        print("  No A button spam in overworld found")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY:")
    print(f"  Total stuck windows (repetitive actions): {len(stuck_windows)}")
    print(f"  Total same-state runs: {len(same_state_runs)}")
    print(f"  Total position stuck runs: {len(position_runs)}")
    print(f"  Total A spam in overworld: {len(a_spam_windows)}")
    print("=" * 70)

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python check_stucks.py <log_file.json>")
        print("\nOr check the most recent log:")
        print("  python check_stucks.py --latest")
        sys.exit(1)
    
    if sys.argv[1] == "--latest":
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
        analyze_stuck_patterns(str(latest_log))
    else:
        log_path = sys.argv[1]
        if not Path(log_path).exists():
            print(f"Log file not found: {log_path}")
            sys.exit(1)
        
        analyze_stuck_patterns(log_path)

if __name__ == "__main__":
    main()

