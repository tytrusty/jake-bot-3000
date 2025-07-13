#!/usr/bin/env python3
"""
Simple RuneScape Bot Example

This is a simple example demonstrating how to use the RuneScape bot
with the new configuration system.
"""

import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runescape_bot import RuneScapeBot
from config_manager import ConfigurationManager

def main():
    """Simple example using configuration file."""
    print("=== Simple RuneScape Bot Example ===")
    
    # Load configuration
    config_manager = ConfigurationManager("bot_config.json")
    if not config_manager.load_config():
        print("Configuration file not found. Please run 'python init_config.py' first.")
        return
    
    # Display configuration
    config_manager.print_config_summary()
    
    # Initialize bot
    use_human_paths = config_manager.is_human_movement_enabled()
    bot = RuneScapeBot(config_manager=config_manager, use_human_paths=use_human_paths)
    
    # Find RuneScape window
    window_region = bot.find_runescape_window()
    if not window_region:
        print("Could not find RuneScape window. Make sure the game is running.")
        return
    
    bot.window_region = window_region
    print(f"Found RuneScape window at: {window_region}")
    
    # Get settings from config
    combat_config = config_manager.get_combat_config()
    target_color = combat_config.get('default_target_color', '00FFFFFA')
    pixel_method = combat_config.get('pixel_method', 'smart')
    
    food_area = None
    if config_manager.is_food_area_enabled():
        food_area = config_manager.get_food_area_coordinates()
    
    food_config = config_manager.get_food_area_config()
    red_threshold = food_config.get('red_threshold', 5)
    
    random_mouse_movement = config_manager.is_random_mouse_movement_enabled()
    enable_breaks = config_manager.is_breaks_enabled()
    
    print(f"\nStarting attack sequence with:")
    print(f"  Target color: #{target_color}")
    print(f"  Pixel method: {pixel_method}")
    print(f"  Auto-eating: {'Enabled' if food_area else 'Disabled'}")
    print(f"  Random mouse movement: {'Enabled' if random_mouse_movement else 'Disabled'}")
    print(f"  Automatic breaks: {'Enabled' if enable_breaks else 'Disabled'}")
    
    # Run a few attack sequences
    for i in range(3):
        print(f"\n--- Attack Sequence {i+1}/3 ---")
        success = bot.attack_sequence(
            target_color,
            food_area=food_area,
            red_threshold=red_threshold,
            pixel_method=pixel_method,
            random_mouse_movement=random_mouse_movement,
            enable_breaks=enable_breaks
        )
        
        if success:
            print("Attack sequence completed successfully!")
        else:
            print("Attack sequence failed or no targets found.")
        
        # Wait between sequences
        if i < 2:  # Don't wait after the last sequence
            print("Waiting 5 seconds before next sequence...")
            time.sleep(5)
    
    print("\nSimple example completed!")

if __name__ == "__main__":
    main() 