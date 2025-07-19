#!/usr/bin/env python3
"""
Pixel Clicker

This module provides functionality for clicking on pixels with specific colors,
including verification to ensure clicks land on the correct target.
"""

import time
import random
import pyautogui
import jake.screenshot_utils
import jake.color_utils
import jake
from typing import Optional, Tuple

class PixelClicker:
    """Handles clicking on pixels with specific colors, including verification."""
    
    def __init__(self, window_region: Optional[Tuple[int, int, int, int]], use_human_paths: bool = False):
        """
        Initialize the pixel clicker.
        
        Args:
            window_region: Window region (x, y, width, height) for screenshot capture
            use_human_paths: Whether to use human-like mouse movement paths
        """
        self.window_region = window_region
        self.use_human_paths = use_human_paths
        
        # Initialize both mouse movement systems
        self.bezier_mouse = jake.path.BezierMouseMovement()
        
        # Initialize human path finder if requested
        self.human_mouse = None
        if self.use_human_paths:
            try:
                self.human_mouse = jake.path.HumanPath()
                print("Human path finder initialized successfully")
            except Exception as e:
                print(f"Failed to initialize human path finder: {e}")
                self.use_human_paths = False
    
    def move_mouse(self, target_x: int, target_y: int, click_type: str = "none") -> bool:
        """
        Move mouse to target using human-like paths and optionally perform a click
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            click_type: Type of click to perform ("left", "right", "double", "none")
                        Use "none" for movement only without clicking (default)
            
        Returns:
            True if movement (and click if specified) successful, False otherwise
        """
        try:
            if self.use_human_paths and self.human_mouse:
                if click_type == "none":
                    return self.human_mouse.move_mouse(target_x, target_y)
                else:
                    return self.human_mouse.move_mouse_and_click(target_x, target_y, click_type)
            else:
                if click_type == "none":
                    return self.bezier_mouse.move_mouse_to(target_x, target_y)
                else:
                    return self.bezier_mouse.click_at(target_x, target_y, click_type)
                
        except Exception as e:
            print(f"Error in human-like mouse movement: {e}")
            raise e
    
    def click_random_pixel_by_color(self, hex_color: str, tolerance: int = 20, 
                                   verify_click: bool = False, max_attempts: int = 5) -> bool:
        """
        Find pixels with specified color and click on a random one
        
        Args:
            hex_color: Target hex color to find
            tolerance: Color tolerance for matching
            verify_click: Whether to verify the click landed on target color
            max_attempts: Maximum number of attempts if verification is enabled
            
        Returns:
            True if successful, False otherwise
        """
        if not hex_color:
            print("No color specified")
            return False
        
        if verify_click:
            attempts = max_attempts
        else:
            attempts = 1
        
        attempt = 0
        
        while attempt < attempts:
            attempt += 1
            print(f"Attempt {attempt}/{attempts}: Searching for pixels with color #{hex_color}")
            
            # Ensure window region is available
            if self.window_region is None:
                print("No window region available")
                return False
            
            screenshot = jake.screenshot_utils.capture_screen_region(self.window_region)

            # Search for pixels with the target color
            matching_pixels = jake.color_utils.find_pixels_by_color(
                screenshot, hex_color, tolerance
            )
            
            if not matching_pixels:
                print(f"No pixels found with color #{hex_color}")
                if verify_click and attempt < attempts:
                    print("Waiting 1 second before retry...")
                    time.sleep(1)
                    continue
                return False
            
            # Select a random pixel
            selected_pixel = random.choice(matching_pixels)
            
            # Convert window coordinates to screen coordinates
            window_x, window_y = self.window_region[0], self.window_region[1]
            screen_x = window_x + selected_pixel[0]
            screen_y = window_y + selected_pixel[1]
            
            print(f"Found {len(matching_pixels)} pixels with color #{hex_color}")
            print(f"Selected pixel at window ({selected_pixel[0]}, {selected_pixel[1]}) - screen ({screen_x}, {screen_y})")
            
            # Move mouse to target using human-like movement (without clicking)
            if not self.move_mouse(screen_x, screen_y):
                print("Failed to move mouse to selected pixel")
                if verify_click and attempt < attempts:
                    print("Waiting 1 second before retry...")
                    time.sleep(1)
                    continue
                return False
            
            # Verify the color under the cursor before clicking
            cursor_x, cursor_y = pyautogui.position()
            cursor_color = jake.screenshot_utils.get_pixel_color_at_position(cursor_x, cursor_y)
            target_rgb = jake.color_utils.hex_to_rgb(hex_color)
            
            # Calculate color difference
            color_diff = sum(abs(int(cursor_color[i]) - target_rgb[i]) for i in range(3))
            
            if color_diff <= tolerance:
                print(f"Color under cursor matches target! Clicking now...")
                pyautogui.click()
                return True
            else:
                print(f"Color under cursor doesn't match target! Expected color RGB {target_rgb}, got RGB{tuple(cursor_color[:3])}")
                if attempt < attempts:
                    print("Target may have moved. Retrying...")
                    time.sleep(.25)
                    continue
                else:
                    print("Max attempts reached. Color verification failed.")
                    return False
        
        return False

    def click_random_in_box(self, box_coords: list, click_type: str = "left") -> bool:
        """
        Click on a random position within a specified box
        
        Args:
            box_coords: List of [x1, y1, x2, y2] coordinates
            click_type: Type of click to perform ("left", "right", "double")
            
        Returns:
            True if successful, False otherwise
        """
        if not box_coords or len(box_coords) != 4:
            print("Invalid box coordinates")
            return False
        
        x1, y1, x2, y2 = box_coords
        
        # Generate random position within the box
        random_x = random.randint(x1, x2)
        random_y = random.randint(y1, y2)
        
        print(f"Clicking random position in box ({x1}, {y1}, {x2}, {y2}) at ({random_x}, {random_y})")
        return self.move_mouse(random_x, random_y, click_type)