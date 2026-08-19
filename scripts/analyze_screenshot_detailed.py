"""Detailed screenshot analysis."""
import sys

import numpy as np
from PIL import Image


def analyze_screenshot_detailed(image_path: str):
    """Detailed analysis of screenshot."""
    img = Image.open(image_path)
    arr = np.array(img)
    
    print(f"\n{'='*70}")
    print(f"Detailed Analysis: {image_path}")
    print(f"{'='*70}")
    
    # Check if it's a blank/white screen
    if len(arr.shape) == 3:
        # Check for mostly white/blank screen
        white_pixels = np.sum(np.all(arr[:,:,:3] > 240, axis=2))
        total_pixels = arr.shape[0] * arr.shape[1]
        white_percentage = (white_pixels / total_pixels) * 100
        
        print(f"White pixels (>240): {white_pixels}/{total_pixels} ({white_percentage:.1f}%)")
        
        # Check for mostly black screen
        black_pixels = np.sum(np.all(arr[:,:,:3] < 15, axis=2))
        black_percentage = (black_pixels / total_pixels) * 100
        print(f"Black pixels (<15): {black_pixels}/{total_pixels} ({black_percentage:.1f}%)")
        
        # Check color distribution
        unique_colors = len(np.unique(arr[:,:,:3].reshape(-1, 3), axis=0))
        print(f"Unique colors: {unique_colors}")
        
        # Sample some pixel values
        print("\nSample pixels (top-left 5x5):")
        for i in range(min(5, arr.shape[0])):
            row = arr[i, :5, :3]  # First 5 pixels, RGB only
            print(f"  Row {i}: {row.tolist()}")
        
        # Check if it looks like a Game Boy screen (should have some structure)
        # Game Boy screens typically have distinct regions
        mid_y = arr.shape[0] // 2
        mid_x = arr.shape[1] // 2
        
        print(f"\nCenter region (around {mid_x},{mid_y}):")
        center_region = arr[mid_y-2:mid_y+3, mid_x-2:mid_x+3, :3]
        print(f"  Shape: {center_region.shape}")
        print(f"  Mean RGB: {center_region.mean(axis=(0,1))}")
        print(f"  Sample: {center_region[2,2,:]}")
        
        # Determine screen type
        if white_percentage > 80:
            print("\n>>> ANALYSIS: Screen appears to be mostly WHITE/BLANK")
            print("   This might indicate:")
            print("   - Title screen (white background)")
            print("   - Blank/loading screen")
            print("   - Screen capture issue")
        elif black_percentage > 80:
            print("\n>>> ANALYSIS: Screen appears to be mostly BLACK")
            print("   This might indicate:")
            print("   - Screen transition")
            print("   - Blank screen")
        elif unique_colors < 10:
            print("\n>>> ANALYSIS: Very few colors detected")
            print("   This might indicate:")
            print("   - Monochrome screen")
            print("   - Screen capture issue")
        else:
            print("\n>>> ANALYSIS: Screen appears to have content")
            print("   This looks like a normal game screen")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_screenshot_detailed(sys.argv[1])
    else:
        # Analyze all screenshots
        import os
        screenshots = [f for f in os.listdir('validation_screenshots') if f.endswith('.png')]
        screenshots.sort()
        for screenshot in screenshots[:3]:
            analyze_screenshot_detailed(os.path.join('validation_screenshots', screenshot))

