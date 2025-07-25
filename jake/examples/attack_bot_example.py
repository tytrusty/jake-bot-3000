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

            # Get target color from user (with default from config)
            target_color = input(f"Enter target hex color (default: {bot.default_target_color}): ").strip()
            if not target_color:
                target_color = bot.default_target_color
            
            bot.print_config_summary()
            bot.run(target_hex_color=target_color)
        
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
                try:
                    window_region = jake.screenshot_utils.find_runescape_window("RuneLite")
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = jake.screenshot_utils.capture_screen_region(window_region)
                except Exception as e:
                    print(f"Could not find RuneScape window. Using left half of screen instead. Error: {e}")
                    screenshot = jake.screenshot_utils.capture_left_half_screen()
                
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