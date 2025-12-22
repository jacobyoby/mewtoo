"""Visual demonstration of Mewtwo without needing a ROM."""
import time
import random
from typing import Dict, List

class MockGameState:
    """Mock game state for demonstration."""
    
    BUTTONS = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "START", "SELECT"]
    
    def __init__(self):
        self.frame_count = 0
        self.scenarios = [
            "You are in Pallet Town. Professor Oak's lab is to the north.",
            "A wild Pidgey appeared!",
            "You found a Potion!",
            "You are walking through tall grass.",
            "You entered a Pokemon Center.",
            "You are talking to an NPC.",
            "Your Pokemon is low on HP!",
            "You won the battle!",
        ]
        self.current_scenario = 0
    
    def get_game_info(self) -> Dict:
        """Get mock game information."""
        self.frame_count += 1
        scenario = self.scenarios[self.current_scenario % len(self.scenarios)]
        self.current_scenario += random.randint(1, 3)
        
        return {
            "screen_text": scenario,
            "frame_count": self.frame_count,
        }
    
    def execute_action(self, action: str) -> bool:
        """Simulate action execution."""
        return action.upper() in self.BUTTONS or action.upper().startswith("WAIT")


class MockLLMProvider:
    """Mock LLM provider that simulates AI decision making."""
    
    def __init__(self):
        self.responses = [
            "A",  # Confirm/interact
            "UP",  # Move up
            "RIGHT, A",  # Move right and interact
            "B",  # Cancel
            "START",  # Open menu
            "WAIT 5",  # Wait
            "DOWN",  # Move down
            "LEFT, A",  # Move left and interact
        ]
        self.index = 0
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a mock response."""
        # Extract context from prompt
        if "wild" in prompt.lower() or "battle" in prompt.lower():
            return "A"  # Attack/confirm
        elif "found" in prompt.lower() or "item" in prompt.lower():
            return "A"  # Pick up item
        elif "low on HP" in prompt.lower():
            return "START"  # Open menu to use item
        elif "Pokemon Center" in prompt:
            return "A"  # Interact
        elif "talking" in prompt.lower():
            return "A"  # Continue dialogue
        
        # Cycle through responses
        response = self.responses[self.index % len(self.responses)]
        self.index += 1
        return response


def print_banner():
    """Print a nice banner."""
    print("\n" + "=" * 70)
    print(" " * 20 + "Mewtwo - Visual Demo")
    print("=" * 70 + "\n")


def print_game_screen(text: str, frame: int):
    """Print a formatted game screen."""
    print("┌" + "─" * 68 + "┐")
    print("│" + " " * 20 + "GAME BOY SCREEN" + " " * 33 + "│")
    print("├" + "─" * 68 + "┤")
    lines = text.split('\n')
    for line in lines[:4]:  # Show max 4 lines
        padded = line[:66].ljust(66)
        print(f"│ {padded} │")
    for _ in range(4 - len(lines)):
        print("│ " + " " * 66 + " │")
    print("├" + "─" * 68 + "┤")
    print(f"│ Frame: {frame:<62} │")
    print("└" + "─" * 68 + "┘")


def main():
    """Run the visual demo."""
    print_banner()
    
    print("This demo simulates how Mewtwo works!")
    print("In the real version, it would:")
    print("  • Load a Pokemon Red ROM using PyBoy emulator")
    print("  • Extract game state using OCR (Tesseract)")
    print("  • Use an LLM (Ollama or Claude) to decide actions")
    print("  • Execute actions by pressing Game Boy buttons\n")
    
    input("Press Enter to start the demo...")
    
    # Initialize mock components
    game_state = MockGameState()
    llm_provider = MockLLMProvider()
    
    print("\n" + "=" * 70)
    print("Starting Pokemon Red gameplay simulation...")
    print("=" * 70 + "\n")
    
    # Simulate gameplay
    for step in range(10):
        print(f"\n{'─' * 70}")
        print(f"Step {step + 1}/10")
        print(f"{'─' * 70}\n")
        
        # Get game state
        game_info = game_state.get_game_info()
        print_game_screen(game_info['screen_text'], game_info['frame_count'])
        
        # Simulate LLM thinking
        print("\nAI Agent thinking...")
        time.sleep(0.8)
        
        # Get action from LLM
        prompt = f"Current state: {game_info['screen_text']}"
        action = llm_provider.generate(prompt)
        
        print(f"AI Decision: '{action}'")
        time.sleep(0.5)
        
        # Execute action
        success = game_state.execute_action(action)
        print(f"Action executed: {success}")
        
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print("\nTo run the real version, you need:")
    print("  1. A Pokemon Red ROM file (.gb)")
    print("  2. Install Ollama: https://ollama.com")
    print("     Then run: ollama pull llama3.2")
    print("  3. Install Tesseract OCR")
    print("  4. Run: python main.py --rom pokemon_red.gb --steps 100 --display")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


