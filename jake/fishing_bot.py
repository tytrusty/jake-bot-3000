#!/usr/bin/env python3
"""
Fishing Bot

This bot implements fishing functionality with the following features:
- Click on fishing spots based on target color
- Monitor when fishing spots run out (color changes)
- Poll inventory area to detect when fishing is complete
- Automatic fishing spot switching when current spot runs out
"""

import time
import random
import pyautogui
import cv2
import numpy as np
import jake.screenshot_utils
import jake.color_utils
import jake.pixel_selection
import jake.mouse_movement
from jake.config_manager import ConfigurationManager
from typing import Optional, Tuple, List

class FishingBot:
    """Fishing bot that handles fishing spot detection and inventory polling."""
    
    def __init__(self, config_file: str = "bot_config.json"):
        """
        Initialize the fishing bot.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_manager = ConfigurationManager(config_file)
        self.config = self.config_manager.config
        
        # Load fishing configuration
        self.fishing_config = self.config.get("fishing", {})
        if not self.fishing_config.get("enabled", False):
            raise ValueError("Fishing bot is not enabled in configuration")
        
        # Load fishing-specific settings
        self.fishing_spot_color = self.fishing_config.get("fishing_spot_color")
        self.drop_boxes = self.fishing_config.get("drop_boxes", [])
        self.drop_interval = self.fishing_config.get("drop_interval", 5.0)
        self.fishing_delay = self.fishing_config.get("fishing_delay", 3.0)
        
        # Load general bot settings
        self.human_movement = self.config.get("human_movement", {})
        self.combat_config = self.config.get("combat", {})
        
        # Current fishing state
        self.current_fishing_spot = None
        self.is_fishing = False
        
        # Debug settings
        self.debug_enabled = self.config.get("debug", {}).get("save_screenshots", True)
        
        # Window detection
        self.window_title = "RuneLite"
        self.window_region = None
        
        print("Fishing Bot initialized")
        print(f"Fishing spot color: #{self.fishing_spot_color}")
        print(f"Drop boxes: {len(self.drop_boxes)} configured")
        print(f"Drop interval: {self.drop_interval}s (drops all valid boxes and restarts fishing)")
        print(f"Fishing delay: {self.fishing_delay}s")
        print(f"Debug mode: {'Enabled' if self.debug_enabled else 'Disabled'}")
    
    def find_runescape_window(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Find the RuneScape window and return its coordinates (x, y, width, height)
        """
        try:
            # Try to find window by title
            import win32gui
            import win32con
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if self.window_title.lower() in window_title.lower():
                        rect = win32gui.GetWindowRect(hwnd)
                        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
                        windows.append((x, y, w, h))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                return windows[0]  # Return the first matching window
            else:
                print(f"Could not find window with title containing '{self.window_title}'")
                return None
                
        except ImportError:
            print("win32gui not available. Please install pywin32: pip install pywin32")
            return None
        except Exception as e:
            print(f"Error finding window: {e}")
            return None
    
    def find_fishing_spot(self) -> Optional[Tuple[int, int]]:
        """
        Find a fishing spot with the target color.
        
        Returns:
            Tuple of (x, y) coordinates if found, None otherwise
        """
        if not self.fishing_spot_color:
            print("No fishing spot color configured")
            return None
        
        print(f"Searching for fishing spot with color #{self.fishing_spot_color}")
        
        # Find RuneScape window if not already found
        if self.window_region is None:
            self.window_region = self.find_runescape_window()
            if not self.window_region:
                print("Could not find RuneScape window")
                return None
        
        # Convert hex color to RGB
        try:
            rgb_color = jake.color_utils.hex_to_rgb(self.fishing_spot_color)
        except ValueError:
            print(f"Invalid fishing spot color: #{self.fishing_spot_color}")
            return None
        
        # Use pixel selection to find fishing spots
        tolerance = 20  # Color tolerance for fishing spots
        
        # Capture screenshot of the RuneScape window
        screenshot = jake.screenshot_utils.capture_screen_region(self.window_region)
        if screenshot is None:
            print("Failed to capture screenshot")
            return None
        
        # Convert hex color to hex string for the function
        hex_color = jake.color_utils.rgb_to_hex(rgb_color)
        
        # Search for pixels with the target color
        matching_pixels = jake.color_utils.find_pixels_by_color(
            screenshot, hex_color, tolerance
        )
        
        if not matching_pixels:
            print("No fishing spots found")
            return None
        
        # Calculate window center coordinates
        window_width = self.window_region[2]
        window_height = self.window_region[3]
        center_x = window_width // 2
        center_y = window_height // 2
        
        # Calculate distances from center for all matching pixels
        distances = []
        for pixel in matching_pixels:
            distance = ((pixel[0] - center_x) ** 2 + (pixel[1] - center_y) ** 2) ** 0.5
            distances.append(distance)
        
        # Calculate probabilities based on distance (closer = higher probability)
        # Use inverse distance weighting: probability = 1 / (distance + 1)
        # Add 1 to avoid division by zero
        probabilities = [1.0 / (distance + 1) for distance in distances]
        
        # Normalize probabilities to sum to 1
        total_prob = sum(probabilities)
        if total_prob > 0:
            normalized_probabilities = [p / total_prob for p in probabilities]
        else:
            # Fallback to uniform distribution if all probabilities are zero
            normalized_probabilities = [1.0 / len(matching_pixels)] * len(matching_pixels)
        
        # Select fishing spot based on weighted probability
        best_spot = random.choices(matching_pixels, weights=normalized_probabilities, k=1)[0]
        
        # Find the distance of the selected spot for logging
        selected_distance = ((best_spot[0] - center_x) ** 2 + (best_spot[1] - center_y) ** 2) ** 0.5
        
        # Convert window coordinates to screen coordinates
        window_x, window_y = self.window_region[0], self.window_region[1]
        screen_x = window_x + best_spot[0]
        screen_y = window_y + best_spot[1]
        
        print(f"Found {len(matching_pixels)} fishing spots")
        print(f"Selected spot at window ({best_spot[0]}, {best_spot[1]}) - screen ({screen_x}, {screen_y}) - distance: {selected_distance:.1f}px")
        return (screen_x, screen_y)
    
    def is_fishing_spot_active(self) -> bool:
        """
        Check if fishing is still active by polling a line below the screen center.
        
        Returns:
            True if fishing spot color is detected on the polling line, False otherwise
        """
        if not self.fishing_spot_color:
            return False
        
        try:
            rgb_color = jake.color_utils.hex_to_rgb(self.fishing_spot_color)
        except ValueError:
            return False
        
        # Find RuneScape window if not already found
        if self.window_region is None:
            self.window_region = self.find_runescape_window()
            if not self.window_region:
                print("Could not find RuneScape window")
                return False
        
        # Calculate window center coordinates
        window_width = self.window_region[2]
        window_height = self.window_region[3]
        center_x = window_width // 2
        
        # Define polling line: 200 pixels directly below center, 2 pixels wide
        line_length = 200
        line_width = 4
        line_x_start = center_x - line_width // 2  # X coordinate (horizontal position)
        line_y_start = window_height // 2  # Y coordinate (vertical position)
        
        # Take a screenshot of the polling line area within the window
        window_x, window_y = self.window_region[0], self.window_region[1]
        region = (window_x + line_x_start, window_y + line_y_start, line_width, line_length)
        screenshot = jake.screenshot_utils.capture_screen_region(region)
        
        if screenshot is None:
            print("Failed to capture polling line screenshot")
            return False
        
        # Check each pixel in the line for the fishing spot color
        tolerance = 20
        matching_pixels = 0
        
        # Check all pixels in the 2x200 rectangle
        for y in range(line_length):
            for x in range(2):  # 2 pixels wide
                pixel_color = screenshot[y, x]  # Get pixel at (x, y) in the region
                # Convert BGR to RGB
                rgb_pixel = (pixel_color[2], pixel_color[1], pixel_color[0])
                
                # Check if color matches using color_utils
                if jake.color_utils.is_color_in_range(rgb_pixel, rgb_color, tolerance):
                    matching_pixels += 1
        
        # Consider fishing active if we find at least 1 matching pixel
        is_active = matching_pixels > 0
        
        # Take debug screenshot if no matching pixels found
        if matching_pixels == 0:
            print(f"Fishing spot color not detected on polling line")
            print(f"Checked {line_length * 2} pixels, found {matching_pixels} matches")
            self.save_debug_screenshot_with_polling_line(is_active)
        
        return is_active
    
    def save_debug_screenshot_with_polling_line(self, is_active: bool):
        """
        Save a debug screenshot with the polling line highlighted.
        
        Args:
            is_active: Whether fishing spot color was detected on the line
        """
        if not self.debug_enabled:
            return
        
        try:
            # Find RuneScape window if not already found
            if self.window_region is None:
                self.window_region = self.find_runescape_window()
                if not self.window_region:
                    return
            
            # Calculate window center coordinates
            window_width = self.window_region[2]
            window_height = self.window_region[3]
            center_x = window_width // 2
            
            # Define polling line coordinates
            line_length = 200
            line_width = 4
            line_x_start = center_x  # X coordinate
            line_y_start = window_height // 2  # Y coordinate
            
            # Take screenshot of the RuneLite window
            screenshot = jake.screenshot_utils.capture_screen_region(self.window_region)
            if screenshot is None:
                return
            
            # Convert to BGR for OpenCV drawing
            if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
                # Already BGR
                debug_image = screenshot.copy()
            else:
                # Convert from RGB to BGR
                debug_image = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
            
            # Draw polling line box
            # Make the box slightly larger for visibility (5 pixels wide)
            box_width = 5
            box_x1 = line_x_start - line_width // 2
            box_y1 = line_y_start
            box_x2 = line_x_start + line_width // 2
            box_y2 = line_y_start + line_length
            
            # Choose color based on detection status
            if is_active:
                box_color = (0, 255, 0)  # Green - fishing active
                status_text = "ACTIVE"
            else:
                box_color = (0, 0, 255)  # Red - fishing inactive
                status_text = "INACTIVE"
            
            # Draw rectangle around polling line
            cv2.rectangle(debug_image, (box_x1, box_y1), (box_x2, box_y2), box_color, 2)
            
            # Draw center line indicator
            cv2.line(debug_image, (center_x, box_y1), (center_x, box_y2), (255, 255, 0), 1)  # Yellow center line
            
            # Add status text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            text_x = box_x1
            text_y = max(box_y1 - 10, 30)  # Position above box, but not off screen
            
            # Draw text background
            (text_width, text_height), baseline = cv2.getTextSize(status_text, font, font_scale, 2)
            cv2.rectangle(debug_image, 
                          (text_x - 2, text_y - text_height - 2),
                          (text_x + text_width + 2, text_y + baseline + 2),
                          box_color, -1)  # Filled rectangle
            
            # Draw text
            cv2.putText(debug_image, status_text, (text_x, text_y), font, font_scale, (255, 255, 255), 2)
            
            # Add polling line info
            info_text = f"Polling Line: ({line_x_start}, {line_y_start}) to ({line_x_start}, {line_y_start + line_length})"
            info_y = text_y + text_height + 20
            
            # Draw info text background
            (info_width, info_height), baseline = cv2.getTextSize(info_text, font, 0.5, 1)
            cv2.rectangle(debug_image, 
                          (text_x - 2, info_y - info_height - 2),
                          (text_x + info_width + 2, info_y + baseline + 2),
                          (0, 0, 0), -1)  # Black background
            
            # Draw info text
            cv2.putText(debug_image, info_text, (text_x, info_y), font, 0.5, (255, 255, 255), 1)
            
            # Save debug screenshot
            import os
            debug_dir = "debug_screenshots"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filename = f"fishing_polling_line_{status_text.lower()}.png"
            filepath = os.path.join(debug_dir, filename)
            
            cv2.imwrite(filepath, debug_image)
            print(f"Debug screenshot saved: {filepath}")
            
        except Exception as e:
            print(f"Error saving debug screenshot: {e}")
    
    def drop_all_valid_boxes(self) -> bool:
        """
        Drop all valid drop boxes (those whose center is not empty) in random order.
        This cancels fishing, so we need to restart fishing after this.
        
        Returns:
            True if at least one drop action was performed, False otherwise
        """
        if not self.drop_boxes:
            print("No drop boxes configured")
            return False
        
        # Filter drop boxes to only include those whose center is not empty
        valid_boxes = []
        empty_color = "3E3529"
        
        print("Checking drop boxes for valid items...")
        for i, box in enumerate(self.drop_boxes):
            # Calculate center of the box
            center_x = (box["x1"] + box["x2"]) // 2
            center_y = (box["y1"] + box["y2"]) // 2
            
            # Get the color at the center of the box
            try:
                center_color = jake.screenshot_utils.get_pixel_color_at_position(center_x, center_y)
                center_hex = jake.color_utils.rgb_to_hex(center_color)
                
                # Check if the center color is not the empty inventory color
                empty_rgb = jake.color_utils.hex_to_rgb(empty_color)
                if not jake.color_utils.is_color_in_range(center_color, empty_rgb, tolerance=10):
                    valid_boxes.append((i, box))
                    print(f"Drop box {i+1} center ({center_x}, {center_y}) has color #{center_hex} - valid")
                else:
                    print(f"Drop box {i+1} center ({center_x}, {center_y}) has color #{center_hex} - empty, skipping")
                    
            except Exception as e:
                print(f"Error checking drop box {i+1} center color: {e}")
                # If we can't check the color, include the box to be safe
                valid_boxes.append((i, box))
        
        if not valid_boxes:
            print("No valid drop boxes found (all centers are empty)")
            return False
        
        # Shuffle the valid boxes to drop them in random order
        random.shuffle(valid_boxes)
        
        print(f"Dropping {len(valid_boxes)} items in random order...")
        
        # Drop each valid box
        for box_index, box in valid_boxes:
            x1, y1 = box["x1"], box["y1"]
            x2, y2 = box["x2"], box["y2"]
            drop_color = box["color"]
            
            # Generate random coordinates within the bounding box
            random_x = random.randint(x1, x2)
            random_y = random.randint(y1, y2)
            
            print(f"Dropping item from box {box_index+1}: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"Clicking at ({random_x}, {random_y}) with color #{drop_color}")
            
            try:
                if self.human_movement.get("enabled", False):
                    # Use human-like movement
                    mouse_mover = jake.mouse_movement.MouseMovement()
                    mouse_mover.move_mouse_to(random_x, random_y)
                else:
                    # Direct movement
                    pyautogui.moveTo(random_x, random_y)
                
                # Click
                pyautogui.click()
                
                # Small delay between drops to avoid overwhelming the game
                time.sleep(random.uniform(0.1, 0.3))
                
                print(f"Successfully dropped item from box {box_index+1}")
                
            except Exception as e:
                print(f"Error dropping item from box {box_index+1}: {e}")
        
        print(f"Completed dropping {len(valid_boxes)} items")
        return True
    
    def click_fishing_spot(self, spot: Tuple[int, int]) -> bool:
        """
        Click on a fishing spot with human-like movement.
        
        Args:
            spot: Tuple of (x, y) coordinates of the fishing spot
            
        Returns:
            True if click was successful, False otherwise
        """
        print(f"Clicking fishing spot at ({spot[0]}, {spot[1]})")
        
        try:
            if self.human_movement.get("enabled", False):
                # Use human-like movement
                mouse_mover = jake.mouse_movement.MouseMovement()
                mouse_mover.move_mouse_to(spot[0], spot[1])
            else:
                # Direct movement
                pyautogui.moveTo(spot[0], spot[1])
            
            # Click
            pyautogui.click()
            
            self.current_fishing_spot = spot
            self.is_fishing = True
            print("Successfully clicked fishing spot")
            return True
            
        except Exception as e:
            print(f"Error clicking fishing spot: {e}")
            return False
    
    def wait_for_fishing_delay(self):
        """Wait for the configured fishing delay."""
        delay = self.fishing_delay + random.uniform(-0.5, 0.5)  # Add some randomness
        print(f"Waiting {delay:.1f}s for fishing action...")
        time.sleep(delay)
    
    def run_fishing_cycle(self) -> bool:
        """
        Run one complete fishing cycle.
        Every drop_interval seconds, drop all valid boxes and restart fishing.
        Runs forever until interrupted or no fishing spots are available.
        
        Returns:
            True if cycle completed successfully, False if should stop
        """
        print("\n=== Starting Fishing Cycle ===")
        
        # Monitor fishing progress with periodic dropping
        last_drop_time = time.time()
        
        while True:
            current_time = time.time()
            
            # Check if it's time to drop items
            if current_time - last_drop_time >= self.drop_interval:
                print(f"\n=== Drop Interval Reached ({self.drop_interval}s) ===")
                
                # Drop all valid boxes
                if self.drop_all_valid_boxes():
                    print("Items dropped successfully, restarting fishing...")
                    
                    # Wait a moment for drops to complete
                    time.sleep(0.5)
                else:
                    print("No items to drop...")
                
                # Always click on a new fishing spot
                new_fishing_spot = self.find_fishing_spot()
                if new_fishing_spot:
                    if self.click_fishing_spot(new_fishing_spot):
                        print("Successfully restarted fishing")
                        # Wait for fishing action
                        self.wait_for_fishing_delay()
                        # Wait 4 seconds before monitoring again
                        time.sleep(4)
                    else:
                        print("Failed to restart fishing")
                        return False
                else:
                    print("No fishing spots available for restart")
                    return False
                
                last_drop_time = time.time()
            
            # Check if current fishing spot is still active
            if not self.is_fishing_spot_active():
                print("Current fishing spot ran out, finding new spot...")
                
                # Find and click a new fishing spot
                new_fishing_spot = self.find_fishing_spot()
                if new_fishing_spot:
                    if self.click_fishing_spot(new_fishing_spot):
                        print("Successfully found and clicked new fishing spot")
                        # Wait for fishing action
                        self.wait_for_fishing_delay()
                        # Wait 4 seconds before monitoring again
                        time.sleep(4)
                    else:
                        print("Failed to click new fishing spot")
                        return False
                else:
                    print("No fishing spots available")
                    return False
            
            # Wait a bit before checking again
            time.sleep(1)
    
    def run(self, max_cycles: Optional[int] = None):
        """
        Run the fishing bot.
        
        Args:
            max_cycles: Maximum number of fishing cycles to run (None for infinite)
        """
        print("=== Fishing Bot Started ===")
        print("Press Ctrl+C to stop")
        
        cycle_count = 0
        
        try:
            while max_cycles is None or cycle_count < max_cycles:
                cycle_count += 1
                print(f"\n--- Fishing Cycle {cycle_count} ---")
                
                # Find initial fishing spot
                fishing_spot = self.find_fishing_spot()
                if not fishing_spot:
                    print("No fishing spots available")
                    break
                
                # Click on the fishing spot
                if not self.click_fishing_spot(fishing_spot):
                    print("Failed to click fishing spot")
                    break
                
                # Wait for fishing action
                self.wait_for_fishing_delay()
                
                # Wait 4 seconds before starting to poll for fishing spot activity
                print("Waiting 4 seconds before monitoring fishing spot...")
                time.sleep(4)
                
                if not self.run_fishing_cycle():
                    print("Fishing cycle failed, stopping bot")
                    break
                
                # Small delay between cycles
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nFishing bot stopped by user")
        except Exception as e:
            print(f"Error in fishing bot: {e}")
        finally:
            print("Fishing bot finished")

def main():
    """Main function to run the fishing bot."""
    import sys
    
    config_file = "bot_config.json"
    max_cycles = None
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            max_cycles = int(sys.argv[2])
        except ValueError:
            print("Invalid max_cycles argument, using unlimited")
            max_cycles = None
    
    try:
        bot = FishingBot(config_file)
        bot.run(max_cycles)
    except Exception as e:
        print(f"Failed to start fishing bot: {e}")

if __name__ == "__main__":
    main() 