"""Game state extraction and management for Pokemon Red."""
import cv2
import numpy as np
from PIL import Image
import pytesseract
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pyboy import PyBoy
from memory_reader import MemoryReader, get_map_name
from ocr_enhancer import OCREnhancer


class GameState:
    """Extracts and manages game state from PyBoy."""
    
    # Game Boy button mappings (PyBoy 2.0 uses lowercase string names)
    BUTTONS = {
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "A": "a",
        "B": "b",
        "SELECT": "select",
        "START": "start",
    }
    
    def __init__(self, pyboy: PyBoy, ocr_enabled: bool = True, ocr_interval: int = 50, 
                 memory_enabled: bool = True, use_enhanced_ocr: bool = True,
                 memory_check_interval: int = 1, ocr_scale_factor: int = 6):
        """Initialize GameState with PyBoy instance.
        
        Args:
            pyboy: PyBoy emulator instance
            ocr_enabled: Whether to enable OCR (can be slow)
            ocr_interval: Only run OCR every N frames (default: 50, higher = less frequent)
            memory_enabled: Whether to enable memory reading (default: True)
            use_enhanced_ocr: Whether to use enhanced OCR with region detection (default: True)
            memory_check_interval: Check memory every N steps (default: 1, higher = less frequent)
            ocr_scale_factor: Scaling factor for OCR (default: 6, higher = better OCR but slower)
                             In headless mode, higher values help OCR accuracy significantly
        """
        self.pyboy = pyboy
        self.screen_width = 160
        self.screen_height = 144
        self.ocr_enabled = ocr_enabled
        self.ocr_interval = max(ocr_interval, 10)  # Minimum interval for performance
        self.memory_enabled = memory_enabled
        self.memory_check_interval = max(memory_check_interval, 1)
        self.use_enhanced_ocr = use_enhanced_ocr
        self.ocr_scale_factor = ocr_scale_factor  # Store scale factor
        self.frame_count = 0
        self.last_ocr_text = ""
        self.last_ocr_frame = 0
        self.last_memory_check_step = 0
        self.cached_memory_state = None
        
        # Initialize OCR enhancer with scale factor
        if self.use_enhanced_ocr:
            self.ocr_enhancer = OCREnhancer(scale_factor=self.ocr_scale_factor)
        else:
            self.ocr_enhancer = None
        
        # Initialize memory reader
        if self.memory_enabled:
            try:
                self.memory_reader = MemoryReader(pyboy)
            except Exception as e:
                print(f"Warning: Could not initialize memory reader: {e}")
                print("Falling back to OCR-only mode")
                self.memory_enabled = False
                self.memory_reader = None
        else:
            self.memory_reader = None
    
    def get_screen_image(self) -> np.ndarray:
        """Get current screen as numpy array."""
        screen = self.pyboy.screen.image
        return np.array(screen)
    
    def save_screenshot(self, filename: Optional[str] = None, directory: str = "logs/screenshots") -> str:
        """Save a screenshot of the current screen.
        
        Args:
            filename: Optional filename (will generate timestamp-based name if not provided)
            directory: Directory to save screenshot (default: logs/screenshots)
            
        Returns:
            Path to saved screenshot file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            filename = f"screenshot_{timestamp}.png"
        
        # Get screen image
        screen_image = self.get_screen_image()
        
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(screen_image)
        
        # Save screenshot
        filepath = os.path.join(directory, filename)
        pil_image.save(filepath)
        
        return filepath
    
    def detect_dialog_box_visually(self, image: Optional[np.ndarray] = None) -> bool:
        """Detect if a dialogue box is present visually (even if OCR fails).
        
        Args:
            image: Screen image (optional, will get current if not provided)
            
        Returns:
            True if dialogue box is detected visually
        """
        try:
            if image is None:
                image = self.get_screen_image()
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            
            h, w = gray.shape
            
            # Check bottom 40 pixels (typical dialogue box height)
            dialog_region = gray[int(h * 0.72):, :]  # Bottom ~28% of screen
            
            # Dialogue boxes are typically darker (lower values) with high contrast
            # Check for a rectangular dark region at the bottom
            mean_bottom = np.mean(dialog_region)
            mean_top = np.mean(gray[:int(h * 0.5), :])  # Top half
            
            # If bottom region is darker than top, likely a dialogue box
            # Lowered threshold to be more sensitive (was 0.85, now 0.90)
            if mean_bottom < mean_top * 0.90:  # Bottom is at least 10% darker
                # Also check for rectangular structure (dialogue boxes have borders)
                # Look for horizontal lines (top and bottom borders)
                horizontal_edges = cv2.Sobel(dialog_region, cv2.CV_64F, 0, 1, ksize=3)
                horizontal_edge_strength = np.mean(np.abs(horizontal_edges))
                
                # Dialogue boxes typically have strong horizontal edges
                # Lowered threshold to be more sensitive (was 10, now 5)
                if horizontal_edge_strength > 5:
                    return True
                
                # Even without strong edges, if bottom is much darker, likely dialogue
                if mean_bottom < mean_top * 0.75:  # Bottom is 25%+ darker
                    return True
            
            return False
        except Exception as e:
            # If visual detection fails, return False (fallback to other methods)
            return False
    
    def get_screen_text(self) -> str:
        """Extract text from the current screen using OCR with improved preprocessing."""
        if not self.ocr_enabled:
            return ""
        
        # Only run OCR periodically to improve performance
        if self.pyboy.frame_count - self.last_ocr_frame < self.ocr_interval:
            return self.last_ocr_text
        
        screen_image = self.get_screen_image()
        
        # Use enhanced OCR if available
        if self.use_enhanced_ocr and self.ocr_enhancer:
            try:
                text = self.ocr_enhancer.extract_text_enhanced(screen_image, prioritize_dialog=True)
                self.last_ocr_text = text
                self.last_ocr_frame = self.pyboy.frame_count
                return text
            except Exception as e:
                print(f"Enhanced OCR error: {e}, falling back to standard OCR")
        
        # Fallback to standard OCR
        # Improved preprocessing for Game Boy screens
        # 1. Scale up for better OCR (Game Boy is 160x144, very small)
        # Higher scale factor = better OCR accuracy, especially in headless mode
        # Use Lanczos interpolation for better quality (slower but more accurate)
        target_width = self.screen_width * self.ocr_scale_factor
        target_height = self.screen_height * self.ocr_scale_factor
        scaled = cv2.resize(screen_image, (target_width, target_height), 
                          interpolation=cv2.INTER_LANCZOS4)
        
        # 2. Convert to grayscale
        gray = cv2.cvtColor(scaled, cv2.COLOR_RGB2GRAY)
        
        # 3. Apply adaptive thresholding (better than fixed threshold)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 4. Focus on text regions (bottom 40% for dialog, full screen for menus)
        # Try bottom region first (where dialog usually is)
        h, w = binary.shape
        dialog_region = binary[int(h * 0.6):, :]
        full_region = binary
        
        # Extract text with multiple PSM modes for better results
        try:
            # Try dialog region first (PSM 7 = single text line)
            text_dialog = pytesseract.image_to_string(
                dialog_region, 
                config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'
            ).strip()
            
            # Try full screen (PSM 6 = uniform block of text)
            text_full = pytesseract.image_to_string(
                full_region,
                config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'
            ).strip()
            
            # Use dialog text if it's longer and more meaningful
            if len(text_dialog) > 3 and len(text_dialog) > len(text_full) * 0.7:
                text = text_dialog
            else:
                text = text_full
            
            # Clean up common OCR errors
            text = text.replace('|', 'I').replace('0', 'O').replace('5', 'S')
            text = ' '.join(text.split())  # Normalize whitespace
            
            self.last_ocr_text = text
            self.last_ocr_frame = self.pyboy.frame_count
            return self.last_ocr_text
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def get_game_info(self) -> Dict:
        """Extract game information from memory and OCR.
        
        Combines memory-based reading (accurate) with OCR (fallback).
        Checks memory less frequently based on memory_check_interval.
        """
        screen_text = self.get_screen_text()
        
        # Read game state from memory (less frequently)
        memory_state = None
        if self.memory_enabled and self.memory_reader:
            # Check if we should read memory this step
            current_step = getattr(self, '_step_count', 0)
            should_check_memory = (
                current_step % self.memory_check_interval == 0 or
                self.cached_memory_state is None
            )
            
            if should_check_memory:
                try:
                    memory_state = self.memory_reader.read_full_game_state()
                    self.cached_memory_state = memory_state
                    self.last_memory_check_step = current_step
                except Exception as e:
                    # Silently fall back to OCR if memory reading fails
                    memory_state = None
            else:
                # Use cached memory state
                memory_state = self.cached_memory_state
        
        if memory_state:
            
            # Determine game state from memory
            game_state = "unknown"
            menu_info = memory_state.get("menu", {})
            battle_info = memory_state.get("battle", {})
            
            if battle_info.get("in_battle"):
                game_state = "battle"
            elif menu_info.get("menu_name") != "none":
                game_state = menu_info.get("menu_name", "menu")
            elif menu_info.get("text_box_open"):
                game_state = "dialog"
            else:
                # Check if we're in overworld (has valid position)
                player_pos = memory_state.get("player_position", (0, 0))
                if player_pos[0] > 0 or player_pos[1] > 0:
                    game_state = "overworld"
                else:
                    # Fallback to OCR-based detection
                    if not screen_text or "PyBoy" in screen_text:
                        game_state = "loading"
                    elif any(word in screen_text.upper() for word in ["NINTENDO", "GAME FREAK", "PRESENTS"]):
                        game_state = "title_screen"
                    elif any(word in screen_text.upper() for word in ["MENU", "OPTIONS", "SAVE"]):
                        game_state = "menu"
                    elif len(screen_text) > 10:
                        game_state = "dialog"
                    elif len(screen_text) > 0:
                        game_state = "overworld"
                    
                    # Use visual detection as fallback for dialogue boxes
                    # This helps when OCR text is garbled or too short (like "reese")
                    if game_state == "overworld" or (game_state == "unknown" and len(screen_text) > 0):
                        if self.detect_dialog_box_visually():
                            game_state = "dialog"
            
            # ALWAYS check for visual dialogue boxes if we have screen text
            # Memory reading might miss text boxes, so visual detection is important
            if game_state == "overworld" and len(screen_text) > 0:
                if self.detect_dialog_box_visually():
                    game_state = "dialog"
            
            # Get map name
            map_info = memory_state.get("current_map", {})
            map_id = map_info.get("map_id", 0)
            map_name = get_map_name(map_id)
            
            return {
                "screen_text": screen_text,
                "frame_count": self.pyboy.frame_count,
                "game_state": game_state,
                "has_text": len(screen_text) > 0,
                # Memory-based data
                "player_position": memory_state.get("player_position"),
                "current_map": {
                    **map_info,
                    "map_name": map_name,
                },
                "player_name": memory_state.get("player_name"),
                "party": memory_state.get("party"),
                "health": memory_state.get("health"),
                "inventory": memory_state.get("inventory"),
                "menu": menu_info,
                "battle": battle_info,
            }
        else:
            # Fallback to OCR-only if memory reading is disabled or failed
            # Detect game state from screen text patterns
            game_state = "unknown"
            if not screen_text or "PyBoy" in screen_text:
                game_state = "loading"
            elif any(word in screen_text.upper() for word in ["NINTENDO", "GAME FREAK", "PRESENTS"]):
                game_state = "title_screen"
            elif any(word in screen_text.upper() for word in ["MENU", "OPTIONS", "SAVE"]):
                game_state = "menu"
            elif any(word in screen_text.upper() for word in ["WILD", "ATTACK", "FIGHT", "RUN"]):
                game_state = "battle"
            elif len(screen_text) > 3:  # Lowered threshold - even short garbled text might be dialogue
                # Check visual detection first for dialogue boxes
                if self.detect_dialog_box_visually():
                    game_state = "dialog"
                else:
                    # If no visual box but text exists, could be overworld text or dialogue
                    # Prefer dialogue if text is longer
                    if len(screen_text) > 10:
                        game_state = "dialog"
                    else:
                        game_state = "overworld"
            elif len(screen_text) > 0:
                game_state = "overworld"
            
            # Use visual detection as fallback for dialogue boxes
            # This helps when OCR text is garbled or too short
            if game_state == "unknown" or game_state == "overworld":
                if self.detect_dialog_box_visually():
                    game_state = "dialog"
            
            return {
                "screen_text": screen_text,
                "frame_count": self.pyboy.frame_count,
                "game_state": game_state,
                "has_text": len(screen_text) > 0,
                "memory_enabled": self.memory_enabled,
            }
    
    def press_button(self, button: str, hold_frames: int = 1):
        """Press a button.
        
        Args:
            button: Button name (UP, DOWN, LEFT, RIGHT, A, B, SELECT, START)
            hold_frames: Number of frames to hold the button
        """
        if button not in self.BUTTONS:
            raise ValueError(f"Unknown button: {button}")
        
        button_id = self.BUTTONS[button]
        self.pyboy.button_press(button_id)
        
        # Hold for specified frames
        for _ in range(hold_frames):
            self.pyboy.tick()
        
        self.pyboy.button_release(button_id)
        self.pyboy.tick()
    
    def execute_action(self, action: str) -> bool:
        """Execute an action string.
        
        Args:
            action: Action string (e.g., "UP", "A", "START")
        
        Returns:
            True if action was executed successfully
        """
        action = action.strip().upper()
        
        # Handle multi-step actions
        if "," in action:
            actions = [a.strip() for a in action.split(",")]
            for a in actions:
                if a in self.BUTTONS:
                    self.press_button(a)
            return True
        
        # Handle single action
        if action in self.BUTTONS:
            self.press_button(action)
            return True
        
        # Handle special commands
        if action.startswith("WAIT"):
            try:
                frames = int(action.split()[1]) if len(action.split()) > 1 else 10
                for _ in range(frames):
                    self.pyboy.tick()
                return True
            except:
                return False
        
        return False
    
    # Convenience methods for accessing memory data
    
    def get_player_position(self) -> Tuple[int, int]:
        """Get player position (X, Y coordinates).
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if not self.memory_enabled or not self.memory_reader:
            return (0, 0)
        try:
            return self.memory_reader.read_player_position()
        except Exception:
            return (0, 0)
    
    def get_current_map(self) -> Dict[str, any]:
        """Get current map information.
        
        Returns:
            Dictionary with map_id, map_bank, and map_name
        """
        if not self.memory_enabled or not self.memory_reader:
            return {"map_id": 0, "map_bank": 0, "map_name": "Unknown"}
        try:
            map_info = self.memory_reader.read_current_map()
            map_id = map_info.get("map_id", 0)
            map_info["map_name"] = get_map_name(map_id)
            return map_info
        except Exception:
            return {"map_id": 0, "map_bank": 0, "map_name": "Unknown"}
    
    def get_pokemon_party(self) -> List[Dict]:
        """Get Pokemon party status.
        
        Returns:
            List of dictionaries with Pokemon data
        """
        if not self.memory_enabled or not self.memory_reader:
            return []
        try:
            return self.memory_reader.read_pokemon_party()
        except Exception:
            return []
    
    def get_health_hp(self) -> Dict[str, any]:
        """Get health/HP values for party Pokemon.
        
        Returns:
            Dictionary with party HP information
        """
        if not self.memory_enabled or not self.memory_reader:
            return {
                "party": [],
                "total_hp": 0,
                "total_max_hp": 0,
                "total_hp_percent": 0,
                "party_size": 0,
                "fainted_count": 0,
            }
        try:
            return self.memory_reader.read_health_hp()
        except Exception:
            return {
                "party": [],
                "total_hp": 0,
                "total_max_hp": 0,
                "total_hp_percent": 0,
                "party_size": 0,
                "fainted_count": 0,
            }
    
    def get_inventory(self) -> List[Dict[str, int]]:
        """Get inventory items.
        
        Returns:
            List of dictionaries with item_id and quantity
        """
        if not self.memory_enabled or not self.memory_reader:
            return []
        try:
            return self.memory_reader.read_inventory()
        except Exception:
            return []
    
    def get_menu_state(self) -> Dict[str, any]:
        """Get current menu state.
        
        Returns:
            Dictionary with menu type and state information
        """
        if not self.memory_enabled or not self.memory_reader:
            return {
                "menu_type": 0,
                "menu_name": "none",
                "menu_state": 0,
                "text_box_open": False,
            }
        try:
            return self.memory_reader.detect_menu_state()
        except Exception:
            return {
                "menu_type": 0,
                "menu_name": "none",
                "menu_state": 0,
                "text_box_open": False,
            }
    
    def get_battle_state(self) -> Dict[str, any]:
        """Get battle state information.
        
        Returns:
            Dictionary with battle state information
        """
        if not self.memory_enabled or not self.memory_reader:
            return {
                "in_battle": False,
                "battle_type": 0,
                "battle_type_name": "none",
                "wild_pokemon_species": 0,
            }
        try:
            return self.memory_reader.read_battle_state()
        except Exception:
            return {
                "in_battle": False,
                "battle_type": 0,
                "battle_type_name": "none",
                "wild_pokemon_species": 0,
            }

