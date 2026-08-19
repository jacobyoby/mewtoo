"""Validation script for early game sequence success rate.

Tests the agent's ability to complete:
1. Start game (title screen -> new game)
2. Get starter Pokemon
3. Reach first town (Viridian City)

Target: >80% success rate for v1.0.0
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os

from pyboy import PyBoy

from config import get_config
from game_state import GameState
from llm_provider import ClaudeProvider, OllamaProvider
from metrics import MetricsCollector
from pokemon_agent import PokemonAgent


def check_goal_completion(log_data: dict, goal_name: str) -> bool:
    """Check if a goal was completed based on log data.
    
    Args:
        log_data: Log data from agent execution
        goal_name: Name of goal to check
        
    Returns:
        True if goal was completed
    """
    # Check completed goals in log
    if 'completed_goals' in log_data:
        return goal_name in log_data['completed_goals']
    
    # Check steps for evidence of completion
    steps = log_data.get('steps', [])
    
    if goal_name == "start_game":
        # Check if we moved past title screen
        for step in steps:
            game_state = step.get('game_state', '')
            if game_state != 'title_screen' and game_state != 'loading':
                return True
        return False
    
    elif goal_name == "get_starter":
        # Check if we have a Pokemon in party
        for step in steps:
            party = step.get('party', [])
            if party and len(party) > 0:
                return True
        return False
    
    elif goal_name == "reach_viridian":
        # Check if we're in Viridian City (map ID 0x01 or 1)
        for step in steps:
            current_map = step.get('current_map', {})
            map_id = current_map.get('map_id')
            # Viridian City is map ID 0x01 (1) in Pokemon Red
            if map_id == 1 or map_id == 0x01:
                return True
        return False
    
    return False


def analyze_early_game_sequence(log_file: str) -> dict:
    """Analyze a log file for early game sequence completion.
    
    Args:
        log_file: Path to log JSON file
        
    Returns:
        Dictionary with analysis results
    """
    with open(log_file) as f:
        log_data = json.load(f)
    
    results = {
        'log_file': log_file,
        'total_steps': len(log_data.get('steps', [])),
        'goals': {
            'start_game': {
                'completed': check_goal_completion(log_data, 'start_game'),
                'step_completed': None
            },
            'get_starter': {
                'completed': check_goal_completion(log_data, 'get_starter'),
                'step_completed': None
            },
            'reach_viridian': {
                'completed': check_goal_completion(log_data, 'reach_viridian'),
                'step_completed': None
            }
        },
        'sequence_complete': False,
        'stuck_patterns': []
    }
    
    # Find step where each goal was completed
    steps = log_data.get('steps', [])
    for i, step in enumerate(steps):
        game_state = step.get('game_state', '')
        party = step.get('party', [])
        current_map = step.get('current_map', {})
        
        # Check start_game
        if not results['goals']['start_game']['step_completed']:
            if game_state != 'title_screen' and game_state != 'loading':
                results['goals']['start_game']['step_completed'] = i
        
        # Check get_starter
        if not results['goals']['get_starter']['step_completed']:
            if party and len(party) > 0:
                results['goals']['get_starter']['step_completed'] = i
        
        # Check reach_viridian
        if not results['goals']['reach_viridian']['step_completed']:
            map_id = current_map.get('map_id')
            # Viridian City is map ID 0x01 (1) in Pokemon Red
            if map_id == 1 or map_id == 0x01:
                results['goals']['reach_viridian']['step_completed'] = i
    
    # Check if full sequence completed
    results['sequence_complete'] = all(
        goal['completed'] for goal in results['goals'].values()
    )
    
    # Detect stuck patterns
    actions = [step.get('action', '') for step in steps]
    if len(actions) > 20:
        # Check for repetitive actions
        last_20 = actions[-20:]
        action_counts = {}
        for action in last_20:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in action_counts.items():
            if count > 15:  # Same action 75%+ of time
                results['stuck_patterns'].append({
                    'action': action,
                    'count': count,
                    'percentage': (count / 20) * 100
                })
    
    return results


def detect_blank_screen(screen_image: np.ndarray, white_threshold: float = 0.8, black_threshold: float = 0.8) -> dict:
    """Detect if screen is mostly blank (white or black).
    
    Args:
        screen_image: Screen image as numpy array
        white_threshold: Percentage threshold for white screen (default: 0.8 = 80%)
        black_threshold: Percentage threshold for black screen (default: 0.8 = 80%)
        
    Returns:
        Dictionary with blank screen detection results
    """
    if screen_image is None or len(screen_image.shape) < 2:
        return {'is_blank': True, 'blank_type': 'invalid', 'white_percentage': 0.0, 'black_percentage': 0.0}
    
    # Extract RGB channels (ignore alpha if present)
    if len(screen_image.shape) == 3:
        rgb = screen_image[:, :, :3] if screen_image.shape[2] >= 3 else screen_image
    else:
        rgb = screen_image
    
    total_pixels = rgb.shape[0] * rgb.shape[1]
    
    # Count white pixels (>240 in all channels)
    white_pixels = np.sum(np.all(rgb > 240, axis=2))
    white_percentage = white_pixels / total_pixels
    
    # Count black pixels (<15 in all channels)
    black_pixels = np.sum(np.all(rgb < 15, axis=2))
    black_percentage = black_pixels / total_pixels
    
    # Determine blank type
    is_blank = False
    blank_type = 'none'
    
    if white_percentage >= white_threshold:
        is_blank = True
        blank_type = 'white'
    elif black_percentage >= black_threshold:
        is_blank = True
        blank_type = 'black'
    
    return {
        'is_blank': is_blank,
        'blank_type': blank_type,
        'white_percentage': white_percentage,
        'black_percentage': black_percentage,
        'unique_colors': len(np.unique(rgb.reshape(-1, rgb.shape[-1]), axis=0)) if len(rgb.shape) == 3 else 1
    }


def capture_representative_screenshot(game_state: GameState, num_frames: int = 5) -> np.ndarray | None:
    """Capture multiple frames and select the most representative one.
    
    Args:
        game_state: GameState instance
        num_frames: Number of frames to capture (default: 5)
        
    Returns:
        Most representative screenshot as numpy array, or None if all blank
    """
    screenshots = []
    blank_detections = []
    
    for _ in range(num_frames):
        try:
            screen = game_state.get_screen_image()
            if screen is not None:
                screenshots.append(screen)
                blank_info = detect_blank_screen(screen)
                blank_detections.append(blank_info)
        except Exception:
            continue
    
    if not screenshots:
        return None
    
    # Filter out blank screens
    non_blank_screens = [(img, info) for img, info in zip(screenshots, blank_detections, strict=True) if not info['is_blank']]
    
    if non_blank_screens:
        # Return the first non-blank screen
        return non_blank_screens[0][0]
    else:
        # All screens are blank, return the one with most content (lowest white/black percentage)
        best_idx = min(range(len(blank_detections)), 
                      key=lambda i: min(blank_detections[i]['white_percentage'], 
                                       blank_detections[i]['black_percentage']))
        return screenshots[best_idx]


def validate_state_matches_screen(game_state_str: str, screen_image: np.ndarray, game_info: dict) -> dict:
    """Verify that reported game state matches screen content.
    
    Args:
        game_state_str: Reported game state string
        screen_image: Current screen image
        game_info: Game info dictionary
        
    Returns:
        Dictionary with validation results
    """
    validation = {
        'state_valid': True,
        'issues': [],
        'blank_screen': False
    }
    
    # Check for blank screen
    blank_info = detect_blank_screen(screen_image)
    if blank_info['is_blank']:
        validation['blank_screen'] = True
        validation['state_valid'] = False
        validation['issues'].append(f"Screen is mostly {blank_info['blank_type']} ({blank_info['white_percentage']:.1%} white, {blank_info['black_percentage']:.1%} black)")
    
    # Check state-specific validations
    if game_state_str == 'overworld':
        # Overworld should have varied content, not blank
        if blank_info['is_blank']:
            validation['state_valid'] = False
            validation['issues'].append("Overworld state but screen is blank")
        
        # Overworld should have a party (after starter selection)
        party = game_info.get('party', [])
        if not party or len(party) == 0:
            validation['issues'].append("Overworld state but no party detected (should have starter)")
    
    elif game_state_str == 'dialog':
        # Dialog should have text content
        screen_text = game_info.get('screen_text', '')
        if not screen_text or len(screen_text.strip()) < 5:
            if not blank_info['is_blank']:
                validation['issues'].append("Dialog state but no text detected")
    
    elif game_state_str == 'title_screen':
        # Title screen might be mostly white/black, that's OK
        pass
    
    return validation


def analyze_game_state(game_state: GameState, game_info: dict) -> dict:
    """Analyze current game state to determine progress.
    
    Args:
        game_state: GameState instance
        game_info: Current game info dictionary
        
    Returns:
        Dictionary with state analysis
    """
    analysis = {
        'game_state': game_info.get('game_state', 'unknown'),
        'has_party': False,
        'party_count': 0,
        'current_map_id': None,
        'screen_text': game_info.get('screen_text', ''),
        'is_in_starter_selection': False,
        'is_in_dialog': False,
        'progress_toward_starter': 0.0  # 0.0 to 1.0
    }
    
    # Check party
    party = game_info.get('party', [])
    if party and len(party) > 0:
        analysis['has_party'] = True
        analysis['party_count'] = len(party)
        # Check if starter Pokemon (species 1-3)
        starters = [1, 2, 3]  # Bulbasaur, Charmander, Squirtle
        if any(p.get('species', 0) in starters for p in party):
            analysis['progress_toward_starter'] = 1.0
    
    # Check map
    current_map = game_info.get('current_map', {})
    analysis['current_map_id'] = current_map.get('map_id')
    
    # Check screen text for starter selection indicators
    screen_text = analysis['screen_text'].upper()
    starter_keywords = ['BULBASAUR', 'CHARMANDER', 'SQUIRTLE', 'CHOOSE', 'POKEMON', 'POKéMON']
    if any(keyword in screen_text for keyword in starter_keywords):
        analysis['is_in_starter_selection'] = True
        if not analysis['has_party']:
            analysis['progress_toward_starter'] = 0.5  # In selection menu
    
    # Check if in dialog
    if analysis['game_state'] == 'dialog' or 'dialog' in analysis['game_state'].lower():
        analysis['is_in_dialog'] = True
        if not analysis['has_party']:
            analysis['progress_toward_starter'] = 0.3  # In dialog, progressing
    
    # Check if we're in overworld but don't have a starter yet (problematic state)
    # This shouldn't happen in normal gameplay - you must select a starter before reaching overworld
    if analysis['game_state'] == 'overworld' and not analysis['has_party']:
        # If we're in overworld without a party, we might have skipped starter selection
        # This is actually a problem - we should have a starter before reaching overworld
        analysis['progress_toward_starter'] = 0.1  # In overworld but no starter (problematic state)
        analysis['is_problematic_state'] = True  # Flag this as a problematic state
    
    return analysis


def save_screenshot_at_step(game_state: GameState, run_num: int, step: int, 
                           output_dir: str = "validation_screenshots", 
                           use_representative: bool = True) -> str | None:
    """Save a screenshot at a specific step, using representative frame if requested.
    
    Args:
        game_state: GameState instance
        run_num: Run number
        step: Current step
        output_dir: Directory to save screenshots
        use_representative: If True, capture multiple frames and use most representative
        
    Returns:
        Path to saved screenshot, or None if failed
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"run{run_num}_step{step}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Get screenshot (representative or single frame)
        if use_representative:
            screen_image = capture_representative_screenshot(game_state, num_frames=5)
        else:
            screen_image = game_state.get_screen_image()
        
        if screen_image is not None:
            # Convert to PIL Image if needed
            if isinstance(screen_image, np.ndarray):
                # Handle RGBA -> RGB conversion if needed
                if screen_image.shape[2] == 4:
                    # Convert RGBA to RGB
                    rgb_image = Image.fromarray(screen_image[:, :, :3])
                else:
                    rgb_image = Image.fromarray(screen_image)
                rgb_image.save(filepath)
            else:
                screen_image.save(filepath)
            return filepath
    except Exception as e:
        print(f"Warning: Failed to save screenshot: {e}")
    
    return None


def run_validation_test(rom_path: str, num_runs: int = 10, max_steps: int = 500,
                       llm_provider: str = 'ollama', headless: bool = True,
                       extend_runs: bool = True, max_extend_steps: int = 200) -> dict:
    """Run multiple validation tests and calculate success rate.
    
    Args:
        rom_path: Path to ROM file
        num_runs: Number of test runs
        max_steps: Maximum steps per run
        llm_provider: LLM provider to use
        headless: Run in headless mode
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'runs': [],
        'success_rate': 0.0,
        'goal_completion_rates': {
            'start_game': 0.0,
            'get_starter': 0.0,
            'reach_viridian': 0.0
        },
        'average_steps_to_complete': {
            'start_game': None,
            'get_starter': None,
            'reach_viridian': None
        },
        'stuck_patterns_found': []
    }
    
    successful_runs = 0
    goal_completions = {'start_game': 0, 'get_starter': 0, 'reach_viridian': 0}
    step_counts = {'start_game': [], 'get_starter': [], 'reach_viridian': []}
    
    print(f"Running {num_runs} validation tests...")
    print("Target: Complete early game sequence (start_game -> get_starter -> reach_viridian)")
    print("Success threshold: >80% for v1.0.0")
    print()
    
    for run_num in range(num_runs):
        print(f"Run {run_num + 1}/{num_runs}...", end=' ', flush=True)
        
        try:
            # Initialize PyBoy
            window = "null" if headless else "SDL2"
            pyboy = PyBoy(rom_path, window=window)
            pyboy.set_emulation_speed(0)  # Unlimited speed
            
            # Wait for game to load (same as main.py)
            for _ in range(60):
                pyboy.tick()
            
            # Initialize components
            metrics = MetricsCollector()
            game_state = GameState(pyboy, metrics=metrics)
            
            # Create LLM provider (pass MetricsCollector, provider will access metrics.llm internally)
            config = get_config()
            llm_config = config.get_llm_config()
            if llm_provider == 'ollama':
                default_model = llm_config.get("ollama_model", "llama3.2")
                llm = OllamaProvider(model=default_model, metrics=metrics)
            else:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                default_model = llm_config.get("claude_model", "claude-3-5-sonnet-20241022")
                llm = ClaudeProvider(api_key=api_key, model=default_model, metrics=metrics)
            
            agent = PokemonAgent(llm, game_state, metrics=metrics)
            
            # Track screenshots at key points
            key_screenshots = {
                'start': None,  # When start_game completes
                'mid': None,    # Midpoint of run
                'final': None   # Final state
            }
            
            # Run agent
            final_state_analysis = None
            final_step = max_steps
            completed_early = False
            start_game_completed_step = None
            
            for step in range(max_steps):
                agent.step()
                pyboy.tick()
                
                # Check for completion
                game_info = game_state.get_game_info()
                current_map = game_info.get('current_map', {})
                party = game_info.get('party', [])
                
                # Analyze game state
                state_analysis = analyze_game_state(game_state, game_info)
                
                # Validate state matches screen content
                screen_image = game_state.get_screen_image()
                if screen_image is not None:
                    state_validation = validate_state_matches_screen(
                        game_info.get('game_state', 'unknown'),
                        screen_image,
                        game_info
                    )
                    state_analysis['state_validation'] = state_validation
                    state_analysis['blank_screen'] = state_validation['blank_screen']
                
                # Capture screenshot when start_game completes
                if hasattr(agent, 'strategy') and agent.strategy:
                    if 'start_game' in agent.strategy.completed_goals:
                        if start_game_completed_step is None:
                            start_game_completed_step = step
                            key_screenshots['start'] = save_screenshot_at_step(
                                game_state, run_num + 1, step, use_representative=True
                            )
                
                # Capture screenshot at midpoint
                if step == max_steps // 2 and key_screenshots['mid'] is None:
                    key_screenshots['mid'] = save_screenshot_at_step(
                        game_state, run_num + 1, step, use_representative=True
                    )
                
                # Check goals (only mark once per run)
                if hasattr(agent, 'strategy') and agent.strategy:
                    # Update goal completion
                    memory_data = {
                        "player_position": game_info.get('player_position'),
                        "current_map": current_map,
                        "party": party,
                        "health": game_info.get('health', {}),
                    }
                    agent.strategy.check_goal_completion(memory_data, game_info.get('game_state', 'unknown'))
                    
                    # Track first completion of each goal
                    if 'start_game' in agent.strategy.completed_goals:
                        if len(step_counts['start_game']) == run_num:
                            goal_completions['start_game'] += 1
                            step_counts['start_game'].append(step)
                    
                    if 'get_starter' in agent.strategy.completed_goals:
                        if len(step_counts['get_starter']) == run_num:
                            goal_completions['get_starter'] += 1
                            step_counts['get_starter'].append(step)
                
                # Viridian City is map ID 0x01 (1)
                map_id = current_map.get('map_id')
                if map_id == 1 or map_id == 0x01:
                    if hasattr(agent, 'strategy') and agent.strategy:
                        if 'reach_viridian' not in agent.strategy.completed_goals:
                            agent.strategy.mark_goal_complete('reach_viridian')
                    if len(step_counts['reach_viridian']) == run_num:
                        goal_completions['reach_viridian'] += 1
                        step_counts['reach_viridian'].append(step)
                        
                        # Full sequence completed
                        successful_runs += 1
                        final_step = step
                        final_state_analysis = state_analysis
                        completed_early = True
                        print(f"SUCCESS (completed in {step} steps)")
                        break
                
                # Update final state analysis
                final_state_analysis = state_analysis
                final_step = step
            
            # If run didn't complete and we're close to starter, extend run
            if not completed_early and extend_runs and final_state_analysis:
                progress = final_state_analysis.get('progress_toward_starter', 0.0)
                is_in_starter_selection = final_state_analysis.get('is_in_starter_selection', False)
                is_in_dialog = final_state_analysis.get('is_in_dialog', False)
                
                # Extend if we're in starter selection or making progress
                if (is_in_starter_selection or (is_in_dialog and progress > 0.2)) and final_step < max_steps + max_extend_steps:
                    print(f" (extending - progress: {progress:.1%})", end='', flush=True)
                    extended_steps = 0
                    for step in range(final_step, min(final_step + max_extend_steps, max_steps + max_extend_steps)):
                        agent.step()
                        pyboy.tick()
                        extended_steps += 1
                        
                        game_info = game_state.get_game_info()
                        current_map = game_info.get('current_map', {})
                        party = game_info.get('party', [])
                        
                        # Check for starter completion
                        if party and len(party) > 0:
                            starters = [1, 2, 3]
                            if any(p.get('species', 0) in starters for p in party):
                                if hasattr(agent, 'strategy') and agent.strategy:
                                    if 'get_starter' not in agent.strategy.completed_goals:
                                        agent.strategy.mark_goal_complete('get_starter')
                                if len(step_counts['get_starter']) == run_num:
                                    goal_completions['get_starter'] += 1
                                    step_counts['get_starter'].append(step)
                                    print(f" - Got starter at step {step}!")
                        
                        # Check for Viridian
                        map_id = current_map.get('map_id')
                        if map_id == 1 or map_id == 0x01:
                            if hasattr(agent, 'strategy') and agent.strategy:
                                if 'reach_viridian' not in agent.strategy.completed_goals:
                                    agent.strategy.mark_goal_complete('reach_viridian')
                            if len(step_counts['reach_viridian']) == run_num:
                                goal_completions['reach_viridian'] += 1
                                step_counts['reach_viridian'].append(step)
                                successful_runs += 1
                                final_step = step
                                completed_early = True
                                print(f" - SUCCESS (completed in {step} steps)")
                                break
                        
                        # Update final state
                        final_state_analysis = analyze_game_state(game_state, game_info)
                        final_step = step
                        
                        # Stop extending if we're not making progress
                        if extended_steps > 50 and final_state_analysis.get('progress_toward_starter', 0.0) <= 0.3:
                            break
            
            # Save final screenshot
            screenshot_path = None
            if final_state_analysis:
                screenshot_path = save_screenshot_at_step(
                    game_state, run_num + 1, final_step, use_representative=True
                )
                if screenshot_path:
                    final_state_analysis['screenshot'] = screenshot_path
                    key_screenshots['final'] = screenshot_path
            
            # Add key screenshots to analysis
            if final_state_analysis:
                final_state_analysis['key_screenshots'] = key_screenshots
                if screenshot_path:
                    final_state_analysis['screenshot'] = screenshot_path
            
            if not completed_early:
                # Analyze why it failed
                if final_state_analysis:
                    progress = final_state_analysis.get('progress_toward_starter', 0.0)
                    state = final_state_analysis.get('game_state', 'unknown')
                    blank_screen = final_state_analysis.get('blank_screen', False)
                    state_validation = final_state_analysis.get('state_validation', {})
                    issues = state_validation.get('issues', [])
                    
                    failure_reason = []
                    if blank_screen:
                        failure_reason.append("blank screen")
                    if issues:
                        failure_reason.append(f"state issues: {', '.join(issues[:2])}")
                    if progress > 0.5:
                        failure_reason.append(f"progress: {progress:.1%}")
                    
                    reason_str = f" ({', '.join(failure_reason)})" if failure_reason else ""
                    print(f"FAILED (timeout at step {final_step}, state: {state}{reason_str})")
                else:
                    print(f"FAILED (timeout at step {final_step})")
            
            pyboy.stop()
            
        except Exception as e:
            print(f"ERROR: {e}")
        
        # Store run result with final state analysis
        run_completed = len(step_counts['reach_viridian']) > run_num
        run_result = {
            'run_number': run_num + 1,
            'completed': run_completed,
            'steps_taken': final_step if 'final_step' in locals() else max_steps,
            'final_state': final_state_analysis if 'final_state_analysis' in locals() else None
        }
        results['runs'].append(run_result)
    
    # Calculate success rate
    results['success_rate'] = (successful_runs / num_runs) * 100
    
    # Calculate goal completion rates
    for goal_name in goal_completions:
        results['goal_completion_rates'][goal_name] = (goal_completions[goal_name] / num_runs) * 100
    
    # Calculate average steps
    for goal_name in step_counts:
        if step_counts[goal_name]:
            results['average_steps_to_complete'][goal_name] = sum(step_counts[goal_name]) / len(step_counts[goal_name])
    
    return results


def print_validation_report(results: dict):
    """Print a formatted validation report.
    
    Args:
        results: Validation results dictionary
    """
    print()
    print("=" * 70)
    print("EARLY GAME SEQUENCE VALIDATION REPORT")
    print("=" * 70)
    print()
    
    print(f"Total Runs: {len(results['runs'])}")
    print(f"Successful Runs: {sum(1 for r in results['runs'] if r['completed'])}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print()
    
    if results['success_rate'] >= 80:
        print("[SUCCESS] Meets v1.0.0 requirement (>80% success rate)")
    else:
        print(f"[FAILURE] Below v1.0.0 requirement (need >80%, got {results['success_rate']:.1f}%)")
    print()
    
    print("Goal Completion Rates:")
    for goal_name, rate in results['goal_completion_rates'].items():
        print(f"  - {goal_name}: {rate:.1f}%")
    print()
    
    print("Average Steps to Complete:")
    for goal_name, avg_steps in results['average_steps_to_complete'].items():
        if avg_steps:
            print(f"  - {goal_name}: {avg_steps:.1f} steps")
        else:
            print(f"  - {goal_name}: Not completed")
    print()
    
    # Show final states for failed runs
    failed_runs = [r for r in results['runs'] if not r['completed']]
    if failed_runs:
        print("Failed Run Analysis:")
        for run in failed_runs[:5]:  # Show first 5 failed runs
            final_state = run.get('final_state', {})
            if final_state:
                progress = final_state.get('progress_toward_starter', 0.0)
                game_state = final_state.get('game_state', 'unknown')
                is_in_starter = final_state.get('is_in_starter_selection', False)
                is_in_dialog = final_state.get('is_in_dialog', False)
                screenshot = final_state.get('screenshot', '')
                
                print(f"  Run {run['run_number']}:")
                print(f"    - Final state: {game_state}")
                print(f"    - Progress toward starter: {progress:.1%}")
                print(f"    - In starter selection: {is_in_starter}")
                print(f"    - In dialog: {is_in_dialog}")
                
                # Show state validation issues
                state_validation = final_state.get('state_validation', {})
                if state_validation.get('issues'):
                    print(f"    - State validation issues: {', '.join(state_validation['issues'][:3])}")
                
                blank_screen = final_state.get('blank_screen', False)
                if blank_screen:
                    print("    - WARNING: Final screen is blank!")
                
                # Show key screenshots
                key_screenshots = final_state.get('key_screenshots', {})
                if key_screenshots:
                    print("    - Key screenshots:")
                    if key_screenshots.get('start'):
                        print(f"      * Start game: {key_screenshots['start']}")
                    if key_screenshots.get('mid'):
                        print(f"      * Midpoint: {key_screenshots['mid']}")
                    if key_screenshots.get('final'):
                        print(f"      * Final: {key_screenshots['final']}")
                elif screenshot:
                    print(f"    - Screenshot: {screenshot}")
        print()
    
    if results.get('stuck_patterns_found'):
        print("Stuck Patterns Detected:")
        for pattern in results['stuck_patterns_found']:
            print(f"  - {pattern['action']}: {pattern['count']} times ({pattern['percentage']:.1f}%)")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate early game sequence completion rate"
    )
    parser.add_argument(
        '--rom',
        type=str,
        required=True,
        help='Path to Pokemon Red ROM file'
    )
    parser.add_argument(
        '--runs',
        type=int,
        default=10,
        help='Number of test runs (default: 10)'
    )
    parser.add_argument(
        '--max-steps',
        type=int,
        default=500,
        help='Maximum steps per run (default: 500)'
    )
    parser.add_argument(
        '--llm-provider',
        type=str,
        default='ollama',
        choices=['ollama', 'claude'],
        help='LLM provider to use (default: ollama)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run in headless mode (default: True)'
    )
    parser.add_argument(
        '--display',
        action='store_true',
        help='Run with display (overrides --headless)'
    )
    parser.add_argument(
        '--no-extend',
        action='store_true',
        help='Disable extending runs when close to completing goals'
    )
    parser.add_argument(
        '--max-extend-steps',
        type=int,
        default=200,
        help='Maximum additional steps when extending runs (default: 200)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Analyze existing log file instead of running new tests'
    )
    
    args = parser.parse_args()
    
    if args.log_file:
        # Analyze existing log file
        if not os.path.exists(args.log_file):
            print(f"Error: Log file not found: {args.log_file}")
            return 1
        
        results = analyze_early_game_sequence(args.log_file)
        print_validation_report(results)
        
        # Save analysis
        output_file = f"early_game_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Analysis saved to: {output_file}")
        
    else:
        # Run new validation tests
        if not os.path.exists(args.rom):
            print(f"Error: ROM file not found: {args.rom}")
            return 1
        
        headless = args.headless and not args.display
        
        results = run_validation_test(
            args.rom,
            num_runs=args.runs,
            max_steps=args.max_steps,
            llm_provider=args.llm_provider,
            headless=headless,
            extend_runs=not args.no_extend,
            max_extend_steps=args.max_extend_steps
        )
        
        print_validation_report(results)
        
        # Save results
        output_file = f"early_game_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")
        
        # Return exit code based on success
        return 0 if results['success_rate'] >= 80 else 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

