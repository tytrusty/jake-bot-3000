#!/usr/bin/env python3
"""
Buy Iron Bot Configuration Initialization Script

This script helps you set up all the configuration parameters for the buy iron bot
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
    print(f"You will have {countdown} seconds to position your mouse.")
    input("Press Enter when you're ready to start the countdown...")
    
    print(f"Starting countdown... You have {countdown} seconds to position your mouse...")
    
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

def get_rectangle_coordinates(description: str) -> list:
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
    
    return [x1, y1, x2, y2]

def init_buy_iron_config():
    """Initialize the buy iron bot configuration."""
    print("=== Buy Iron Bot Configuration Setup ===")
    print("This script will help you set up all configuration parameters for the buy iron bot.")
    print("Make sure RuneScape is running and you're at the starting location.\n")
    print("The bot will perform this sequence:")
    print("1. Click on ladder to climb down")
    print("2. Wait for specified time")
    print("3. Move towards vendor (click in vendor region box)")
    print("4. Click on vendor (target color) and wait 5 seconds")
    print("5. Buy iron ore (click in buy box)")
    print("6. Deposit in bank (target color)")
    print("7. Repeat from step 1\n")
    
    # Default configuration
    default_config = {
        "version": "1.0",
        "description": "Buy Iron Bot Configuration",
        
        # Buy iron specific settings
        "buy_iron": {
            "enabled": True,
            "ladder_color": None,
            "wait_time": 5.0,
            "vendor_color": None,
            "buy_box": None,
            "bank_color": None,
            "color_tolerance": 20,
            "vendor_click_wait": 5.0,
            "verify_clicks": True,
            "inventory_deposit_box": None,
            "vendor_region_box": None
        },
        
        # Human-like movement settings (always enabled)
        "human_movement": {
            "enabled": True,
            "speed_range": [0.5, 2.0],
            "use_random_selection": True,
            "k_nearest": 8,
            "use_iterative_movement": True,
            "max_iterations": 5,
            "tolerance": 10.0
        },
        
        # Debug settings
        "debug": {
            "save_screenshots": True,
            "screenshot_dir": "debug_screenshots"
        }
    }
    
    # Ask for filename first
    filename = input("Enter configuration filename (default: buy_iron_config.json): ").strip()
    if not filename:
        filename = "buy_iron_config.json"
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Try to load existing configuration
    config = default_config.copy()
    existing_config = None
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_config = json.load(f)
            print(f"\nFound existing configuration file: {filename}")
            print("I'll ask you whether you want to update each setting that's already configured.")
        else:
            print(f"\nNo existing configuration file found. Creating new configuration: {filename}")
    except Exception as e:
        print(f"Error reading existing configuration: {e}")
        print("Creating new configuration file.")
    
    # Helper function to ask if user wants to update a setting
    def ask_to_update(setting_name, current_value, description=""):
        if existing_config and setting_name in existing_config:
            existing_value = existing_config[setting_name]
            if existing_value is not None:
                print(f"\n{description}")
                print(f"Current {setting_name}: {existing_value}")
                update_choice = input("Update this setting? (y/n, default: n): ").strip().lower()
                return update_choice == 'y'
        return True  # Always ask if no existing value or no existing config
    
    # Helper function to ask if user wants to update a nested setting
    def ask_to_update_nested(parent_key, setting_name, current_value, description=""):
        if existing_config and parent_key in existing_config and setting_name in existing_config[parent_key]:
            existing_value = existing_config[parent_key][setting_name]
            if existing_value is not None:
                print(f"\n{description}")
                print(f"Current {setting_name}: {existing_value}")
                update_choice = input("Update this setting? (y/n, default: n): ").strip().lower()
                return update_choice == 'y'
        return True  # Always ask if no existing value or no existing config
    
    # Step 1: Ladder configuration
    print("\n=== Step 1: Ladder Configuration ===")
    print("The bot will use color detection to find and click on the ladder.")
    
    # Check if we should update ladder settings
    ladder_color_exists = existing_config and existing_config.get("buy_iron", {}).get("ladder_color") is not None
    
    if ladder_color_exists:
        print(f"Current ladder configuration:")
        if ladder_color_exists and existing_config and "buy_iron" in existing_config:
            print(f"  Ladder color: #{existing_config['buy_iron']['ladder_color']}")
        
        update_ladder = input("Update ladder configuration? (y/n, default: n): ").strip().lower()
        if update_ladder != 'y':
            # Keep existing value
            if ladder_color_exists and existing_config and "buy_iron" in existing_config:
                config["buy_iron"]["ladder_color"] = existing_config["buy_iron"]["ladder_color"]
            print("Keeping existing ladder configuration.")
        else:
            # Configure new ladder settings
            print("\nMove your mouse to the ladder to capture its color")
            _, _, ladder_color = get_mouse_position_with_countdown(
                "Move your mouse to the ladder"
            )
            config["buy_iron"]["ladder_color"] = ladder_color
            print(f"Ladder color saved: #{ladder_color}")
    else:
        # No existing ladder config, configure new one
        print("\nMove your mouse to the ladder to capture its color")
        _, _, ladder_color = get_mouse_position_with_countdown(
            "Move your mouse to the ladder"
        )
        config["buy_iron"]["ladder_color"] = ladder_color
        print(f"Ladder color saved: #{ladder_color}")
    
    # Step 2: Wait time configuration
    if ask_to_update_nested("buy_iron", "wait_time", config["buy_iron"]["wait_time"], 
                           "=== Step 2: Wait Time Configuration ===\nAfter climbing down the ladder, the bot will wait before moving towards the vendor."):
        print("\n=== Step 2: Wait Time Configuration ===")
        print("After climbing down the ladder, the bot will wait before moving towards the vendor.")
        
        wait_time_str = input("Enter wait time in seconds (default: 3.0): ").strip()
        if wait_time_str:
            try:
                config["buy_iron"]["wait_time"] = float(wait_time_str)
            except ValueError:
                print("Invalid input, using default wait time of 3.0 seconds")
                config["buy_iron"]["wait_time"] = 3.0
        else:
            config["buy_iron"]["wait_time"] = 3.0
        
        print(f"Wait time set to: {config['buy_iron']['wait_time']} seconds")
    elif existing_config:
        config["buy_iron"]["wait_time"] = existing_config["buy_iron"]["wait_time"]
        print(f"Keeping existing wait time: {config['buy_iron']['wait_time']} seconds")
    
    # Step 3: Vendor color configuration
    if ask_to_update_nested("buy_iron", "vendor_color", config["buy_iron"]["vendor_color"],
                           "=== Step 3: Vendor Color Configuration ===\nThe bot will click on the vendor using color detection."):
        print("\n=== Step 3: Vendor Color Configuration ===")
        print("The bot will click on the vendor using color detection.")
        print("Move your mouse to the vendor to capture its color.")
        
        _, _, vendor_color = get_mouse_position_with_countdown(
            "Move your mouse to the vendor"
        )
        config["buy_iron"]["vendor_color"] = vendor_color
        print(f"Vendor color saved: #{vendor_color}")
    elif existing_config:
        config["buy_iron"]["vendor_color"] = existing_config["buy_iron"]["vendor_color"]
        print(f"Keeping existing vendor color: #{config['buy_iron']['vendor_color']}")
    
    # Step 3.5: Vendor region box configuration
    if ask_to_update_nested("buy_iron", "vendor_region_box", config["buy_iron"]["vendor_region_box"],
                           "=== Step 3.5: Vendor Region Box Configuration ===\nDefine the region where the bot will click randomly to find the vendor."):
        print("\n=== Step 3.5: Vendor Region Box Configuration ===")
        print("Define the region where the bot will click randomly to find the vendor.")
        print("This should be an area where the vendor is typically located.")
        
        vendor_region_box = get_rectangle_coordinates("Set up vendor region box")
        config["buy_iron"]["vendor_region_box"] = vendor_region_box
        print(f"Vendor region box saved: {vendor_region_box}")
    elif existing_config:
        config["buy_iron"]["vendor_region_box"] = existing_config["buy_iron"]["vendor_region_box"]
        print(f"Keeping existing vendor region box: {config['buy_iron']['vendor_region_box']}")
    
    # Step 4: Buy box configuration
    if ask_to_update_nested("buy_iron", "buy_box", config["buy_iron"]["buy_box"],
                           "=== Step 4: Buy Box Configuration ===\nDefine the area where the 'Buy' button or iron ore selection is located."):
        print("\n=== Step 4: Buy Box Configuration ===")
        print("Define the area where the 'Buy' button or iron ore selection is located.")
        print("This is where the bot will click to purchase iron ore.")
        
        buy_box = get_rectangle_coordinates("Set up buy iron ore area")
        config["buy_iron"]["buy_box"] = buy_box
        print(f"Buy box saved: {buy_box}")
    elif existing_config:
        config["buy_iron"]["buy_box"] = existing_config["buy_iron"]["buy_box"]
        print(f"Keeping existing buy box: {config['buy_iron']['buy_box']}")
    
    # Step 5: Bank color configuration
    if ask_to_update_nested("buy_iron", "bank_color", config["buy_iron"]["bank_color"],
                           "=== Step 5: Bank Color Configuration ===\nThe bot will click on the bank using color detection."):
        print("\n=== Step 5: Bank Color Configuration ===")
        print("The bot will click on the bank using color detection.")
        print("Move your mouse to the bank booth/chest to capture its color.")
        
        _, _, bank_color = get_mouse_position_with_countdown(
            "Move your mouse to the bank booth/chest"
        )
        config["buy_iron"]["bank_color"] = bank_color
        print(f"Bank color saved: #{bank_color}")
    elif existing_config:
        config["buy_iron"]["bank_color"] = existing_config["buy_iron"]["bank_color"]
        print(f"Keeping existing bank color: #{config['buy_iron']['bank_color']}")
    
    # Step 5.5: Inventory deposit box configuration
    if ask_to_update_nested("buy_iron", "inventory_deposit_box", config["buy_iron"]["inventory_deposit_box"],
                           "=== Step 5.5: Inventory Deposit Box Configuration ===\nAfter clicking the banker, the bot will click on an inventory box to deposit items."):
        print("\n=== Step 5.5: Inventory Deposit Box Configuration ===")
        print("After clicking the banker, the bot will click on an inventory box to deposit items.")
        print("Define the area where items appear in your inventory.")
        
        inventory_box = get_rectangle_coordinates("Set up inventory deposit box area")
        config["buy_iron"]["inventory_deposit_box"] = inventory_box
        print(f"Inventory deposit box saved: {inventory_box}")
    elif existing_config:
        config["buy_iron"]["inventory_deposit_box"] = existing_config["buy_iron"]["inventory_deposit_box"]
        print(f"Keeping existing inventory deposit box: {config['buy_iron']['inventory_deposit_box']}")
    
    # Step 6: Color tolerance configuration
    if ask_to_update_nested("buy_iron", "color_tolerance", config["buy_iron"]["color_tolerance"],
                           "=== Step 6: Color Tolerance Configuration ===\nColor tolerance determines how strict the color matching is."):
        print("\n=== Step 6: Color Tolerance Configuration ===")
        print("Color tolerance determines how strict the color matching is.")
        print("Lower values (5-10) = more strict, Higher values (20-50) = more flexible")
        
        tolerance_str = input("Enter color tolerance (0-255, default: 20): ").strip()
        if tolerance_str:
            try:
                tolerance = int(tolerance_str)
                if 0 <= tolerance <= 255:
                    config["buy_iron"]["color_tolerance"] = tolerance
                else:
                    print("Tolerance must be between 0 and 255, using default value of 20")
                    config["buy_iron"]["color_tolerance"] = 20
            except ValueError:
                print("Invalid input, using default tolerance of 20")
                config["buy_iron"]["color_tolerance"] = 20
        else:
            config["buy_iron"]["color_tolerance"] = 20
        
        print(f"Color tolerance set to: {config['buy_iron']['color_tolerance']}")
    elif existing_config:
        config["buy_iron"]["color_tolerance"] = existing_config["buy_iron"]["color_tolerance"]
        print(f"Keeping existing color tolerance: {config['buy_iron']['color_tolerance']}")
    
    # Step 7: Vendor click wait configuration
    if ask_to_update_nested("buy_iron", "vendor_click_wait", config["buy_iron"]["vendor_click_wait"],
                           "=== Step 7: Vendor Click Wait Configuration ===\nAfter clicking on the vendor, the bot will wait before proceeding to buy iron ore."):
        print("\n=== Step 7: Vendor Click Wait Configuration ===")
        print("After clicking on the vendor, the bot will wait before proceeding to buy iron ore.")
        
        click_wait_str = input(f"Enter wait time after clicking vendor in seconds (default: {config['buy_iron']['vendor_click_wait']}): ").strip()
        if click_wait_str:
            try:
                click_wait = float(click_wait_str)
                if click_wait >= 0:
                    config["buy_iron"]["vendor_click_wait"] = click_wait
                else:
                    print("Wait time must be non-negative, using default value")
            except ValueError:
                print("Invalid input, using default value")
        
        print(f"Vendor click wait time: {config['buy_iron']['vendor_click_wait']} seconds")
    elif existing_config:
        config["buy_iron"]["vendor_click_wait"] = existing_config["buy_iron"]["vendor_click_wait"]
        print(f"Keeping existing vendor click wait: {config['buy_iron']['vendor_click_wait']} seconds")
    
    # Step 7.5: Click verification configuration
    if ask_to_update_nested("buy_iron", "verify_clicks", config["buy_iron"]["verify_clicks"],
                           "=== Step 7.5: Click Verification Configuration ===\nClick verification ensures that clicks on moving targets (vendor/bank) actually land on the correct color."):
        print("\n=== Step 7.5: Click Verification Configuration ===")
        print("Click verification ensures that clicks on moving targets (vendor/bank) actually land on the correct color.")
        print("This helps handle cases where the target moves between detection and clicking.")
        
        verify_choice = input("Enable click verification? (y/n, default: y): ").strip().lower()
        config["buy_iron"]["verify_clicks"] = verify_choice != 'n'
        
        if config["buy_iron"]["verify_clicks"]:
            print("Click verification enabled. Bot will retry clicks if they don't land on target color.")
        else:
            print("Click verification disabled. Bot will not verify clicks.")
    elif existing_config:
        config["buy_iron"]["verify_clicks"] = existing_config["buy_iron"]["verify_clicks"]
        print(f"Keeping existing click verification setting: {'Enabled' if config['buy_iron']['verify_clicks'] else 'Disabled'}")
    
    # Step 8: Human movement configuration
    if ask_to_update_nested("human_movement", "speed_range", config["human_movement"]["speed_range"],
                           "=== Step 8: Human-like Movement Configuration ===\nThe bot will always use human-like mouse movement for more realistic behavior."):
        print("\n=== Step 8: Human-like Movement Configuration ===")
        print("The bot will always use human-like mouse movement for more realistic behavior.")
        print("This cannot be disabled as it helps avoid detection.")
        
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
    elif existing_config:
        config["human_movement"]["speed_range"] = existing_config["human_movement"]["speed_range"]
        print(f"Keeping existing speed range: {config['human_movement']['speed_range'][0]:.1f}x to {config['human_movement']['speed_range'][1]:.1f}x")
    
    # Step 9: Debug configuration
    if ask_to_update_nested("debug", "save_screenshots", config["debug"]["save_screenshots"],
                           "=== Step 9: Debug Configuration ===\nEnable debug screenshots for troubleshooting."):
        print("\n=== Step 9: Debug Configuration ===")
        debug_choice = input("Enable debug screenshots? (y/n, default: y): ").strip().lower()
        config["debug"]["save_screenshots"] = debug_choice != 'n'
        
        if config["debug"]["save_screenshots"]:
            screenshot_dir = input("Enter screenshot directory (default: debug_screenshots): ").strip()
            if screenshot_dir:
                config["debug"]["screenshot_dir"] = screenshot_dir
            else:
                config["debug"]["screenshot_dir"] = "debug_screenshots"
            print(f"Debug screenshots will be saved to: {config['debug']['screenshot_dir']}")
    elif existing_config:
        config["debug"]["save_screenshots"] = existing_config["debug"]["save_screenshots"]
        config["debug"]["screenshot_dir"] = existing_config["debug"]["screenshot_dir"]
        print(f"Keeping existing debug settings: {'Enabled' if config['debug']['save_screenshots'] else 'Disabled'}")
    
    # Save configuration
    print("\n=== Configuration Summary ===")
    print("Your configuration:")
    print(f"- Ladder color: #{config['buy_iron']['ladder_color']}")
    print(f"- Wait time: {config['buy_iron']['wait_time']} seconds")
    print(f"- Vendor color: #{config['buy_iron']['vendor_color']}")
    print(f"- Vendor region box: {config['buy_iron']['vendor_region_box']}")
    print(f"- Buy box: {config['buy_iron']['buy_box']}")
    print(f"- Bank color: #{config['buy_iron']['bank_color']}")
    print(f"- Inventory deposit box: {config['buy_iron']['inventory_deposit_box']}")
    print(f"- Color tolerance: {config['buy_iron']['color_tolerance']}")
    print(f"- Vendor click wait: {config['buy_iron']['vendor_click_wait']} seconds")
    print(f"- Click verification: {'Enabled' if config['buy_iron']['verify_clicks'] else 'Disabled'}")
    print(f"- Human movement: Always enabled (speed: {config['human_movement']['speed_range'][0]:.1f}x to {config['human_movement']['speed_range'][1]:.1f}x)")
    print(f"- Debug screenshots: {'Enabled' if config['debug']['save_screenshots'] else 'Disabled'}")
    
    # Save the configuration
    try:
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {filename}")
        print("\nYou can now run the buy iron bot with:")
        print(f"python jake/buy_iron_script.py {filename}")
        print("\nOr use the example script:")
        print("python jake/examples/buy_iron_example.py")
        
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False
    
    return True

def main():
    """Main function."""
    try:
        success = init_buy_iron_config()
        if success:
            print("\nConfiguration setup completed successfully!")
        else:
            print("\nConfiguration setup failed.")
    except KeyboardInterrupt:
        print("\n\nConfiguration setup cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main() 