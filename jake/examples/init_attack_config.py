#!/usr/bin/env python3
"""
Configuration Initialization Script

This script helps you set up all the configuration parameters for the RuneScape bot
in a single JSON file. Run this once to create your config, then use it with the bot.
"""

import json
import os
import sys
import time
import pyautogui
import jake.screenshot_utils
import jake.color_utils

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_mouse_position_with_countdown(description: str, countdown: int = 5) -> tuple:
    """Get mouse position with countdown."""
    print(f"\n{description}")
    print(f"You have {countdown} seconds to position your mouse...")
    
    for i in range(countdown, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print()
    
    x, y = pyautogui.position()
    rgb_color = jake.screenshot_utils.get_pixel_color_at_position(x, y)
    hex_color = jake.color_utils.rgb_to_hex(rgb_color)
    
    print(f"Position: ({x}, {y})")
    print(f"Color: RGB{rgb_color} = #{hex_color}")
    
    return x, y, hex_color

def get_rectangle_coordinates(description: str) -> tuple:
    """Get rectangle coordinates by selecting two corners."""
    print(f"\n{description}")
    
    # Get first corner
    print("Step 1: Move mouse to first corner")
    x1, y1, _ = get_mouse_position_with_countdown("Move mouse to first corner")
    
    # Get second corner
    print("Step 2: Move mouse to opposite corner")
    x2, y2, _ = get_mouse_position_with_countdown("Move mouse to opposite corner")
    
    # Ensure coordinates are in correct order
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    
    return (x1, y1, x2, y2)

def init_config():
    """Initialize the bot configuration."""
    print("=== RuneScape Bot Configuration Setup ===")
    print("This script will help you set up all configuration parameters.")
    print("Make sure RuneScape is running and visible on your screen.\n")
    
    config = {
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
    
    # Step 1: Human-like movement configuration
    print("\n=== Step 1: Human-like Movement Configuration ===")
    human_choice = input("Enable human-like mouse movement? (y/n, default: n): ").strip().lower()
    config["human_movement"]["enabled"] = human_choice == 'y'
    
    if config["human_movement"]["enabled"]:
        print("\nSpeed range configuration:")
        print("1. Slow (0.2x to 0.5x) - Very slow, careful movements")
        print("2. Normal (0.5x to 2.0x) - Default human-like variation")
        print("3. Fast (1.5x to 3.0x) - Quick movements")
        print("4. Custom - Specify your own range")
        
        speed_choice = input("Choose speed option (1-4, default: 2): ").strip()
        if speed_choice == "1":
            config["human_movement"]["speed_range"] = [0.2, 0.5]
        elif speed_choice == "3":
            config["human_movement"]["speed_range"] = [1.5, 3.0]
        elif speed_choice == "4":
            try:
                min_speed = float(input("Enter minimum speed multiplier (e.g., 0.5): ").strip())
                max_speed = float(input("Enter maximum speed multiplier (e.g., 2.0): ").strip())
                config["human_movement"]["speed_range"] = [min_speed, max_speed]
            except ValueError:
                print("Invalid input, using default speed range")
                config["human_movement"]["speed_range"] = [0.5, 2.0]
        else:
            config["human_movement"]["speed_range"] = [0.5, 2.0]  # Default
        
        print(f"Speed range set to: {config['human_movement']['speed_range'][0]:.1f}x to {config['human_movement']['speed_range'][1]:.1f}x")
    
    # Step 2: Health bar position
    print("\n=== Step 2: Health Bar Position ===")
    print("You need to attack a mob to make their health bar appear.")
    health_choice = input("Set up health bar position now? (y/n, default: y): ").strip().lower()
    
    if health_choice != 'n':
        print("\n1. Attack a mob to make their health bar appear")
        print("2. Move your mouse to the green health bar pixel (#048834)")
        
        x, y, color = get_mouse_position_with_countdown("Move mouse to health bar pixel")
        config["health_bar"]["x"] = x
        config["health_bar"]["y"] = y
        config["health_bar"]["color"] = color
        print(f"Health bar position saved: ({x}, {y}) with color #{color}")
    else:
        print("Health bar position will need to be set up later.")
    
    # Step 3: Food area configuration
    print("\n=== Step 3: Food Area Configuration ===")
    food_choice = input("Set up food area for auto-eating? (y/n, default: y): ").strip().lower()
    
    if food_choice != 'n':
        config["food_area"]["enabled"] = True
        
        # Get food area coordinates
        food_coords = get_rectangle_coordinates("Set up food area (where your food is in inventory)")
        config["food_area"]["coordinates"] = food_coords
        print(f"Food area saved: {food_coords}")
        
        # Get red threshold
        red_threshold_str = input("Enter red threshold for health monitoring (default 5): ").strip()
        if red_threshold_str:
            config["food_area"]["red_threshold"] = int(red_threshold_str)
        else:
            config["food_area"]["red_threshold"] = 5
    else:
        print("Auto-eating will be disabled.")
    
    # Step 4: Loot pickup configuration
    print("\n=== Step 4: Loot Pickup Configuration ===")
    loot_choice = input("Configure loot pickup settings? (y/n, default: y): ").strip().lower()
    
    if loot_choice != 'n':
        # Loot color
        loot_color = input(f"Enter loot text color (hex, default: {config['loot_pickup']['loot_color']}): ").strip()
        if loot_color:
            config["loot_pickup"]["loot_color"] = loot_color
        
        # Color tolerance
        tolerance_str = input(f"Enter color tolerance (default {config['loot_pickup']['tolerance']}): ").strip()
        if tolerance_str:
            config["loot_pickup"]["tolerance"] = int(tolerance_str)
        
        # Max distance
        max_distance_str = input(f"Enter max distance from center (default {config['loot_pickup']['max_distance']}): ").strip()
        if max_distance_str:
            config["loot_pickup"]["max_distance"] = int(max_distance_str)
        
        # Debug screenshots
        debug_str = input("Save debug screenshots? (y/n, default: y): ").strip().lower()
        config["loot_pickup"]["save_debug"] = debug_str != 'n'
        
        # Inventory area for burying
        bury_choice = input("Set up inventory area for burying items? (y/n, default: n): ").strip().lower()
        if bury_choice == 'y':
            inventory_coords = get_rectangle_coordinates("Set up inventory area")
            config["loot_pickup"]["inventory_area"] = inventory_coords
            print(f"Inventory area saved: {inventory_coords}")
            
            # Enable burying
            bury_str = input("Enable burying items after pickup? (y/n, default: n): ").strip().lower()
            config["loot_pickup"]["bury"] = bury_str == 'y'
    
    # Step 5: Combat settings
    print("\n=== Step 5: Combat Settings ===")
    
    # Default target color
    target_color = input(f"Enter default target color (hex, default: {config['combat']['default_target_color']}): ").strip()
    if target_color:
        config["combat"]["default_target_color"] = target_color
    
    # Pixel selection method
    print("\nPixel selection methods:")
    print("1. Smart (blob-based with green exclusion)")
    print("2. Random (original method)")
    method_choice = input("Choose default pixel selection method (1-2, default: 1): ").strip()
    if method_choice == "2":
        config["combat"]["pixel_method"] = "random"
    
    # Random mouse movement
    random_mouse_str = input("Enable random mouse movement during combat? (y/n, default: n): ").strip().lower()
    config["combat"]["random_mouse_movement"] = random_mouse_str == 'y'
    
    # Break system
    break_str = input("Enable automatic breaks? (y/n, default: n): ").strip().lower()
    config["combat"]["enable_breaks"] = break_str == 'y'
    
    if config["combat"]["enable_breaks"]:
        print("Break settings:")
        print(f"Current: {config['combat']['break_interval_min']}-{config['combat']['break_interval_max']} min intervals, {config['combat']['break_duration_min']}-{config['combat']['break_duration_max']} min breaks")
        custom_breaks = input("Use custom break settings? (y/n, default: n): ").strip().lower()
        if custom_breaks == 'y':
            try:
                min_interval = int(input("Enter minimum break interval (minutes, default 29): ").strip() or "29")
                max_interval = int(input("Enter maximum break interval (minutes, default 33): ").strip() or "33")
                min_duration = int(input("Enter minimum break duration (minutes, default 2): ").strip() or "2")
                max_duration = int(input("Enter maximum break duration (minutes, default 6): ").strip() or "6")
                
                config["combat"]["break_interval_min"] = min_interval
                config["combat"]["break_interval_max"] = max_interval
                config["combat"]["break_duration_min"] = min_duration
                config["combat"]["break_duration_max"] = max_duration
            except ValueError:
                print("Invalid input, using default break settings")
    
    # Step 6: Save configuration
    print("\n=== Step 6: Save Configuration ===")
    
    # Show summary
    print("\nConfiguration Summary:")
    print(f"Human-like movement: {'Enabled' if config['human_movement']['enabled'] else 'Disabled'}")
    if config['human_movement']['enabled']:
        print(f"  Speed range: {config['human_movement']['speed_range'][0]:.1f}x to {config['human_movement']['speed_range'][1]:.1f}x")
    
    if config['health_bar']['x'] is not None:
        print(f"Health bar: ({config['health_bar']['x']}, {config['health_bar']['y']})")
    else:
        print("Health bar: Not configured")
    
    print(f"Auto-eating: {'Enabled' if config['food_area']['enabled'] else 'Disabled'}")
    if config['food_area']['enabled']:
        print(f"  Food area: {config['food_area']['coordinates']}")
        print(f"  Red threshold: {config['food_area']['red_threshold']}")
    
    print(f"Loot pickup: {'Enabled' if config['loot_pickup']['enabled'] else 'Disabled'}")
    if config['loot_pickup']['enabled']:
        print(f"  Loot color: #{config['loot_pickup']['loot_color']}")
        print(f"  Tolerance: {config['loot_pickup']['tolerance']}")
        print(f"  Max distance: {config['loot_pickup']['max_distance']}")
        print(f"  Bury items: {'Yes' if config['loot_pickup']['bury'] else 'No'}")
    
    print(f"Default target color: #{config['combat']['default_target_color']}")
    print(f"Pixel method: {config['combat']['pixel_method']}")
    print(f"Random mouse movement: {'Enabled' if config['combat']['random_mouse_movement'] else 'Disabled'}")
    print(f"Automatic breaks: {'Enabled' if config['combat']['enable_breaks'] else 'Disabled'}")
    
    # Save configuration
    config_file = "bot_config.json"
    save_choice = input(f"\nSave configuration to {config_file}? (y/n): ").strip().lower()
    
    if save_choice == 'y':
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuration saved to {config_file}")
            print(f"\nTo use this configuration, run:")
            print(f"python runescape_bot_example.py {config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    else:
        print("Configuration not saved.")

if __name__ == "__main__":
    init_config() 