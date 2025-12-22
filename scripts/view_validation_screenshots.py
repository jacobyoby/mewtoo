"""View and analyze validation screenshots."""
import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np

def analyze_screenshot(image_path: str):
    """Analyze a screenshot and print information about it.
    
    Args:
        image_path: Path to screenshot image
    """
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        print(f"\n{'='*70}")
        print(f"Screenshot: {os.path.basename(image_path)}")
        print(f"{'='*70}")
        print(f"Size: {img.size[0]}x{img.size[1]} pixels")
        print(f"Mode: {img.mode}")
        print(f"Format: {img.format}")
        
        # Analyze pixel values
        if len(img_array.shape) == 3:
            print(f"Shape: {img_array.shape}")
            print(f"Color channels: {img_array.shape[2]}")
            
            # Check if it's mostly black/empty
            mean_brightness = img_array.mean()
            print(f"Mean brightness: {mean_brightness:.2f} (0=black, 255=white)")
            
            # Check for uniform color (might indicate blank screen)
            std_brightness = img_array.std()
            print(f"Brightness std dev: {std_brightness:.2f} (low = uniform, high = varied)")
            
            if mean_brightness < 10:
                print("WARNING: Image appears to be mostly black (blank screen?)")
            elif mean_brightness > 240:
                print("WARNING: Image appears to be mostly white (blank screen?)")
            elif std_brightness < 5:
                print("WARNING: Image appears to be uniform color (blank screen?)")
            else:
                print("Image appears to have content")
        
        # Try to extract text using OCR (if available)
        try:
            import pytesseract
            text = pytesseract.image_to_string(img)
            if text.strip():
                print(f"\nDetected Text (first 200 chars):")
                print(text.strip()[:200])
            else:
                print("\nNo text detected in image")
        except Exception as e:
            print(f"\nOCR not available or failed: {e}")
        
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")


def main():
    """Main entry point."""
    screenshot_dir = "validation_screenshots"
    
    if not os.path.exists(screenshot_dir):
        print(f"Error: Screenshot directory not found: {screenshot_dir}")
        return 1
    
    # Get all PNG files
    screenshot_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
    
    if not screenshot_files:
        print(f"No screenshots found in {screenshot_dir}")
        return 1
    
    # Sort by modification time (newest first)
    screenshot_files.sort(key=lambda f: os.path.getmtime(os.path.join(screenshot_dir, f)), reverse=True)
    
    print(f"Found {len(screenshot_files)} screenshots")
    print(f"Analyzing most recent {min(3, len(screenshot_files))}...")
    
    # Analyze the most recent screenshots
    for screenshot_file in screenshot_files[:3]:
        image_path = os.path.join(screenshot_dir, screenshot_file)
        analyze_screenshot(image_path)
    
    print(f"\n{'='*70}")
    print("Analysis complete")
    print(f"{'='*70}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

