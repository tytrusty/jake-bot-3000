#!/usr/bin/env python3
"""
Configuration Manager

This module provides a ConfigurationManager class for loading and managing
bot configuration from JSON files.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple

class ConfigurationManager:
    """Manages bot configuration from JSON files."""
    
    def __init__(self, config_file: str = "bot_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "version": "1.0",
            "description": "RuneScape Bot Configuration",
            
            # Human-like movement settings
            "human_movement": {
                "enabled": False,
                "speed_range": [0.5, 2.0],
                "use_random_selection": True,
                "k_nearest": 8,
                "use_iterative_movement": True,
                "max_iterations": 5,
                "tolerance": 10.0
            },
            
            # Health monitoring
            "health_bar": {
                "x": None,
                "y": None,
                "color": None
            },
            
            # Food area for auto-eating
            "food_area": {
                "enabled": False,
                "coordinates": None,
                "red_threshold": 5
            },
            
            # Loot pickup settings
            "loot_pickup": {
                "enabled": True,
                "loot_color": "AA00FFFF",
                "tolerance": 20,
                "max_distance": 500,
                "save_debug": True,
                "inventory_area": None,
                "bury": False
            },
            
            # Combat settings
            "combat": {
                "default_target_color": "00FFFFFA",
                "pixel_method": "smart",
                "random_mouse_movement": False,
                "enable_breaks": False,
                "break_interval_min": 29,
                "break_interval_max": 33,
                "break_duration_min": 2,
                "break_duration_max": 6
            },
            
            # Debug settings
            "debug": {
                "save_screenshots": True,
                "screenshot_dir": "debug_screenshots"
            }
        }
    
    def load_config(self) -> bool:
        """
        Load configuration from JSON file.
        
        Returns:
            True if config loaded successfully, False otherwise
        """
        if not os.path.exists(self.config_file):
            print(f"Configuration file {self.config_file} not found.")
            print("Run 'python init_config.py' to create a configuration file.")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
            
            # Merge loaded config with defaults (preserve defaults for missing keys)
            self._merge_config(loaded_config)
            print(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def _merge_config(self, loaded_config: Dict[str, Any]):
        """Merge loaded configuration with defaults."""
        for key, value in loaded_config.items():
            if key in self.config:
                if isinstance(value, dict) and isinstance(self.config[key], dict):
                    # Recursively merge nested dictionaries
                    self._merge_nested_dict(self.config[key], value)
                else:
                    # Replace non-dict values
                    self.config[key] = value
            else:
                # Add new keys
                self.config[key] = value
    
    def _merge_nested_dict(self, default_dict: Dict[str, Any], loaded_dict: Dict[str, Any]):
        """Recursively merge nested dictionaries."""
        for key, value in loaded_dict.items():
            if key in default_dict and isinstance(value, dict) and isinstance(default_dict[key], dict):
                self._merge_nested_dict(default_dict[key], value)
            else:
                default_dict[key] = value
    
    def save_config(self) -> bool:
        """
        Save current configuration to JSON file.
        
        Returns:
            True if config saved successfully, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_human_movement_config(self) -> Dict[str, Any]:
        """Get human movement configuration."""
        return self.config.get("human_movement", {})
    
    def get_health_bar_config(self) -> Dict[str, Any]:
        """Get health bar configuration."""
        return self.config.get("health_bar", {})
    
    def get_food_area_config(self) -> Dict[str, Any]:
        """Get food area configuration."""
        return self.config.get("food_area", {})
    
    def get_loot_pickup_config(self) -> Dict[str, Any]:
        """Get loot pickup configuration."""
        return self.config.get("loot_pickup", {})
    
    def get_combat_config(self) -> Dict[str, Any]:
        """Get combat configuration."""
        return self.config.get("combat", {})
    
    def get_debug_config(self) -> Dict[str, Any]:
        """Get debug configuration."""
        return self.config.get("debug", {})
    
    def get_health_bar_position(self) -> Optional[Tuple[int, int]]:
        """Get health bar position as tuple."""
        health_config = self.get_health_bar_config()
        x = health_config.get("x")
        y = health_config.get("y")
        if x is not None and y is not None:
            return (x, y)
        return None
    
    def get_food_area_coordinates(self) -> Optional[Tuple[int, int, int, int]]:
        """Get food area coordinates as tuple."""
        food_config = self.get_food_area_config()
        coords = food_config.get("coordinates")
        if coords and len(coords) == 4:
            return tuple(coords)
        return None
    
    def get_inventory_area_coordinates(self) -> Optional[Tuple[int, int, int, int]]:
        """Get inventory area coordinates as tuple."""
        loot_config = self.get_loot_pickup_config()
        coords = loot_config.get("inventory_area")
        if coords and len(coords) == 4:
            return tuple(coords)
        return None
    
    def get_speed_range(self) -> Tuple[float, float]:
        """Get speed range as tuple."""
        human_config = self.get_human_movement_config()
        speed_range = human_config.get("speed_range", [0.5, 2.0])
        return tuple(speed_range)
    
    def is_human_movement_enabled(self) -> bool:
        """Check if human-like movement is enabled."""
        return self.get_human_movement_config().get("enabled", False)
    
    def is_food_area_enabled(self) -> bool:
        """Check if food area is enabled."""
        return self.get_food_area_config().get("enabled", False)
    
    def is_loot_pickup_enabled(self) -> bool:
        """Check if loot pickup is enabled."""
        return self.get_loot_pickup_config().get("enabled", True)
    
    def is_random_mouse_movement_enabled(self) -> bool:
        """Check if random mouse movement is enabled."""
        return self.get_combat_config().get("random_mouse_movement", False)
    
    def is_breaks_enabled(self) -> bool:
        """Check if automatic breaks are enabled."""
        return self.get_combat_config().get("enable_breaks", False)
    
    def print_config_summary(self):
        """Print a summary of the current configuration."""
        print("\n=== Configuration Summary ===")
        
        # Human movement
        human_config = self.get_human_movement_config()
        print(f"Human-like movement: {'Enabled' if human_config.get('enabled') else 'Disabled'}")
        if human_config.get('enabled'):
            speed_range = self.get_speed_range()
            print(f"  Speed range: {speed_range[0]:.1f}x to {speed_range[1]:.1f}x")
        
        # Health bar
        health_config = self.get_health_bar_config()
        if health_config.get('x') is not None:
            print(f"Health bar: ({health_config['x']}, {health_config['y']})")
        else:
            print("Health bar: Not configured")
        
        # Food area
        food_config = self.get_food_area_config()
        print(f"Auto-eating: {'Enabled' if food_config.get('enabled') else 'Disabled'}")
        if food_config.get('enabled'):
            coords = self.get_food_area_coordinates()
            if coords:
                print(f"  Food area: {coords}")
            print(f"  Red threshold: {food_config.get('red_threshold', 5)}")
        
        # Loot pickup
        loot_config = self.get_loot_pickup_config()
        print(f"Loot pickup: {'Enabled' if loot_config.get('enabled') else 'Disabled'}")
        if loot_config.get('enabled'):
            print(f"  Loot color: #{loot_config.get('loot_color', 'AA00FFFF')}")
            print(f"  Tolerance: {loot_config.get('tolerance', 20)}")
            print(f"  Max distance: {loot_config.get('max_distance', 500)}")
            print(f"  Bury items: {'Yes' if loot_config.get('bury') else 'No'}")
        
        # Combat
        combat_config = self.get_combat_config()
        print(f"Default target color: #{combat_config.get('default_target_color', '00FFFFFA')}")
        print(f"Pixel method: {combat_config.get('pixel_method', 'smart')}")
        print(f"Random mouse movement: {'Enabled' if combat_config.get('random_mouse_movement') else 'Disabled'}")
        print(f"Automatic breaks: {'Enabled' if combat_config.get('enable_breaks') else 'Disabled'}")
        
        if combat_config.get('enable_breaks'):
            print(f"  Break intervals: {combat_config.get('break_interval_min', 29)}-{combat_config.get('break_interval_max', 33)} minutes")
            print(f"  Break duration: {combat_config.get('break_duration_min', 2)}-{combat_config.get('break_duration_max', 6)} minutes")
        
        print() 