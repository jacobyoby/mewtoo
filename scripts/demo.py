"""Demo script to show Mewtwo structure without needing a ROM."""
import sys
from pathlib import Path

# Add parent directory to path to import from project root
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

import os  # noqa: E402

from dotenv import load_dotenv  # noqa: E402


def demo_llm_providers():
    """Demonstrate LLM providers."""
    print("=" * 60)
    print("Mewtwo - Demo")
    print("=" * 60)
    print()
    
    load_dotenv()
    
    # Try Claude first if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("Claude API key found!")
        print("  You can use: --llm-provider claude")
        print()
    
    # Check Ollama
    try:
        import ollama
        client = ollama.Client()
        response = client.list()
        # Access models from ListResponse object
        model_list = response.models if hasattr(response, 'models') else []
        
        if model_list:
            print("Ollama is installed and has models!")
            # Extract model names from Model objects
            model_names = [m.model for m in model_list]
            print(f"  Available models: {', '.join(model_names)}")
            print("  You can use: --llm-provider ollama")
        else:
            print("Warning: Ollama is installed but no models found.")
            print("  Run: ollama pull llama3.2")
    except Exception as e:
        print("Warning: Ollama not available")
        print(f"  Error: {e}")
        print("  Install from: https://ollama.com")
    
    print()
    print("=" * 60)
    print("To run the full agent, you need:")
    print("  1. A Pokemon Red ROM file (.gb)")
    print("  2. Either Ollama with a model OR Claude API key")
    print("  3. Tesseract OCR installed")
    print()
    print("Example command:")
    print("  python main.py --rom pokemon_red.gb --steps 50 --display")
    print("=" * 60)

if __name__ == "__main__":
    demo_llm_providers()

