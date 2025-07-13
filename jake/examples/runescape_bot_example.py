#!/usr/bin/env python3
"""
RuneScape Bot Example

This is an example script demonstrating how to use the RuneScape bot framework.
It provides an interactive interface for configuring and running the bot.
"""

import sys
import os
import time
import random
import keyboard
import numpy as np
import cv2

# Add the parent directory to the Python path to import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runescape_bot import RuneScapeBot
import screenshot_utils
import color_utils
import pixel_selection

# Optional import for human path finder
try:
    from path.human_path_finder import HumanPath
    HUMAN_PATH_AVAILABLE = True
except ImportError:
    HUMAN_PATH_AVAILABLE = False
    print("Human path finder not available. Install required dependencies for human-like mouse movement.")

def main():
    """Main function for the RuneScape bot example."""
    # Check if user wants to use human-like paths
    use_human_paths = False
    speed_range = (0.5, 2.0)  # Default speed range
    
    if HUMAN_PATH_AVAILABLE:
        human_path_choice = input("Use human-like mouse movement? (y/n, default: n): ").strip().lower()
        use_human_paths = human_path_choice == 'y'
        
        if use_human_paths:
            # Configure speed range
            print("\nSpeed range configuration:")
            print("This controls how fast the mouse moves (multiplier of base speed)")
            print(f"Current default: {speed_range[0]:.1f}x to {speed_range[1]:.1f}x")
            
            configure_speed = input("Configure speed range? (y/n, default: n): ").strip().lower()
            if configure_speed == 'y':
                print("\nSpeed range options:")
                print("1. Slow (0.2x to 0.5x) - Very slow, careful movements")
                print("2. Normal (0.5x to 2.0x) - Default human-like variation")
                print("3. Fast (1.5x to 3.0x) - Quick movements")
                print("4. Custom - Specify your own range")
                
                speed_choice = input("Choose speed option (1-4, default: 2): ").strip()
                if speed_choice == "1":
                    speed_range = (0.2, 0.5)
                elif speed_choice == "3":
                    speed_range = (1.5, 3.0)
                elif speed_choice == "4":
                    try:
                        min_speed = float(input("Enter minimum speed multiplier (e.g., 0.5): ").strip())
                        max_speed = float(input("Enter maximum speed multiplier (e.g., 2.0): ").strip())
                        speed_range = (min_speed, max_speed)
                    except ValueError:
                        print("Invalid input, using default speed range")
                        speed_range = (0.5, 2.0)
                else:
                    speed_range = (0.5, 2.0)  # Default
                
                print(f"Speed range set to: {speed_range[0]:.1f}x to {speed_range[1]:.1f}x")
    
    bot = RuneScapeBot(use_human_paths=use_human_paths)
    
    # Update speed range if human paths are enabled
    if use_human_paths and bot.human_path:
        bot.human_path.speed_range = speed_range
    
    print("RuneScape Bot")
    print("1. Attack Bot (Find pixels by color)")
    print("2. Debug Screenshot")
    print("3. Find Health Bar Position")
    print("4. Find Food Area")
    print("5. Configure Loot Pickup")
    print("6. Exit")
    
    while True:
        choice = input("Choose an option (1-6): ").strip()
        
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
            
            # Get target color from user
            target_color = input("Enter target hex color (default: 00FFFFFA): ").strip()
            if not target_color:
                target_color = "00FFFFFA"
            
            # Get pixel selection method
            print("\nPixel selection methods:")
            print("1. Smart (blob-based with green exclusion)")
            print("2. Random (original method)")
            method_choice = input("Choose pixel selection method (1-2, default: 1): ").strip()
            if method_choice == "2":
                pixel_method = "random"
            else:
                pixel_method = "smart" 
            
            # Check for food area configuration
            food_area = bot.load_food_area()
            if food_area is None:
                print("\nNo food area configured. Auto-eating will be disabled.")
                setup_food = input("Would you like to set up food area now? (y/n): ").strip().lower()
                if setup_food == 'y':
                    food_area = bot.setup_food_area()
                else:
                    print("Continuing without auto-eating. You can set up food area later with option 4.")
            
            # Get red threshold for health monitoring
            red_threshold_str = input("Enter red threshold for health monitoring (default 5): ").strip()
            if not red_threshold_str:
                red_threshold = 5
            else:
                red_threshold = int(red_threshold_str)
            
            # Get random mouse movement option
            random_mouse_str = input("Enable random mouse movement during combat? (y/n, default: n): ").strip().lower()
            random_mouse_movement = random_mouse_str == 'y'
            
            # Get break system option
            break_str = input("Enable automatic breaks (2-6 min breaks every 29-33 min)? (y/n, default: n): ").strip().lower()
            enable_breaks = break_str == 'y'
            
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
                print("Automatic breaks: ENABLED (2-6 min breaks every 29-33 min)")
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
                    
                    # Take a break every 29-33 minutes
                    break_interval = random.uniform(29 * 60, 33 * 60)  # 29-33 minutes in seconds
                    
                    if time_since_last_break >= break_interval:
                        # Calculate break duration (2-6 minutes)
                        break_duration = random.uniform(2 * 60, 6 * 60)  # 2-6 minutes in seconds
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
                success = bot.attack_sequence(target_color, food_area=food_area, red_threshold=red_threshold, pixel_method=pixel_method, random_mouse_movement=random_mouse_movement, enable_breaks=enable_breaks)
                
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
                left_half_region = screenshot_utils.get_left_half_region()
                screenshot_utils.save_screenshot(filename, left_half_region)
                
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
                    screenshot = screenshot_utils.capture_left_half_screen()
                else:
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = screenshot_utils.capture_screen_region(window_region)
                
                print(f"Finding pixels with color {hex_color} and tolerance {tolerance} using method '{debug_method}'...")
                
                if debug_method == "random":
                    pixels = color_utils.find_pixels_by_color(screenshot, hex_color, tolerance)
                else:
                    # Use smart selection to get filtered pixels and debug info
                    downsample_factor = 4  # Can be made configurable
                    result = pixel_selection.smart_pixel_select(screenshot, hex_color, tolerance, return_debug=True, downsample_factor=downsample_factor)
                    if isinstance(result, tuple) and len(result) >= 3:
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
                        pixels = color_utils.find_pixels_by_color(screenshot, hex_color, tolerance)
                
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
            # Find health bar position
            print("\n=== Health Bar Position Finder ===")
            
            # Find RuneScape window first
            window_region = bot.find_runescape_window()
            if not window_region:
                print("Could not find RuneScape window. Make sure the game is running.")
                continue
            
            bot.window_region = window_region
            print(f"Found RuneScape window at: {window_region}")
            
            # Run health bar position finder
            bot.find_health_bar_position()
        elif choice == "4":
            bot.setup_food_area()
        elif choice == "5":
            bot.configure_loot_pickup()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 