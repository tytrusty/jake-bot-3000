#!/usr/bin/env python3
"""
RuneScape Bot Example

This is an example script demonstrating how to use the RuneScape bot framework.
It loads configuration from a JSON file and provides an interactive interface.
"""

import sys
import os
import time
import random
import keyboard
import numpy as np
import cv2
import argparse

# Add the parent directory to the Python path to import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jake.bots.attack_bot import AttackBot
from jake.config_manager import ConfigurationManager
import jake.screenshot_utils
import jake.color_utils
import pixel_selection
from jake.path import HumanPath

def main():
    """Main function for the RuneScape bot example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RuneScape Bot Example')
    parser.add_argument('config_file', nargs='?', default='bot_config.json',
                       help='Path to configuration file (default: bot_config.json)')
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigurationManager(args.config_file)
    if not config_manager.load_config():
        print(f"\nConfiguration file '{args.config_file}' not found or invalid.")
        print("Please run 'python init_config.py' to create a configuration file.")
        return
    
    # Display configuration summary
    config_manager.print_config_summary()
    
    # Initialize bot with configuration
    use_human_paths = config_manager.is_human_movement_enabled()
    bot = AttackBot(config_manager=config_manager, use_human_paths=use_human_paths)
    
    # Update human path settings if enabled
    if use_human_paths and bot.human_path:
        human_config = config_manager.get_human_movement_config()
        speed_range = config_manager.get_speed_range()
        bot.human_path.speed_range = speed_range
        
        # Update other human path settings
        if 'use_random_selection' in human_config:
            bot.human_path.use_random_selection = human_config['use_random_selection']
        if 'k' in human_config:
            bot.human_path.k = human_config['k']
        if 'use_iterative_movement' in human_config:
            bot.human_path.use_iterative_movement = human_config['use_iterative_movement']
        if 'max_iterations' in human_config:
            bot.human_path.max_iterations = human_config['max_iterations']
        if 'tolerance' in human_config:
            bot.human_path.tolerance = human_config['tolerance']
    
    print("RuneScape Bot")
    print("1. Attack Bot (Find pixels by color)")
    print("2. Debug Screenshot")
    print("3. Reconfigure Settings")
    print("4. Exit")
    
    while True:
        choice = input("Choose an option (1-4): ").strip()
        
        if choice == "1":
            # Attack bot functionality
            print("\n=== Attack Bot ===")
            
            # Find RuneScape window first
            window_region = bot.find_runescape_window()
            if not window_region:
                print("Could not find RuneScape window. Make sure the game is running.")
                continue
            
            bot.window_region = window_region
            print(f"Found RuneScape window at: {window_region}")
            
            # Get target color from user (with default from config)
            combat_config = config_manager.get_combat_config()
            default_color = combat_config.get('default_target_color', '00FFFFFA')
            target_color = input(f"Enter target hex color (default: {default_color}): ").strip()
            if not target_color:
                target_color = default_color
            
            # Get pixel selection method from config
            pixel_method = combat_config.get('pixel_method', 'smart')
            
            # Get food area from config
            food_area = None
            if config_manager.is_food_area_enabled():
                food_area = config_manager.get_food_area_coordinates()
                if food_area:
                    print(f"Using configured food area: {food_area}")
                else:
                    print("Food area enabled but coordinates not found in config")
            else:
                print("Auto-eating disabled in configuration")
            
            # Get red threshold from config
            food_config = config_manager.get_food_area_config()
            red_threshold = food_config.get('red_threshold', 5)
            
            # Get random mouse movement from config
            random_mouse_movement = config_manager.is_random_mouse_movement_enabled()
            
            # Get break settings from config
            enable_breaks = config_manager.is_breaks_enabled()
            
            # Run attack sequence
            print(f"\nStarting attack bot with color: {target_color}")
            print(f"Using pixel selection method: {pixel_method}")
            if food_area:
                print(f"Auto-eating enabled with food area: {food_area}")
                print(f"Health monitoring threshold: {red_threshold}")
            else:
                print("Auto-eating disabled - no food area configured")
            if random_mouse_movement:
                print("Random mouse movement during combat: ENABLED")
            else:
                print("Random mouse movement during combat: DISABLED")
            if enable_breaks:
                break_config = combat_config
                print(f"Automatic breaks: ENABLED ({break_config.get('break_interval_min', 29)}-{break_config.get('break_interval_max', 33)} min intervals, {break_config.get('break_duration_min', 2)}-{break_config.get('break_duration_max', 6)} min breaks)")
            else:
                print("Automatic breaks: DISABLED")
            print("Press 'q' to stop the attack sequence")
            
            bot.running = True
            session_start_time = time.time()
            last_break_time = session_start_time
            
            while bot.running:
                if keyboard.is_pressed('q'):
                    print("Stopping attack bot...")
                    bot.running = False
                    break
                
                # Check if it's time for a break
                if enable_breaks:
                    current_time = time.time()
                    session_duration = current_time - session_start_time
                    time_since_last_break = current_time - last_break_time
                    
                    # Get break settings from config
                    break_config = combat_config
                    break_interval = random.uniform(
                        break_config.get('break_interval_min', 29) * 60,
                        break_config.get('break_interval_max', 33) * 60
                    )
                    
                    if time_since_last_break >= break_interval:
                        # Calculate break duration from config
                        break_duration = random.uniform(
                            break_config.get('break_duration_min', 2) * 60,
                            break_config.get('break_duration_max', 6) * 60
                        )
                        break_minutes = break_duration / 60
                        
                        # Log break to file
                        break_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        break_log_entry = f"{break_timestamp} - Break started: {break_minutes:.1f} minute break after {time_since_last_break / 60:.1f} minutes of activity"
                        
                        try:
                            with open("break_log.txt", "a") as f:
                                f.write(break_log_entry + "\n")
                            print(f"Break logged to break_log.txt")
                        except Exception as e:
                            print(f"Error logging break: {e}")
                        
                        print(f"\n=== TAKING BREAK ===")
                        print(f"Session duration: {session_duration / 60:.1f} minutes")
                        print(f"Time since last break: {time_since_last_break / 60:.1f} minutes")
                        print(f"Taking a {break_minutes:.1f} minute break...")
                        print("You can manually stop the bot during break by pressing 'q'")
                        
                        # Take the break
                        break_start = time.time()
                        while time.time() - break_start < break_duration and bot.running:
                            if keyboard.is_pressed('q'):
                                print("Stopping attack bot during break...")
                                bot.running = False
                                break
                            
                            # Show countdown every 30 seconds
                            remaining = break_duration - (time.time() - break_start)
                            if int(remaining) % 30 == 0 and remaining > 0:
                                print(f"Break remaining: {remaining / 60:.1f} minutes")
                            
                            time.sleep(1)
                        
                        if bot.running:
                            # Log break completion
                            break_end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                            break_end_entry = f"{break_end_timestamp} - Break finished: {break_minutes:.1f} minute break completed"
                            
                            try:
                                with open("break_log.txt", "a") as f:
                                    f.write(break_end_entry + "\n")
                            except Exception as e:
                                print(f"Error logging break completion: {e}")
                            
                            print("Break finished! Resuming attack sequence...")
                            last_break_time = time.time()
                            continue
                
                # Run one attack sequence with food eating
                success = bot.attack_sequence(
                    target_color, 
                    food_area=food_area, 
                    red_threshold=red_threshold, 
                    pixel_method=pixel_method, 
                    random_mouse_movement=random_mouse_movement, 
                    enable_breaks=enable_breaks
                )
                
                if success:
                    print("Attack successful! Waiting before next attack...")
                    time.sleep(3)  # Wait 3 seconds before next attack
                else:
                    print("Attack failed or no targets found. Retrying...")
                    time.sleep(1)
        
        elif choice == "2":
            # Debug screenshot functionality
            print("\n=== Debug Screenshot (Left Half of Screen) ===")
            
            print("Debug options:")
            print("1. Save regular screenshot of left half")
            print("2. Find pixels by color and save highlighted screenshot")
            print("3. Back to main menu")
            
            debug_choice = input("Choose debug option (1-3): ").strip()
            
            if debug_choice == "1":
                filename = input("Enter filename (or press Enter for auto): ").strip()
                if not filename:
                    filename = None
                left_half_region = jake.screenshot_utils.get_left_half_region()
                jake.screenshot_utils.save_screenshot(filename, left_half_region)
                
            elif debug_choice == "2":
                hex_color = input("Enter hex color to find (e.g., 00FFFFFA): ").strip()
                if not hex_color:
                    hex_color = "00FFFFFA"
                
                tolerance = input("Enter color tolerance (default 10): ").strip()
                if not tolerance:
                    tolerance = 10
                else:
                    tolerance = int(tolerance)
                
                print("\nPixel selection methods:")
                print("1. Smart (blob-based with green exclusion)")
                print("2. Random (original method)")
                method_choice = input("Choose pixel selection method (1-2, default: 1): ").strip()
                if method_choice == "2":
                    debug_method = "random"
                else:
                    debug_method = "smart"
                
                # Find RuneScape window for debug
                window_region = bot.find_runescape_window()
                if not window_region:
                    print("Could not find RuneScape window. Using left half of screen instead.")
                    screenshot = jake.screenshot_utils.capture_left_half_screen()
                else:
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = jake.screenshot_utils.capture_screen_region(window_region)
                
                print(f"Finding pixels with color {hex_color} and tolerance {tolerance} using method '{debug_method}'...")
                
                if debug_method == "random":
                    pixels = jake.color_utils.find_pixels_by_color(screenshot, hex_color, tolerance)
                else:
                    # Use smart selection to get filtered pixels and debug info
                    downsample_factor = 4  # Can be made configurable
                    result = pixel_selection.smart_pixel_select(screenshot, hex_color, tolerance, return_debug=True, downsample_factor=downsample_factor)
                    if isinstance(result, tuple) and len(result) >= 3:
                        print(f"Result: {result}")
                        if len(result) == 4:
                            selected_pixel, labeled_blobs, filtered_target_mask, prob_heatmap = result
                            # Save probability heatmap
                            prob_heatmap_normalized = (prob_heatmap * 255).astype(np.uint8)
                            prob_heatmap_colored = cv2.applyColorMap(prob_heatmap_normalized, cv2.COLORMAP_JET)
                            cv2.imwrite(f"debug_screenshots/debug_screenshot_{hex_color}_{tolerance}_{debug_method}_probability_heatmap.png", prob_heatmap_colored)
                        else:
                            selected_pixel, labeled_blobs, filtered_target_mask = result
                        
                        if selected_pixel:
                            # Get all valid pixels from the filtered mask
                            filtered_pixels = np.where(filtered_target_mask)
                            pixels = list(zip(filtered_pixels[1], filtered_pixels[0]))
                        else:
                            pixels = []
                    else:
                        # Fallback to random selection if smart selection failed
                        pixels = jake.color_utils.find_pixels_by_color(screenshot, hex_color, tolerance)
                
                if pixels:
                    print(f"Found {len(pixels)} pixels! Check debug_screenshots/ folder for highlighted image.")
                    # Save the screenshot with the labels "labeled_blobs" to image
                    labeled_blobs = labeled_blobs.astype(np.uint8) * 255
                    filtered_target_mask = filtered_target_mask.astype(np.uint8) * 255
                    cv2.imwrite(f"debug_screenshots/debug_screenshot_{hex_color}_{tolerance}_{debug_method}_labeled_blobs.png", labeled_blobs)
                    cv2.imwrite(f"debug_screenshots/debug_screenshot_{hex_color}_{tolerance}_{debug_method}_filtered_target_mask.png", filtered_target_mask)
                else:
                    print("No pixels found. Check debug_screenshots/ folder for screenshot.")
            
            elif debug_choice == "3":
                continue
            else:
                print("Invalid debug choice.")
        
        elif choice == "3":
            # Reconfigure settings
            print("\n=== Reconfigure Settings ===")
            print("To reconfigure settings, run:")
            print("python init_config.py")
            print("\nThis will create a new configuration file with your updated settings.")
        
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 