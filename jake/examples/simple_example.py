#!/usr/bin/env python3
"""
Simple RuneScape Bot Example

This is a simple example demonstrating basic usage of the RuneScape bot framework.
"""

import sys
import os
import time

# Add the parent directory to the Python path to import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runescape_bot import RuneScapeBot

def simple_example():
    """Simple example of using the RuneScape bot."""
    print("=== Simple RuneScape Bot Example ===\n")
    
    # Initialize the bot with human-like mouse movements
    print("Initializing bot with human-like mouse movements...")
    bot = RuneScapeBot(use_human_paths=True)
    
    # Find RuneScape window
    print("Looking for RuneScape window...")
    window_region = bot.find_runescape_window()
    
    if not window_region:
        print("Could not find RuneScape window. Make sure the game is running.")
        return
    
    bot.window_region = window_region
    print(f"Found RuneScape window at: {window_region}")
    
    # Example: Move mouse to a random position
    print("\nMoving mouse to a random position...")
    success = bot.move_mouse_randomly(distance=100)
    if success:
        print("Random mouse movement successful!")
    else:
        print("Random mouse movement failed.")
    
    # Example: Click on a specific color
    print("\nLooking for pixels with color #00FFFFFA...")
    success = bot.click_random_pixel_by_color("00FFFFFA", tolerance=10, method="smart")
    if success:
        print("Successfully clicked on target pixel!")
    else:
        print("No target pixels found or click failed.")
    
    print("\nSimple example completed!")

def configuration_example():
    """Example of configuring the bot."""
    print("=== Configuration Example ===\n")
    
    # Initialize bot
    bot = RuneScapeBot(use_human_paths=True)
    
    # Configure food area
    print("Setting up food area...")
    food_area = bot.setup_food_area()
    if food_area:
        print(f"Food area configured: {food_area}")
    
    # Configure loot pickup
    print("\nConfiguring loot pickup...")
    loot_config = bot.configure_loot_pickup()
    print(f"Loot configuration: {loot_config}")
    
    print("\nConfiguration example completed!")

if __name__ == "__main__":
    print("Simple RuneScape Bot Examples")
    print("Choose an example to run:")
    print("1. Simple usage example")
    print("2. Configuration example")
    print("3. Both examples")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        simple_example()
    elif choice == "2":
        configuration_example()
    elif choice == "3":
        simple_example()
        print("\n" + "="*50 + "\n")
        configuration_example()
    else:
        print("Invalid choice. Running simple example...")
        simple_example() 