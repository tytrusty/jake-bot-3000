#!/usr/bin/env python3
"""
Fishing Bot Minimap Configuration Script

This script helps you set up the minimap configuration for the fishing bot.
It allows you to configure the minimap center and radius by clicking on the
minimap center and a point on the perimeter.
"""

import json
import os
import sys
import time
import math
import pyautogui
import jake.screenshot_utils
import jake.color_utils
from jake.config_manager import ConfigurationManager

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

def calculate_radius(center_x: int, center_y: int, perimeter_x: int, perimeter_y: int) -> float:
    """Calculate the radius of the minimap circle."""
    dx = perimeter_x - center_x
    dy = perimeter_y - center_y
    radius = math.sqrt(dx*dx + dy*dy)
    return radius

def init_fishing_config():
    """Initialize the fishing bot minimap configuration."""
    print("=== Fishing Bot Minimap Configuration Setup ===")
    print("This script will help you configure the minimap for the fishing bot.")
    print("Make sure RuneScape is running and the minimap is visible.\n")
    
    # Load existing config or create new one
    config_manager = ConfigurationManager("bot_config.json")
    
    # Initialize fishing config if it doesn't exist
    if "fishing" not in config_manager.config:
        config_manager.config["fishing"] = {
            "enabled": False,
            "minimap": {
                "center_x": None,
                "center_y": None,
                "radius": None
            },
            "fishing_spot_color": None,
            "bank_color": None,
            "drop_boxes": [],
            "drop_interval": 30.0,
            "travel_delay": 2.0,
            "fishing_delay": 3.0
        }
    else:
        # Ensure all required keys exist in existing fishing config
        fishing_config = config_manager.config["fishing"]
        
        # Initialize minimap if not present
        if "minimap" not in fishing_config:
            fishing_config["minimap"] = {
                "center_x": None,
                "center_y": None,
                "radius": None
            }
        
        # Initialize drop_boxes if not present
        if "drop_boxes" not in fishing_config:
            fishing_config["drop_boxes"] = []
        
        # Set defaults for missing keys
        if "fishing_spot_color" not in fishing_config:
            fishing_config["fishing_spot_color"] = None
        if "bank_color" not in fishing_config:
            fishing_config["bank_color"] = None
        if "drop_interval" not in fishing_config:
            fishing_config["drop_interval"] = 30.0
        if "travel_delay" not in fishing_config:
            fishing_config["travel_delay"] = 2.0
        if "fishing_delay" not in fishing_config:
            fishing_config["fishing_delay"] = 3.0
    
    print("=== Minimap Configuration ===")
    print("You will need to click on two points on the minimap:")
    print("1. The center of the minimap")
    print("2. A point on the perimeter of the minimap (edge)")
    print("\nThis will help calculate the minimap's radius for navigation.")
    
    # Get minimap center
    print("\nStep 1: Minimap Center")
    center_x, center_y, center_color = get_mouse_position_with_countdown(
        "Move your mouse to the center of the minimap"
    )
    
    # Get minimap perimeter point
    print("\nStep 2: Minimap Perimeter")
    print("Now click on any point on the edge/perimeter of the minimap")
    perimeter_x, perimeter_y, perimeter_color = get_mouse_position_with_countdown(
        "Move your mouse to a point on the minimap perimeter (edge)"
    )
    
    # Calculate radius
    radius = calculate_radius(center_x, center_y, perimeter_x, perimeter_y)
    
    print(f"\nMinimap Configuration Results:")
    print(f"Center: ({center_x}, {center_y})")
    print(f"Perimeter point: ({perimeter_x}, {perimeter_y})")
    print(f"Calculated radius: {radius:.2f} pixels")
    
    # Update config
    config_manager.config["fishing"]["enabled"] = True
    config_manager.config["fishing"]["minimap"]["center_x"] = center_x
    config_manager.config["fishing"]["minimap"]["center_y"] = center_y
    config_manager.config["fishing"]["minimap"]["radius"] = radius
    
    # Optional: Configure fishing spot and bank colors
    print("\n=== Optional: Fishing Spot and Bank Colors ===")
    print("You can configure colors for fishing spots and banks to help with navigation.")
    
    fishing_color_choice = input("Configure fishing spot color? (y/n, default: n): ").strip().lower()
    if fishing_color_choice == 'y':
        print("\nMove your mouse to a fishing spot to capture its color")
        _, _, fishing_color = get_mouse_position_with_countdown(
            "Move your mouse to a fishing spot"
        )
        config_manager.config["fishing"]["fishing_spot_color"] = fishing_color
        print(f"Fishing spot color saved: #{fishing_color}")
    
    bank_color_choice = input("Configure bank color? (y/n, default: n): ").strip().lower()
    if bank_color_choice == 'y':
        print("\nMove your mouse to a bank booth/chest to capture its color")
        _, _, bank_color = get_mouse_position_with_countdown(
            "Move your mouse to a bank booth/chest"
        )
        config_manager.config["fishing"]["bank_color"] = bank_color
        print(f"Bank color saved: #{bank_color}")
    
    # Configure drop boxes
    print("\n=== Drop Box Configuration ===")
    print("Configure up to 16 drop boxes for inventory management.")
    print("Each drop box is a rectangular area in your inventory where items appear when fishing is complete.")
    print("The bot will drop all valid items from these boxes every drop interval.")
    
    drop_boxes_count = 0
    first_box_width = 0
    first_box_height = 20  # Default height
    
    while drop_boxes_count < 16:
        print(f"\nDrop Box {drop_boxes_count + 1}:")
        
        if drop_boxes_count == 0:
            # First box: require top-left and top-right corners
            print("For the first drop box, you need to specify the top-left and top-right corners.")
            print("This will define the size of all subsequent drop boxes.")
            
            # Get top-left corner
            print("Step 1: Move mouse to top-left corner of the drop box")
            top_left_x, top_left_y, top_left_color = get_mouse_position_with_countdown(
                "Move your mouse to top-left corner of the first drop box"
            )
            
            # Get top-right corner
            print("Step 2: Move mouse to top-right corner of the drop box")
            top_right_x, top_right_y, top_right_color = get_mouse_position_with_countdown(
                "Move your mouse to top-right corner of the first drop box"
            )
            
            # Calculate box dimensions
            first_box_width = top_right_x - top_left_x
            # Keep the default height of 20 pixels
            
            # Create first box
            x1, y1 = top_left_x, top_left_y
            x2, y2 = top_right_x, top_left_y + first_box_height
            
            config_manager.config["fishing"]["drop_boxes"].append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "color": top_left_color
            })
            print(f"Drop box {drop_boxes_count + 1} saved: ({x1}, {y1}) to ({x2}, {y2}) with color #{top_left_color}")
            print(f"Box dimensions: {first_box_width} x {first_box_height} pixels")
            
            # Option to customize height for all boxes
            height_choice = input(f"Customize box height? Current: {first_box_height}px (y/n, default: n): ").strip().lower()
            if height_choice == 'y':
                try:
                    new_height = int(input(f"Enter new height in pixels (default {first_box_height}): ").strip())
                    if new_height > 0:
                        first_box_height = new_height
                        # Update the first box with new height
                        config_manager.config["fishing"]["drop_boxes"][-1]["y2"] = top_left_y + first_box_height
                        print(f"Box height updated to {first_box_height}px")
                except ValueError:
                    print("Invalid input, keeping default height")
            
        else:
            # Subsequent boxes: just specify center point
            print(f"For drop box {drop_boxes_count + 1}, just specify the center point.")
            print(f"The box will be {first_box_width} x {first_box_height} pixels centered on your click.")
            
            # Get center point
            center_x, center_y, center_color = get_mouse_position_with_countdown(
                f"Move your mouse to center of drop box {drop_boxes_count + 1}",
                countdown=3
            )
            
            # Calculate box coordinates based on center and dimensions
            half_width = first_box_width // 2
            half_height = first_box_height // 2
            x1 = center_x - half_width
            y1 = center_y - half_height
            x2 = center_x + half_width
            y2 = center_y + half_height
            
            config_manager.config["fishing"]["drop_boxes"].append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "color": center_color
            })
            print(f"Drop box {drop_boxes_count + 1} saved: center ({center_x}, {center_y}) -> ({x1}, {y1}) to ({x2}, {y2}) with color #{center_color}")
        
        drop_boxes_count += 1
        if input("Add another drop box? (y/n): ").strip().lower() == 'n':
            break
    
    # Configure drop interval
    print("\n=== Drop Interval ===")
    print("Every drop interval, the bot will drop all valid items and restart fishing.")
    drop_interval_str = input(f"Drop interval in seconds (default {config_manager.config['fishing']['drop_interval']}): ").strip()
    if drop_interval_str:
        try:
            config_manager.config["fishing"]["drop_interval"] = float(drop_interval_str)
        except ValueError:
            print("Invalid input, using default drop interval")
    
    # Configure delays
    print("\n=== Travel and Fishing Delays ===")
    print("Configure delays for travel and fishing actions:")
    
    travel_delay_str = input(f"Travel delay in seconds (default {config_manager.config['fishing']['travel_delay']}): ").strip()
    if travel_delay_str:
        try:
            config_manager.config["fishing"]["travel_delay"] = float(travel_delay_str)
        except ValueError:
            print("Invalid input, using default travel delay")
    
    fishing_delay_str = input(f"Fishing delay in seconds (default {config_manager.config['fishing']['fishing_delay']}): ").strip()
    if fishing_delay_str:
        try:
            config_manager.config["fishing"]["fishing_delay"] = float(fishing_delay_str)
        except ValueError:
            print("Invalid input, using default fishing delay")
    
    # Show configuration summary
    print("\n=== Configuration Summary ===")
    fishing_config = config_manager.config["fishing"]
    print(f"Fishing bot: {'Enabled' if fishing_config['enabled'] else 'Disabled'}")
    
    minimap_config = fishing_config["minimap"]
    if minimap_config["center_x"] is not None:
        print(f"Minimap center: ({minimap_config['center_x']}, {minimap_config['center_y']})")
        print(f"Minimap radius: {minimap_config['radius']:.2f} pixels")
    
    if fishing_config["fishing_spot_color"]:
        print(f"Fishing spot color: #{fishing_config['fishing_spot_color']}")
    else:
        print("Fishing spot color: Not configured")
    
    if fishing_config["bank_color"]:
        print(f"Bank color: #{fishing_config['bank_color']}")
    else:
        print("Bank color: Not configured")
    
    if fishing_config["drop_boxes"]:
        print("\nConfigured Drop Boxes:")
        for i, drop_box in enumerate(fishing_config["drop_boxes"]):
            print(f"{i+1}. ({drop_box['x1']}, {drop_box['y1']}) to ({drop_box['x2']}, {drop_box['y2']}) with color #{drop_box['color']}")
    else:
        print("Drop boxes: Not configured")
    
    print(f"Drop interval: {fishing_config['drop_interval']} seconds (drops all valid boxes and restarts fishing)")
    print(f"Travel delay: {fishing_config['travel_delay']} seconds")
    print(f"Fishing delay: {fishing_config['fishing_delay']} seconds")
    
    # Save configuration
    print("\n=== Save Configuration ===")
    save_choice = input("Save configuration to bot_config.json? (y/n): ").strip().lower()
    
    if save_choice == 'y':
        if config_manager.save_config():
            print("Fishing configuration saved successfully!")
            print("\nThe minimap is now configured for the fishing bot.")
            print("The bot will use this configuration to navigate between fishing spots and banks.")
        else:
            print("Error saving configuration.")
    else:
        print("Configuration not saved.")

if __name__ == "__main__":
    init_fishing_config() 