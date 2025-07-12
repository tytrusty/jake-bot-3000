#!/usr/bin/env python3
"""
Color Picker Utility for RuneScape Bot
Helps you find the exact colors on your screen
"""

import pyautogui
import time
import screenshot_utils
import color_utils
import pixel_selection

def main():
    print("=== RuneScape Bot Color Picker ===")
    print("This utility helps you find the exact colors on your screen")
    print()
    
    while True:
        print("\nOptions:")
        print("1. Get color at mouse position")
        print("2. Find unique colors in left half of screen")
        print("3. Test color matching with tolerance")
        print("4. Test smart pixel selection (blob detection)")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            print("\n=== Color at Mouse Position ===")
            print("Move your mouse to the pixel you want to check")
            print("You have 5 seconds to position your mouse...")
            
            for i in range(5, 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
            print()
            
            # Get mouse position and color
            mouse_x, mouse_y = pyautogui.position()
            rgb_color = screenshot_utils.get_pixel_color_at_position(mouse_x, mouse_y)
            hex_color = color_utils.rgb_to_hex(rgb_color)
            
            print(f"\nMouse position: ({mouse_x}, {mouse_y})")
            print(f"Color: RGB{rgb_color} = #{hex_color}")
            
        elif choice == "2":
            print("\n=== Finding Unique Colors ===")
            print("This may take a moment...")
            
            # Try to find RuneScape window first
            try:
                from runescape_bot import RuneScapeBot
                bot = RuneScapeBot()
                window_region = bot.find_runescape_window()
                if window_region:
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = screenshot_utils.capture_screen_region(window_region)
                else:
                    print("Could not find RuneScape window. Using left half of screen instead.")
                    screenshot = screenshot_utils.capture_left_half_screen()
            except:
                print("Using left half of screen")
                screenshot = screenshot_utils.capture_left_half_screen()
            
            unique_colors = color_utils.find_colors_in_region(screenshot)
            
            print(f"\nFound {len(unique_colors)} unique colors")
            print("Most common colors (first 20):")
            
            for i, color in enumerate(unique_colors[:20]):
                hex_color = color_utils.rgb_to_hex(color)
                print(f"  {i+1:2d}. RGB{color} = #{hex_color}")
                
        elif choice == "3":
            print("\n=== Test Color Matching ===")
            
            # Get target color
            target_hex = input("Enter hex color to test (e.g., FF00FF): ").strip()
            if not target_hex:
                print("No color entered, skipping...")
                continue
            
            # Get tolerance
            tolerance_input = input("Enter tolerance (default 10): ").strip()
            tolerance = int(tolerance_input) if tolerance_input else 10
            
            print(f"\nTesting color #{target_hex} with tolerance {tolerance}")
            
            # Test the color matching
            # Try to find RuneScape window first
            try:
                from runescape_bot import RuneScapeBot
                bot = RuneScapeBot()
                window_region = bot.find_runescape_window()
                if window_region:
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = screenshot_utils.capture_screen_region(window_region)
                else:
                    print("Could not find RuneScape window. Using left half of screen instead.")
                    screenshot = screenshot_utils.capture_left_half_screen()
            except:
                print("Using left half of screen")
                screenshot = screenshot_utils.capture_left_half_screen()
            
            pixels = color_utils.find_pixels_by_color(screenshot, target_hex, tolerance)
            
            if pixels:
                print(f"Found {len(pixels)} pixels!")
                print("First 5 coordinates:")
                for i, (x, y) in enumerate(pixels[:5]):
                    print(f"  {i+1}: ({x}, {y})")
            else:
                print("No pixels found with that color")
                
        elif choice == "4":
            print("\n=== Test Smart Pixel Selection ===")
            
            # Get target color
            target_hex = input("Enter hex color to test (e.g., FF00FF): ").strip()
            if not target_hex:
                print("No color entered, skipping...")
                continue
            
            # Get tolerance
            tolerance_input = input("Enter tolerance (default 10): ").strip()
            tolerance = int(tolerance_input) if tolerance_input else 10
            
            print(f"\nTesting smart pixel selection for color #{target_hex} with tolerance {tolerance}")
            
            # Capture screenshot and test smart selection
            # Try to find RuneScape window first
            try:
                from runescape_bot import RuneScapeBot
                bot = RuneScapeBot()
                window_region = bot.find_runescape_window()
                if window_region:
                    print(f"Using RuneScape window region: {window_region}")
                    screenshot = screenshot_utils.capture_screen_region(window_region)
                else:
                    print("Could not find RuneScape window. Using left half of screen instead.")
                    screenshot = screenshot_utils.capture_left_half_screen()
            except:
                print("Using left half of screen")
                screenshot = screenshot_utils.capture_left_half_screen()
            
            # Get downsampling factor from user
            downsample_input = input("Enter downsampling factor (default 4, 1 = no downsampling): ").strip()
            downsample_factor = int(downsample_input) if downsample_input else 4
            
            selected_pixel = pixel_selection.smart_pixel_select(screenshot, target_hex, tolerance, downsample_factor=downsample_factor)
            
            if selected_pixel:
                print(f"Smart selection found pixel: {selected_pixel}")
                
                # Also test random selection for comparison
                random_pixel = pixel_selection.random_pixel_select(screenshot, target_hex, tolerance)
                if random_pixel:
                    print(f"Random selection found pixel: {random_pixel}")
                else:
                    print("Random selection found no pixels")
                
                # Save debug screenshot
                save_debug = input("Save debug screenshot? (y/n): ").strip().lower()
                if save_debug == 'y':
                    import cv2
                    import os
                    
                    # Create debug directory if it doesn't exist
                    debug_dir = "debug_screenshots"
                    if not os.path.exists(debug_dir):
                        os.makedirs(debug_dir)
                    
                    # Save original screenshot with selected pixels highlighted
                    debug_screenshot = screenshot.copy()
                    if selected_pixel:
                        cv2.circle(debug_screenshot, selected_pixel, 5, (0, 255, 0), -1)  # Green circle
                    if random_pixel:
                        cv2.circle(debug_screenshot, random_pixel, 5, (255, 0, 0), -1)   # Blue circle
                    
                    filename = f"color_picker_debug_{target_hex}_{tolerance}.png"
                    filepath = os.path.join(debug_dir, filename)
                    cv2.imwrite(filepath, debug_screenshot)
                    print(f"Debug screenshot saved: {filepath}")
            else:
                print("Smart selection found no valid pixels (all blobs had green neighbors)")
                
        elif choice == "5":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 