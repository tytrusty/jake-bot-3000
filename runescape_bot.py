import cv2
import numpy as np
import pyautogui
import pydirectinput
import time
import keyboard
import threading
import random
import os
from typing import Tuple, Optional, List
from mouse_movement import MouseMovement
import screenshot_utils
import color_utils
import pixel_selection
from scipy.ndimage import label, binary_dilation

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class RuneScapeBot:
    def __init__(self):
        self.running = False
        self.window_title = "RuneLite"
        self.window_region: Optional[Tuple[int, int, int, int]] = None
        self.templates_dir = "templates"
        self.in_combat = False  # Combat status flag
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # Initialize PyDirectInput for better game compatibility
        pydirectinput.FAILSAFE = False
        
        # Initialize mouse movement controller with speed range for more human-like variability
        self.mouse = MouseMovement(speed_factor=(2.0, 5.0), jitter_factor=0.3)
        
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
    

    
    def click_on_element(self, element_coords: Tuple[int, int, int, int], 
                        region: Tuple[int, int, int, int], 
                        click_type: str = "left") -> bool:
        """
        Click on an element within the game window using natural mouse movement
        """
        try:
            # Calculate absolute screen coordinates
            region_x, region_y = region[0], region[1]
            element_x, element_y = element_coords[0], element_coords[1]
            
            # Center of the element
            center_x = region_x + element_x + element_coords[2] // 2
            center_y = region_y + element_y + element_coords[3] // 2
            
            # Use natural mouse movement for more human-like behavior
            if click_type == "left":
                return self.mouse.click_at(center_x, center_y, "left")
            elif click_type == "right":
                return self.mouse.click_at(center_x, center_y, "right")
            elif click_type == "double":
                return self.mouse.double_click_at(center_x, center_y)
            else:
                print(f"Unknown click type: {click_type}")
                return False
            
        except Exception as e:
            print(f"Error clicking: {e}")
            return False
    
    def click_random_pixel_by_color(self, hex_color: str, tolerance: int = 10, method: str = "smart") -> bool:
        """
        Find pixels with specified color and click on a random one
        
        Args:
            hex_color: Target hex color to find
            tolerance: Color tolerance for matching
            method: "random" for original method, "smart" for blob-based selection
        """
        # Find RuneScape window if not already found
        if self.window_region is None:
            self.window_region = self.find_runescape_window()
            if not self.window_region:
                print("Could not find RuneScape window")
                return False
        
        # Capture screenshot of the RuneScape window
        screenshot = screenshot_utils.capture_screen_region(self.window_region)
        
        # Use the new pixel selection logic with downsampling for high-resolution screens
        downsample_factor = 4  # Can be made configurable
        if method == "smart":
            selected_pixel = pixel_selection.smart_pixel_select(screenshot, hex_color, tolerance, return_debug=False, downsample_factor=downsample_factor)
        else:
            selected_pixel = pixel_selection.random_pixel_select(screenshot, hex_color, tolerance)
        
        if selected_pixel is None:
            print(f"No pixels found with color {hex_color} using method '{method}'")
            return False
        
        pixel_x, pixel_y = selected_pixel
        
        # Convert to absolute screen coordinates (RuneScape window)
        window_x, window_y = self.window_region[0], self.window_region[1]
        screen_x = window_x + pixel_x
        screen_y = window_y + pixel_y
        
        # Click on the pixel
        try:
            self.mouse.click_at(screen_x, screen_y, "left")
            print(f"Clicked on pixel ({pixel_x}, {pixel_y}) with color {hex_color} at screen position ({screen_x}, {screen_y}) using method '{method}'")
            return True
        except Exception as e:
            print(f"Error clicking on pixel: {e}")
            return False
    
    def attack_sequence(self, target_hex_color: str = "00FFFFFA", 
                       health_x: Optional[int] = None,
                       health_y: Optional[int] = None,
                       wait_time: float = 4.0,
                       food_area: Optional[Tuple[int, int, int, int]] = None,
                       red_threshold: int = 5,
                       pixel_method: str = "smart"):
        """
        Complete attack sequence: find target, click, check combat by color, and auto-eat
        """
        print(f"Starting attack sequence for color: {target_hex_color}")
        
        # Load health bar position if not provided
        if health_x is None or health_y is None:
            health_pos = self.load_health_bar_position()
            if health_pos is None:
                print("No health bar position found. Please run the health bar position finder first.")
                return False
            health_x, health_y = health_pos
        
        # Load food area if not provided
        if food_area is None:
            food_area = self.load_food_area()
            if food_area is None:
                print("No food area configured. Auto-eating will be disabled.")
                print("Run option 8 to set up food area for auto-eating.")
        
        # Step 0: Check if already in combat (mob auto-attacked after previous death)
        print("Step 0: Checking if already in combat...")
        combat_detected = self.check_combat_status_by_color(health_x, health_y, mode="combat", tolerance=30)
        
        if combat_detected:
            print("Already in combat! Skipping target selection and monitoring for mob death...")
            # Skip to combat monitoring phase
            return self.monitor_combat_and_health(health_x, health_y, food_area, red_threshold)
        
        # Step 1: Find and click on target pixel
        print("Step 1: Finding and clicking on target...")
        if not self.click_random_pixel_by_color(target_hex_color, method=pixel_method):
            print("Failed to find or click on target")
            return False
        
        # Step 2: Wait 2 seconds, then check if combat is present by color (#048834)
        print(f"Step 2: Waiting {wait_time} seconds, then checking combat status...")
        time.sleep(wait_time)
        
        # Check for combat color (#048834 - green)
        combat_detected = self.check_combat_status_by_color(health_x, health_y, mode="combat", tolerance=30)
        
        if not combat_detected:
            print("Combat not detected, waiting 0.5 seconds and retrying...")
            time.sleep(0.5)
            return False  # Signal to retry
        else:
            print("Combat detected! Now monitoring for mob death and health...")
            return self.monitor_combat_and_health(health_x, health_y, food_area, red_threshold)
    
    def monitor_combat_and_health(self, health_x: int, health_y: int, 
                                 food_area: Optional[Tuple[int, int, int, int]], 
                                 red_threshold: int) -> bool:
        """
        Monitor combat status and health during combat
        
        Args:
            health_x: X coordinate of health bar pixel
            health_y: Y coordinate of health bar pixel
            food_area: Food area coordinates for auto-eating
            red_threshold: Threshold for health monitoring
            
        Returns:
            True if mob died and waiting completed, False otherwise
        """
        print("Step 3: Polling for mob death (red color #601211) and monitoring health...")
        
        # Get screen dimensions for health sampling
        screen_width = pyautogui.size().width
        screen_height = pyautogui.size().height
        middle_left_x = screen_width // 4  # 25% from left
        middle_left_y = screen_height // 2  # middle height
        
        while True:
            # Check for mob death first
            death_detected = self.check_combat_status_by_color(health_x, health_y, mode="death", tolerance=30)
            
            if death_detected:
                print("Mob is dead! Waiting random time (up to 5 minutes, avg 3 seconds)...")
                # Use exponential distribution for skewed timing: most waits are short, some are longer
                # This gives us an average of 3 seconds but can go up to 5 minutes
                wait_time = min(random.expovariate(1/2), 300)  # 1/2 = 2 second average, max 300 seconds (5 minutes)
                print(f"Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                return True  # Signal to find next target
            
            # Check health if food area is configured
            if food_area is not None:
                # Sample both points for red color
                left_color = screenshot_utils.get_pixel_color_at_position(middle_left_x, middle_left_y)
                
                # Define pure red color (255, 0, 0)
                pure_red = (255, 0, 0)
                
                # Calculate color distance to pure red for both points
                left_distance = color_utils.calculate_color_distance(left_color, pure_red)
                
                # Check if BOTH points are close to pure red (small distance = closer to red)
                if left_distance <= red_threshold:
                    print(f"Low health detected! Both points are close to red:")
                    print(f"Left pixel: RGB{left_color} (distance to red: {left_distance:.1f})")
                    
                    # Click randomly in food area
                    x1, y1, x2, y2 = food_area
                    random_x = random.randint(x1, x2)
                    random_y = random.randint(y1, y2)
                    
                    print(f"Eating food at ({random_x}, {random_y})")
                    
                    try:
                        self.mouse.click_at(random_x, random_y, "left")
                        print("Food eaten! Continuing combat...")
                        
                        # Wait a moment for the food to be consumed
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"Error eating food: {e}")
            
            # Wait 0.25 seconds before next check
            time.sleep(0.25)
    
    def check_combat_status_by_color(self, x: int, y: int, 
                                   mode: str = "combat",  # "combat" or "death"
                                   tolerance: int = 30) -> bool:
        """
        Check combat status by monitoring a specific pixel for health bar colors
        mode: "combat" checks for green (#048834), "death" checks for red (#601211)
        Returns: True if the specified color is detected, False otherwise
        """
        try:
            # Get the color at the specified position
            pixel_color = screenshot_utils.get_pixel_color_at_position(x, y)
            pixel_hex = color_utils.rgb_to_hex(pixel_color)
            
            # print(f"Health bar pixel ({x}, {y}) color: RGB{pixel_color} = #{pixel_hex}")
            
            if mode == "combat":
                # Check for green combat color (#048834)
                target_color = "048834"
                if color_utils.colors_match(pixel_hex, target_color, tolerance):
                    self.in_combat = True
                    print(f"Combat detected (green #{target_color})")
                    return True
                else:
                    self.in_combat = False
                    print(f"No combat detected (expected green #{target_color})")
                    return False
                    
            elif mode == "death":
                # Check for red death color (#601211)
                target_color = "601211"
                if color_utils.colors_match(pixel_hex, target_color, tolerance):
                    self.in_combat = False
                    print(f"Death detected (red #{target_color})")
                    return True
                else:
                    # print(f"No death detected (expected red #{target_color})")
                    return False
                    
            else:
                print(f"Invalid mode: {mode}. Use 'combat' or 'death'")
                return False
                
        except Exception as e:
            print(f"Error checking combat status by color: {e}")
            return False

    def find_health_bar_position(self) -> Optional[Tuple[int, int]]:
        """
        Interactive tool to find the health bar position
        """
        print("\n=== Health Bar Position Finder ===")
        print("1. Attack a mob to make their health bar appear")
        print("2. Move your mouse to the green health bar pixel (#048834)")
        print("3. You have 3 seconds to position your mouse...")
        
        for i in range(3, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print()
        
        # Get mouse position
        mouse_x, mouse_y = pyautogui.position()
        rgb_color = screenshot_utils.get_pixel_color_at_position(mouse_x, mouse_y)
        hex_color = color_utils.rgb_to_hex(rgb_color)
        
        print(f"\nHealth bar position: ({mouse_x}, {mouse_y})")
        print(f"Color: RGB{rgb_color} = #{hex_color}")
        
        # Save this position for future use
        save_choice = input("Save this position? (y/n): ").strip().lower()
        if save_choice == 'y':
            # Save to a simple config file
            config_path = "health_bar_config.txt"
            with open(config_path, 'w') as f:
                f.write(f"{mouse_x},{mouse_y},{hex_color}")
            print(f"Position saved to {config_path}")
        
        return (mouse_x, mouse_y)
    
    def load_health_bar_position(self) -> Optional[Tuple[int, int]]:
        """
        Load saved health bar position from config file
        """
        config_path = "health_bar_config.txt"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    line = f.read().strip()
                    x, y, color = line.split(',')
                    print(f"Loaded health bar position: ({x}, {y}) with color #{color}")
                    return (int(x), int(y))
            except Exception as e:
                print(f"Error loading health bar position: {e}")
        return None

    def setup_food_area(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Interactive setup for food area coordinates
        """
        print("\n=== Food Area Setup ===")
        print("You need to specify the food area as a rectangle.")
        print("This should be the area where your food is located in your inventory.")
        
        try:
            print("\nStep 1: Move mouse to bottom-left corner of food area")
            print("You have 5 seconds to position your mouse...")
            for i in range(5, 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
            print()
            
            x1, y1 = pyautogui.position()
            print(f"Bottom-left corner: ({x1}, {y1})")
            
            print("\nStep 2: Move mouse to top-right corner of food area")
            print("You have 5 seconds to position your mouse...")
            for i in range(5, 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
            print()
            
            x2, y2 = pyautogui.position()
            print(f"Top-right corner: ({x2}, {y2})")
            
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            food_area = (x1, y1, x2, y2)
            print(f"\nFood area: {food_area}")
            
            # Save to config
            save_choice = input("Save this food area? (y/n): ").strip().lower()
            if save_choice == 'y':
                config_path = "food_area_config.txt"
                with open(config_path, 'w') as f:
                    f.write(f"{x1},{y1},{x2},{y2}")
                print(f"Food area saved to {config_path}")
            
            return food_area
            
        except Exception as e:
            print(f"Error setting up food area: {e}")
            return None

    def load_food_area(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Load saved food area from config file
        """
        config_path = "food_area_config.txt"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    line = f.read().strip()
                    x1, y1, x2, y2 = map(int, line.split(','))
                    print(f"Loaded food area: ({x1}, {y1}, {x2}, {y2})")
                    return (x1, y1, x2, y2)
            except Exception as e:
                print(f"Error loading food area: {e}")
        return None

def main():
    bot = RuneScapeBot()
    
    print("RuneScape Bot")
    print("1. Attack Bot (Find pixels by color)")
    print("2. Debug Screenshot")
    print("3. Find Health Bar Position")
    print("4. Find Food Area")
    print("5. Exit")
    
    while True:
        choice = input("Choose an option (1-9): ").strip()
        
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
                    print("Continuing without auto-eating. You can set up food area later with option 8.")
            
            # Get red threshold for health monitoring
            red_threshold_str = input("Enter red threshold for health monitoring (default 5): ").strip()
            if not red_threshold_str:
                red_threshold = 5
            else:
                red_threshold = int(red_threshold_str)
            
            # Run attack sequence
            print(f"\nStarting attack bot with color: {target_color}")
            print(f"Using pixel selection method: {pixel_method}")
            if food_area:
                print(f"Auto-eating enabled with food area: {food_area}")
                print(f"Health monitoring threshold: {red_threshold}")
            else:
                print("Auto-eating disabled - no food area configured")
            print("Press 'q' to stop the attack sequence")
            
            bot.running = True
            while bot.running:
                if keyboard.is_pressed('q'):
                    print("Stopping attack bot...")
                    bot.running = False
                    break
                
                # Run one attack sequence with food eating
                success = bot.attack_sequence(target_color, food_area=food_area, red_threshold=red_threshold, pixel_method=pixel_method)
                
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
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 