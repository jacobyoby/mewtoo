"""Configuration helper for Mewtwo."""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


class Config:
    """Configuration manager for Mewtwo."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config.yaml file (default: config.yaml in project root)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                self.config = {}
        else:
            # Use defaults if config file doesn't exist
            self.config = self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "agent": {
                "max_history": 5,
                "use_cache": True,
                "use_strategy": True,
                "goal_check_interval": 5,
            },
            "strategy": {
                "exploration_rate": 0.3,
                "max_recent_events": 10,
            },
            "llm": {
                "max_tokens": 10,
                "ollama_model": "llama3.2",
                "claude_model": "claude-3-5-sonnet-20241022",
            },
            "ocr": {
                "enabled": True,
                "interval": 50,
                "scale_factor": 6,  # Higher = better OCR accuracy (especially in headless mode)
            },
            "memory": {
                "check_interval": 3,
                "enabled": True,
            },
            "performance": {
                "frames_per_step": 3,
                "fast_mode": False,
                "cache_max_size": 100,
            },
            "logging": {
                "log_dir": "logs",
                "auto_log": True,
            },
            "game": {
                "default_steps": 100,
                "display": False,
                "sound": False,
                "headless": False,
            },
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., "agent.max_history")
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., "agent.max_history")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to YAML file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config.get("agent", {})
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get strategy configuration."""
        return self.config.get("strategy", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.config.get("llm", {})
    
    def get_ocr_config(self) -> Dict[str, Any]:
        """Get OCR configuration."""
        return self.config.get("ocr", {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory configuration."""
        return self.config.get("memory", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get("performance", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get("logging", {})
    
    def get_game_config(self) -> Dict[str, Any]:
        """Get game configuration."""
        return self.config.get("game", {})
    
    def get_active_profile(self) -> str:
        """Get the name of the active profile.
        
        Returns:
            Profile name (default: "balanced")
        """
        return self.config.get("active_profile", "balanced")
    
    def get_profile(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get profile configuration.
        
        Args:
            profile_name: Profile name (default: uses active_profile)
        
        Returns:
            Profile configuration dict or empty dict if not found
        """
        if profile_name is None:
            profile_name = self.get_active_profile()
        
        profiles = self.config.get("profiles", {})
        return profiles.get(profile_name, {})
    
    def list_profiles(self) -> List[str]:
        """List all available profile names.
        
        Returns:
            List of profile names
        """
        profiles = self.config.get("profiles", {})
        return list(profiles.keys())
    
    def apply_profile(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Apply profile settings, overriding defaults.
        
        Args:
            profile_name: Profile name (default: uses active_profile)
        
        Returns:
            Dictionary of applied settings
        """
        profile = self.get_profile(profile_name)
        if not profile:
            return {}
        
        applied = {}
        
        # Apply strategy settings
        if "exploration_rate" in profile:
            self.set("strategy.exploration_rate", profile["exploration_rate"])
            applied["exploration_rate"] = profile["exploration_rate"]
        
        if "goal_check_interval" in profile:
            self.set("agent.goal_check_interval", profile["goal_check_interval"])
            applied["goal_check_interval"] = profile["goal_check_interval"]
        
        # Apply LLM settings
        if "max_tokens" in profile:
            self.set("llm.max_tokens", profile["max_tokens"])
            applied["max_tokens"] = profile["max_tokens"]
        
        # Apply performance settings
        if "cache_max_size" in profile:
            self.set("performance.cache_max_size", profile["cache_max_size"])
            applied["cache_max_size"] = profile["cache_max_size"]
        
        if "frames_per_step" in profile:
            self.set("performance.frames_per_step", profile["frames_per_step"])
            applied["frames_per_step"] = profile["frames_per_step"]
        
        return applied


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def setup_tesseract():
    """Setup Tesseract OCR path if needed."""
    import pytesseract
    
    # Check if Tesseract path is set in environment
    tesseract_cmd = os.getenv("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return
    
    # Try common Windows paths
    if os.name == 'nt':
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            if Path(path).exists():
                pytesseract.pytesseract.tesseract_cmd = path
                return

