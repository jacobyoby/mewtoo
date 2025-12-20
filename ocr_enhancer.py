"""Enhanced OCR for Game Boy screens with text region detection and character-level recognition."""
import cv2
import numpy as np
import pytesseract
from typing import List, Tuple, Optional, Dict
from enum import Enum


class TextRegion(Enum):
    """Text regions on Game Boy screen."""
    DIALOG_BOX = "dialog_box"  # Bottom dialog box
    MENU = "menu"  # Menu text
    BATTLE_TEXT = "battle_text"  # Battle interface
    OVERWORLD = "overworld"  # Overworld text
    FULL_SCREEN = "full_screen"  # Entire screen


class OCREnhancer:
    """Enhanced OCR with text region detection and Game Boy font optimization."""
    
    # Game Boy dialog box typically at bottom 40 pixels (out of 144)
    DIALOG_BOX_Y_START = 104  # 144 - 40
    DIALOG_BOX_HEIGHT = 40
    
    # Menu regions (approximate)
    MENU_REGIONS = [
        (0, 0, 160, 80),  # Top menu area
    ]
    
    def __init__(self, scale_factor: int = 4):
        """Initialize OCR enhancer.
        
        Args:
            scale_factor: Scaling factor for OCR (default: 4x)
        """
        self.scale_factor = scale_factor
        self.last_text_regions = []
    
    def detect_text_regions(self, image: np.ndarray) -> List[Dict]:
        """Detect text regions in Game Boy screen.
        
        Args:
            image: Screen image (160x144 RGB)
            
        Returns:
            List of detected text regions with coordinates
        """
        regions = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Scale up for better detection
        scaled = cv2.resize(gray, (image.shape[1] * self.scale_factor, image.shape[0] * self.scale_factor))
        
        # Apply threshold
        _, binary = cv2.threshold(scaled, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Detect dialog box (bottom region)
        h, w = binary.shape
        dialog_y_start = int(self.DIALOG_BOX_Y_START * self.scale_factor)
        dialog_region = binary[dialog_y_start:, :]
        
        # Find contours in dialog region
        contours, _ = cv2.findContours(dialog_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get bounding box of all contours
            x_coords = []
            y_coords = []
            for contour in contours:
                x, y, cw, ch = cv2.boundingRect(contour)
                x_coords.extend([x, x + cw])
                y_coords.extend([y, y + ch])
            
            if x_coords and y_coords:
                min_x = min(x_coords) // self.scale_factor
                max_x = max(x_coords) // self.scale_factor
                min_y = (min(y_coords) + dialog_y_start) // self.scale_factor
                max_y = (max(y_coords) + dialog_y_start) // self.scale_factor
                
                regions.append({
                    "type": TextRegion.DIALOG_BOX,
                    "bbox": (min_x, min_y, max_x - min_x, max_y - min_y),
                    "confidence": 0.8
                })
        
        # Detect menu regions (top area with text)
        menu_region = binary[:int(80 * self.scale_factor), :]
        menu_contours, _ = cv2.findContours(menu_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if menu_contours:
            x_coords = []
            y_coords = []
            for contour in menu_contours:
                x, y, cw, ch = cv2.boundingRect(contour)
                if cw > 10 and ch > 5:  # Filter small noise
                    x_coords.extend([x, x + cw])
                    y_coords.extend([y, y + ch])
            
            if x_coords and y_coords:
                min_x = min(x_coords) // self.scale_factor
                max_x = max(x_coords) // self.scale_factor
                min_y = min(y_coords) // self.scale_factor
                max_y = max(y_coords) // self.scale_factor
                
                regions.append({
                    "type": TextRegion.MENU,
                    "bbox": (min_x, min_y, max_x - min_x, max_y - min_y),
                    "confidence": 0.6
                })
        
        # If no regions detected, return full screen
        if not regions:
            regions.append({
                "type": TextRegion.FULL_SCREEN,
                "bbox": (0, 0, image.shape[1], image.shape[0]),
                "confidence": 0.3
            })
        
        self.last_text_regions = regions
        return regions
    
    def extract_text_from_region(self, image: np.ndarray, region: Dict, 
                                  use_character_level: bool = False) -> str:
        """Extract text from a specific region.
        
        Args:
            image: Screen image
            region: Region dictionary with bbox
            use_character_level: Use character-level OCR
            
        Returns:
            Extracted text
        """
        x, y, w, h = region["bbox"]
        
        # Extract region
        region_img = image[y:y+h, x:x+w]
        
        if region_img.size == 0:
            return ""
        
        # Scale up
        scaled = cv2.resize(region_img, (w * self.scale_factor, h * self.scale_factor), 
                          interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(scaled, cv2.COLOR_RGB2GRAY) if len(scaled.shape) == 3 else scaled
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Choose PSM mode based on region type
        if region["type"] == TextRegion.DIALOG_BOX:
            psm = "7"  # Single text line
        elif region["type"] == TextRegion.MENU:
            psm = "6"  # Uniform block
        else:
            psm = "6"  # Default
        
        # Character-level OCR if requested
        if use_character_level:
            psm = "8"  # Single word
            config = f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'
        else:
            config = f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'
        
        try:
            text = pytesseract.image_to_string(binary, config=config).strip()
            
            # Clean up common OCR errors for Game Boy font
            text = self._clean_gameboy_text(text)
            
            return text
        except Exception as e:
            return ""
    
    def _clean_gameboy_text(self, text: str) -> str:
        """Clean up common OCR errors for Game Boy font.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Common Game Boy OCR errors
        replacements = {
            '|': 'I',
            '0': 'O',  # Context-dependent, but common
            '5': 'S',
            '8': 'B',
            '1': 'I',
            'l': 'I',
            'rn': 'm',
            'vv': 'w',
        }
        
        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def extract_text_enhanced(self, image: np.ndarray, 
                              prioritize_dialog: bool = True) -> str:
        """Extract text with enhanced OCR using region detection.
        
        Args:
            image: Screen image
            prioritize_dialog: Prioritize dialog box text
            
        Returns:
            Extracted text
        """
        # Detect text regions
        regions = self.detect_text_regions(image)
        
        if not regions:
            return ""
        
        # Sort regions by confidence and type priority
        if prioritize_dialog:
            regions.sort(key=lambda r: (
                r["type"] == TextRegion.DIALOG_BOX,
                r["confidence"]
            ), reverse=True)
        
        # Extract text from each region
        texts = []
        for region in regions:
            text = self.extract_text_from_region(image, region)
            if text and len(text.strip()) > 2:
                texts.append(text)
        
        # Combine texts, prioritizing dialog
        if texts:
            # If we have dialog text, use it primarily
            dialog_texts = [t for i, t in enumerate(texts) 
                          if regions[i]["type"] == TextRegion.DIALOG_BOX]
            if dialog_texts:
                return ' '.join(dialog_texts)
            else:
                return ' '.join(texts)
        
        return ""

