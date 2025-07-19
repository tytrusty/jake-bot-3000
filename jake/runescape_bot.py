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
import math
from sklearn.cluster import DBSCAN
from path.human_path_finder import HumanPath
from config_manager import ConfigurationManager

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class RuneScapeBot:
    def __init__(self, config_manager: ConfigurationManager, use_human_paths: bool = False):
        self.running = False
        self.window_title = "RuneLite"
        self.window_region: Optional[Tuple[int, int, int, int]] = None
        self.in_combat = False  # Combat status flag
        self.use_human_paths = use_human_paths
        self.config_manager = config_manager
        
        # Initialize PyDirectInput for better game compatibility
        pydirectinput.FAILSAFE = False
        
        # Initialize mouse movement controller with speed range for more human-like variability
        self.mouse = MouseMovement(speed_factor=(2.0, 5.0), jitter_factor=0.3)
        
        # Initialize human path finder if requested and available
        self.human_path = None
        if self.use_human_paths:
            try:
                self.human_path = HumanPath()
                print("Human path finder initialized successfully")
            except Exception as e:
                print(f"Failed to initialize human path finder: {e}")
                self.use_human_paths = False
    
    def move_mouse_randomly(self, distance: int = 50, visualize: bool = False) -> bool:
        """
        Move mouse to a random position using human-like movement if available
        
        Args:
            distance: Distance in pixels to move from current position
            visualize: Whether to visualize the path (default: False for random movements)
            
        Returns:
            True if movement was successful, False otherwise
        """
        try:
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate random position at specified distance
            angle = random.uniform(0, 2 * np.pi)  # Random angle
            new_x = int(current_x + distance * np.cos(angle))
            new_y = int(current_y + distance * np.sin(angle))
            
            # Ensure the new position is within screen bounds
            screen_width = pyautogui.size().width
            screen_height = pyautogui.size().height
            new_x = max(0, min(new_x, screen_width - 1))
            new_y = max(0, min(new_y, screen_height - 1))
            
            print(f"Random mouse movement: ({current_x}, {current_y}) -> ({new_x}, {new_y})")
            
            # Use human-like movement if available, otherwise fall back to standard movement
            if self.use_human_paths and self.human_path:
                # Use human path finder for random movement
                current_pos = (current_x, current_y)
                target_pos = (new_x, new_y)
                
                # Use human path finder for random movement
                success = self.human_path.move_mouse(new_x, new_y)
                if success:
                    return True
                else:
                    # Fallback to standard movement if path generation fails
                    pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.1, 0.3))
                    return True
            else:
                # Use standard mouse movement
                pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.1, 0.3))
                return True
                
        except Exception as e:
            print(f"Error during random mouse movement: {e}")
            return False
    
    def move_mouse_human_like(self, target_x: int, target_y: int, click_type: str = "left") -> bool:
        """
        Move mouse to target using human-like paths and perform a click
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            click_type: Type of click to perform ("left", "right", "double")
            
        Returns:
            True if movement and click successful, False otherwise
        """
        try:
            if self.use_human_paths and self.human_path:
                # Use human path finder for movement and clicking
                return self.human_path.move_mouse_and_click(target_x, target_y, click_type)
            else:
                # Use standard mouse movement
                return self.mouse.click_at(target_x, target_y, click_type)
                
        except Exception as e:
            print(f"Error in human-like mouse movement: {e}")
            # Fallback to standard movement
            return self.mouse.click_at(target_x, target_y, click_type)
        
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
            
            # Use human-like mouse movement if available, otherwise use standard movement
            return self.move_mouse_human_like(center_x, center_y, click_type)
            
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
            success = self.move_mouse_human_like(screen_x, screen_y, "left")
            if success:
                print(f"Clicked on pixel ({pixel_x}, {pixel_y}) with color {hex_color} at screen position ({screen_x}, {screen_y}) using method '{method}'")
            return success
        except Exception as e:
            print(f"Error clicking on pixel: {e}")
            return False
    
    def pickup_loot(self, loot_color: str = "FFAA00FF", tolerance: int = 10, max_distance: int = 500, 
                   save_debug: bool = True, bury: bool = False, inventory_area: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Find and right-click on loot items after mob death
        
        Args:
            loot_color: Hex color of loot text (default: #FFAA00FF)
            tolerance: Color tolerance for matching
            max_distance: Maximum distance from screen center to search (in pixels)
            save_debug: Whether to save debug screenshots
            bury: Whether to click in inventory area after pickup
            inventory_area: Bounding box coordinates for inventory area (x1, y1, x2, y2)
            
        Returns:
            True if loot was found and clicked, False otherwise
        """
        try:
            # Find RuneScape window if not already found
            if self.window_region is None:
                self.window_region = self.find_runescape_window()
                if not self.window_region:
                    print("Could not find RuneScape window")
                    return False
            
            # Capture screenshot of the RuneScape window
            screenshot = screenshot_utils.capture_screen_region(self.window_region)
            
            # Calculate screen center relative to the window
            window_width = self.window_region[2]
            window_height = self.window_region[3]
            center_x = window_width // 2
            center_y = window_height // 2
            
            print(f"Searching for loot with color #{loot_color} within {max_distance} pixels of center ({center_x}, {center_y})")
            
            # Find all pixels with the loot color
            loot_pixels = color_utils.find_pixels_by_color(screenshot, loot_color, tolerance)
            
            if not loot_pixels:
                print(f"No loot pixels found with color #{loot_color}")
                if save_debug:
                    # Save debug screenshot showing no loot found
                    debug_filename = f"debug_screenshots/loot_debug_no_pixels_{loot_color}.png"
                    cv2.imwrite(debug_filename, screenshot)
                    print(f"Debug screenshot saved: {debug_filename}")
                return False
            
            print(f"Found {len(loot_pixels)} loot pixels, filtering by distance...")
            
            # Filter pixels by distance from center using np.where
            if loot_pixels:
                # Convert to numpy arrays for vectorized operations
                pixel_coords = np.array(loot_pixels)
                x_coords = pixel_coords[:, 0]
                y_coords = pixel_coords[:, 1]
                
                # Calculate distances from center (vectorized)
                distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
                
                # Use np.where to find valid indices
                valid_indices = np.where(distances <= max_distance)[0]
                valid_loot_pixels = [tuple(loot_pixels[i]) for i in valid_indices]
            else:
                valid_loot_pixels = []
            
            if not valid_loot_pixels:
                print(f"No loot pixels found within {max_distance} pixels of center")
                if save_debug:
                    # Save debug screenshot showing all loot pixels (outside range)
                    debug_screenshot = screenshot.copy()
                    
                    # Draw all loot pixels in red
                    for x, y in loot_pixels:
                        cv2.circle(debug_screenshot, (x, y), 2, (0, 0, 255), -1)  # Red dots
                    
                    # Draw center and range circle
                    cv2.circle(debug_screenshot, (center_x, center_y), 5, (255, 255, 255), -1)  # White center
                    cv2.circle(debug_screenshot, (center_x, center_y), max_distance, (0, 255, 0), 2)  # Green range circle
                    
                    debug_filename = f"debug_screenshots/loot_debug_outside_range_{loot_color}.png"
                    cv2.imwrite(debug_filename, debug_screenshot)
                    print(f"Debug screenshot saved: {debug_filename}")
                return False
            
            print(f"Found {len(valid_loot_pixels)} valid loot pixels within range")
            
            # Select the Euclidean mean (centroid) of valid loot pixels using DBSCAN clustering
            if len(valid_loot_pixels) > 0:
                # Convert to numpy array for DBSCAN
                pixel_coords = np.array(valid_loot_pixels)
                
                # Apply DBSCAN clustering
                dbscan = DBSCAN(eps=20, min_samples=3)
                cluster_labels = dbscan.fit_predict(pixel_coords)
                
                # Get unique cluster labels (excluding noise points with label -1)
                unique_clusters = set(cluster_labels)
                if -1 in unique_clusters:
                    unique_clusters.remove(-1)  # Remove noise points
                
                if len(unique_clusters) == 0:
                    print("No valid clusters found, using all pixels")
                    # Fallback to original centroid method
                    centroid_x = int(np.mean(pixel_coords[:, 0]))
                    centroid_y = int(np.mean(pixel_coords[:, 1]))
                    selected_pixel = (centroid_x, centroid_y)
                    pixel_x, pixel_y = selected_pixel
                    print(f"Selected fallback centroid at ({centroid_x}, {centroid_y}) from {len(valid_loot_pixels)} valid pixels")
                else:
                    # Find cluster closest to screen center
                    min_distance = float('inf')
                    best_cluster = None
                    best_centroid = None
                    
                    for cluster_id in unique_clusters:
                        # Get pixels in this cluster
                        cluster_mask = cluster_labels == cluster_id
                        cluster_pixels = pixel_coords[cluster_mask]
                        
                        # Calculate cluster centroid
                        cluster_centroid_x = int(np.mean(cluster_pixels[:, 0]))
                        cluster_centroid_y = int(np.mean(cluster_pixels[:, 1]))
                        
                        # Calculate distance to screen center
                        distance_to_center = np.sqrt((cluster_centroid_x - center_x)**2 + (cluster_centroid_y - center_y)**2)
                        
                        if distance_to_center < min_distance:
                            min_distance = distance_to_center
                            best_cluster = cluster_id
                            best_centroid = (cluster_centroid_x, cluster_centroid_y)
                    
                    selected_pixel = best_centroid
                    pixel_x, pixel_y = selected_pixel
                    print(f"Selected cluster {best_cluster} centroid at ({pixel_x}, {pixel_y}) from {len(valid_loot_pixels)} valid pixels (distance to center: {min_distance:.1f})")
                    
                    # Draw cluster circles in debug mode
                    if save_debug:
                        debug_screenshot = screenshot.copy()
                        
                        # Draw all loot pixels in blue
                        for x, y in loot_pixels:
                            cv2.circle(debug_screenshot, (x, y), 1, (255, 0, 0), -1)  # Blue dots for all loot
                        
                        # Draw valid loot pixels in green
                        for x, y in valid_loot_pixels:
                            cv2.circle(debug_screenshot, (x, y), 3, (0, 255, 0), -1)  # Green dots for valid loot
                        
                        # Draw cluster circles
                        for cluster_id in unique_clusters:
                            cluster_mask = cluster_labels == cluster_id
                            cluster_pixels = pixel_coords[cluster_mask]
                            
                            # Calculate cluster centroid and radius
                            cluster_centroid_x = int(np.mean(cluster_pixels[:, 0]))
                            cluster_centroid_y = int(np.mean(cluster_pixels[:, 1]))
                            
                            # Calculate radius as max distance from centroid to any point in cluster
                            distances = np.sqrt((cluster_pixels[:, 0] - cluster_centroid_x)**2 + (cluster_pixels[:, 1] - cluster_centroid_y)**2)
                            radius = int(np.max(distances)) + 5  # Add some padding
                            
                            # Draw circle around cluster
                            color = (0, 255, 255) if cluster_id == best_cluster else (128, 128, 128)  # Yellow for best, gray for others
                            cv2.circle(debug_screenshot, (cluster_centroid_x, cluster_centroid_y), radius, color, 2)
                            
                            # Add cluster label
                            cv2.putText(debug_screenshot, f"C{cluster_id}", (cluster_centroid_x + radius + 5, cluster_centroid_y), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
                        # Draw selected pixel in red
                        cv2.circle(debug_screenshot, (pixel_x, pixel_y), 5, (0, 0, 255), -1)  # Red dot for selected
                        
                        # Draw center and range circle
                        cv2.circle(debug_screenshot, (center_x, center_y), 5, (255, 255, 255), -1)  # White center
                        cv2.circle(debug_screenshot, (center_x, center_y), max_distance, (0, 255, 0), 2)  # Green range circle
                        
                        debug_filename = f"debug_screenshots/loot_debug_success_{loot_color}.png"
                        cv2.imwrite(debug_filename, debug_screenshot)
                        print(f"Debug screenshot saved: {debug_filename}")
            else:
                print("No valid loot pixels found")
                return False
            
            # Convert to absolute screen coordinates
            window_x, window_y = self.window_region[0], self.window_region[1]
            screen_x = window_x + pixel_x
            screen_y = window_y + pixel_y
            
            # Add offset to right-click position (move down a bit because the loot is below the text)
            right_click_offset = 10  # 10 pixels down
            screen_y += right_click_offset
            
            # Right-click on the loot with offset
            print(f"Right-clicking on loot at pixel ({pixel_x}, {pixel_y}) -> screen ({screen_x}, {screen_y}) (with {right_click_offset}px offset)")
            
            try:
                success = self.move_mouse_human_like(screen_x, screen_y, "right")
                if not success:
                    print("Failed to right-click on loot")
                    return False
                print("Successfully right-clicked on loot!")
                
                # Wait for the right-click menu to appear
                wait_time = random.uniform(0.25, 0.55)
                print(f"Waiting {wait_time:.2f} seconds for menu to appear...")
                time.sleep(wait_time)
                
                # Define the menu box area (centered below the cursor)
                menu_width = 200
                menu_height = 200
                menu_start_x = screen_x - menu_width // 2  # Center horizontally
                menu_start_y = screen_y + 10  # 10 pixels below cursor
                menu_end_x = screen_x + menu_width // 2
                menu_end_y = screen_y + 10 + menu_height
                
                print(f"Searching for loot color in menu box: ({menu_start_x}, {menu_start_y}) to ({menu_end_x}, {menu_end_y})")
                
                # Capture screenshot of the menu area
                menu_region = (menu_start_x, menu_start_y, menu_width, menu_height)
                menu_screenshot = screenshot_utils.capture_screen_region(menu_region)
                
                # Find loot color pixels in the menu area
                menu_loot_pixels = color_utils.find_pixels_by_color(menu_screenshot, loot_color, tolerance)
                
                if not menu_loot_pixels:
                    print("No loot color found in menu box")
                    if save_debug:
                        debug_filename = f"debug_screenshots/loot_menu_no_pixels_{loot_color}.png"
                        cv2.imwrite(debug_filename, menu_screenshot)
                        print(f"Menu debug screenshot saved: {debug_filename}")
                    return False
                
                print(f"Found {len(menu_loot_pixels)} loot pixels in menu")
                
                # Select the Euclidean mean (centroid) of menu loot pixels using DBSCAN clustering
                if len(menu_loot_pixels) > 0:
                    # Convert to numpy array for DBSCAN
                    menu_pixel_coords = np.array(menu_loot_pixels)
                    
                    # Apply DBSCAN clustering
                    dbscan = DBSCAN(eps=20, min_samples=3)
                    cluster_labels = dbscan.fit_predict(menu_pixel_coords)
                    
                    # Get unique cluster labels (excluding noise points with label -1)
                    unique_clusters = set(cluster_labels)
                    if -1 in unique_clusters:
                        unique_clusters.remove(-1)  # Remove noise points
                    
                    if len(unique_clusters) == 0:
                        print("No valid menu clusters found, using random pixel")
                        # Fallback to random selection
                        selected_menu_pixel = random.choice(menu_loot_pixels)
                        menu_pixel_x, menu_pixel_y = selected_menu_pixel
                        print(f"Selected random menu pixel at ({menu_pixel_x}, {menu_pixel_y}) from {len(menu_loot_pixels)} menu pixels")
                    else:
                        # Select a random cluster
                        random_cluster_id = random.choice(list(unique_clusters))
                        
                        # Get pixels in the selected cluster
                        cluster_mask = cluster_labels == random_cluster_id
                        cluster_pixels = menu_pixel_coords[cluster_mask]
                        
                        # Select a random pixel from the cluster
                        random_index = random.randint(0, len(cluster_pixels) - 1)
                        selected_menu_pixel = tuple(cluster_pixels[random_index])
                        menu_pixel_x, menu_pixel_y = selected_menu_pixel
                        print(f"Selected random pixel from cluster {random_cluster_id} at ({menu_pixel_x}, {menu_pixel_y}) from {len(cluster_pixels)} cluster pixels")
                        
                        # Draw cluster circles in debug mode
                        if save_debug:
                            debug_screenshot = menu_screenshot.copy()
                            
                            # Draw all menu loot pixels in blue
                            for x, y in menu_loot_pixels:
                                cv2.circle(debug_screenshot, (x, y), 2, (255, 0, 0), -1)  # Blue dots
                            
                            # Draw cluster circles
                            for cluster_id in unique_clusters:
                                cluster_mask = cluster_labels == cluster_id
                                cluster_pixels_debug = menu_pixel_coords[cluster_mask]
                                
                                # Calculate cluster centroid and radius
                                cluster_centroid_x = int(np.mean(cluster_pixels_debug[:, 0]))
                                cluster_centroid_y = int(np.mean(cluster_pixels_debug[:, 1]))
                                
                                # Calculate radius as max distance from centroid to any point in cluster
                                distances = np.sqrt((cluster_pixels_debug[:, 0] - cluster_centroid_x)**2 + (cluster_pixels_debug[:, 1] - cluster_centroid_y)**2)
                                radius = int(np.max(distances)) + 5  # Add some padding
                                
                                # Draw circle around cluster
                                color = (0, 255, 255) if cluster_id == random_cluster_id else (128, 128, 128)  # Yellow for selected, gray for others
                                cv2.circle(debug_screenshot, (cluster_centroid_x, cluster_centroid_y), radius, color, 2)
                                
                                # Add cluster label
                                cv2.putText(debug_screenshot, f"C{cluster_id}", (cluster_centroid_x + radius + 5, cluster_centroid_y), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                            
                            # Draw selected menu pixel in red
                            cv2.circle(debug_screenshot, (menu_pixel_x, menu_pixel_y), 4, (0, 0, 255), -1)  # Red dot
                            
                            debug_filename = f"debug_screenshots/loot_menu_success_{loot_color}.png"
                            cv2.imwrite(debug_filename, debug_screenshot)
                            print(f"Menu debug screenshot saved: {debug_filename}")
                else:
                    print("No loot pixels found in menu")
                    return False
                
                # Convert to absolute screen coordinates
                absolute_menu_x = menu_start_x + menu_pixel_x
                absolute_menu_y = menu_start_y + menu_pixel_y
                
                print(f"Left-clicking on menu option at ({menu_pixel_x}, {menu_pixel_y}) -> screen ({absolute_menu_x}, {absolute_menu_y})")
                
                # Left-click on the menu option
                success = self.move_mouse_human_like(absolute_menu_x, absolute_menu_y, "left")
                if not success:
                    print("Failed to click on menu option")
                    return False
                print("Successfully clicked on menu option!")
                
                if save_debug:
                    # Save debug screenshot of menu area
                    debug_screenshot = menu_screenshot.copy()
                    
                    # Draw all menu loot pixels in blue
                    for x, y in menu_loot_pixels:
                        cv2.circle(debug_screenshot, (x, y), 2, (255, 0, 0), -1)  # Blue dots
                    
                    # Draw selected menu pixel in red
                    cv2.circle(debug_screenshot, (menu_pixel_x, menu_pixel_y), 4, (0, 0, 255), -1)  # Red dot
                    
                    debug_filename = f"debug_screenshots/loot_menu_success_{loot_color}.png"
                    cv2.imwrite(debug_filename, debug_screenshot)
                    print(f"Menu debug screenshot saved: {debug_filename}")
                
                # Check if burying is enabled and inventory area is configured
                if bury and inventory_area is not None:
                    print("Burying enabled, clicking in inventory area...")
                    
                    # Wait a moment for the item to appear in inventory
                    time.sleep(random.uniform(0.9, 1.8))
                    
                    # Get inventory area coordinates
                    inv_x1, inv_y1, inv_x2, inv_y2 = inventory_area
                    
                    # Select a random pixel within the inventory area
                    random_inv_x = random.randint(inv_x1, inv_x2)
                    random_inv_y = random.randint(inv_y1, inv_y2)
                    
                    print(f"Clicking in inventory area at ({random_inv_x}, {random_inv_y})")
                    
                    # Click in the inventory area
                    success = self.move_mouse_human_like(random_inv_x, random_inv_y, "left")
                    if not success:
                        print("Failed to click in inventory area")
                        return False
                    print("Successfully clicked in inventory area!")
                    
                    # Wait a bit after burying before random mouse movement
                    print("Waiting 0.25 seconds after burying...")
                    time.sleep(0.5)
                    
                    # Random mouse movement after burying (human-like behavior)
                    print("Moving mouse randomly after burying...")
                    self.move_mouse_randomly(distance=100, visualize=False)
                    
                    if save_debug:
                        # Save debug screenshot of inventory click
                        debug_filename = f"debug_screenshots/loot_bury_click_{loot_color}.png"
                        
                        # Capture screenshot of inventory area
                        inv_region = (inv_x1, inv_y1, inv_x2 - inv_x1, inv_y2 - inv_y1)
                        inv_screenshot = screenshot_utils.capture_screen_region(inv_region)
                        
                        # Draw click point
                        click_x = random_inv_x - inv_x1
                        click_y = random_inv_y - inv_y1
                        cv2.circle(inv_screenshot, (click_x, click_y), 5, (0, 0, 255), -1)  # Red dot
                        
                        cv2.imwrite(debug_filename, inv_screenshot)
                        print(f"Bury click debug screenshot saved: {debug_filename}")
                
                return True
                
            except Exception as e:
                print(f"Error in loot pickup process: {e}")
                return False
                
        except Exception as e:
            print(f"Error in loot pickup: {e}")
            return False
    
    def attack_sequence(self, target_hex_color: str = "00FFFFFA", 
                       health_x: Optional[int] = None,
                       health_y: Optional[int] = None,
                       wait_time: float = 4.0,
                       food_area: Optional[Tuple[int, int, int, int]] = None,
                       red_threshold: int = 5,
                       pixel_method: str = "smart",
                       random_mouse_movement: bool = False,
                       enable_breaks: bool = False):
        """
        Complete attack sequence: find target, click, check combat by color, and auto-eat
        """
        print(f"Starting attack sequence for color: {target_hex_color}")
        
        # Load health bar position if not provided
        if health_x is None or health_y is None:
            health_pos = self.load_health_bar_position()
            if health_pos is None:
                print("No health bar position found. Please configure health bar position in your config file.")
                return False
            health_x, health_y = health_pos
        
        # Load food area if not provided
        if food_area is None:
            food_area = self.load_food_area()
            if food_area is None:
                print("No food area configured. Auto-eating will be disabled.")
                print("Configure food area in your config file to enable auto-eating.")
        
        # Step 0: Check if already in combat (mob auto-attacked after previous death)
        print("Step 0: Checking if already in combat...")
        combat_detected = self.check_combat_status_by_color(health_x, health_y, mode="combat", tolerance=30)
        
        if combat_detected:
            print("Already in combat! Skipping target selection and monitoring for mob death...")
            # Skip to combat monitoring phase
            return self.monitor_combat_and_health(health_x, health_y, food_area, red_threshold, random_mouse_movement)
        
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
            return self.monitor_combat_and_health(health_x, health_y, food_area, red_threshold, random_mouse_movement)
    
    def monitor_combat_and_health(self, health_x: int, health_y: int, 
                                 food_area: Optional[Tuple[int, int, int, int]], 
                                 red_threshold: int, random_mouse_movement: bool = False) -> bool:
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
        
        # Add timeout mechanism - give up after 60 seconds
        start_time = time.time()
        timeout_duration = 60  # 60 seconds = 1 minute
        
        while True:
            # Check for timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                print(f"Timeout reached ({timeout_duration} seconds). Giving up on current mob and restarting attack sequence.")
                return False  # Signal to restart attack sequence
            # Random mouse movement during combat (5% chance each tick)
            if random_mouse_movement and random.random() < 0.05:
                self.move_mouse_randomly(distance=50, visualize=False)
            
            # Check for mob death first
            death_detected = self.check_combat_status_by_color(health_x, health_y, mode="death", tolerance=30)
            
            if death_detected:
                print("Mob is dead!")
                
                # Check if loot pickup is enabled
                loot_config = self.load_loot_config()
                print(f"Loot config: {loot_config}")
                print(f"Bury: {loot_config.get('bury', False)}")
                print(f"Inventory area: {loot_config.get('inventory_area', None)}")
                if loot_config.get('enabled', True):
                    print("Waiting 1 second before attempting to pickup loot...")
                    time.sleep(3)
                    
                    print("Attempting to pickup loot...")
                    
                    # Try to pickup loot with configured settings
                    loot_picked = self.pickup_loot(
                        loot_color=loot_config.get('loot_color', 'AA00FFFF'),
                        tolerance=loot_config.get('tolerance', 10),
                        max_distance=loot_config.get('max_distance', 500),
                        save_debug=loot_config.get('save_debug', True),
                        bury=loot_config.get('bury', False),
                        inventory_area=loot_config.get('inventory_area', None)
                    )
                    if loot_picked:
                        print("Loot pickup successful!")
                    else:
                        print("No loot found or loot pickup failed")
                else:
                    print("Loot pickup is disabled in configuration")
                
                print("Waiting random time (up to 5 minutes, avg 2 seconds)...")
                # Use exponential distribution for skewed timing: most waits are short, some are longer
                # This gives us an average of 3 seconds but can go up to 5 minutes
                # wait_time = min(random.expovariate(1/2), 300)  # 1/2 = 2 second average, max 300 seconds (5 minutes)
                wait_time = min(random.expovariate(1/1), 300)  # 1/1 = 1 second average, max 300 seconds (5 minutes)
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
                        success = self.move_mouse_human_like(random_x, random_y, "left")
                        if success:
                            print("Food eaten! Continuing combat...")
                            
                            # Wait a moment for the food to be consumed
                            time.sleep(0.5)
                        else:
                            print("Failed to eat food")
                        
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
    
    def load_health_bar_position(self) -> Optional[Tuple[int, int]]:
        """
        Load saved health bar position from config manager
        """
        health_pos = self.config_manager.get_health_bar_position()
        if health_pos:
            print(f"Loaded health bar position from config: {health_pos}")
            return health_pos
        return None

    def load_food_area(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Load saved food area from config manager
        """
        food_area = self.config_manager.get_food_area_coordinates()
        if food_area:
            print(f"Loaded food area from config: {food_area}")
            return food_area
        return None

    def load_loot_config(self) -> dict:
        """
        Load loot configuration from config manager
        """
        loot_config = self.config_manager.get_loot_pickup_config()
        inventory_area = self.config_manager.get_inventory_area_coordinates()
        return {
            'loot_color': loot_config.get('loot_color', 'AA00FFFF'),
            'tolerance': loot_config.get('tolerance', 10),
            'max_distance': loot_config.get('max_distance', 500),
            'enabled': loot_config.get('enabled', True),
            'save_debug': loot_config.get('save_debug', True),
            'inventory_area': inventory_area if inventory_area else (0, 0, 0, 0),
            'bury': loot_config.get('bury', False)
        } 