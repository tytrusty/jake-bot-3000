import cv2
import numpy as np
import pyautogui
import time
import random
import os
from typing import Tuple, Optional, List
import jake.screenshot_utils
import jake.color_utils
import jake.pixel_selection
from scipy.ndimage import label, binary_dilation
import math
from sklearn.cluster import DBSCAN
from jake.config_manager import ConfigurationManager
import jake.pixel_clicker
import keyboard  

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class AttackBot:
    def __init__(self, config_manager: ConfigurationManager, use_human_paths: bool = False):
        self.running = False
        self.window_title = "RuneLite"
        self.in_combat = False  # Combat status flag
        self.use_human_paths = use_human_paths
        self.config_manager = config_manager
        self.initialized = False
        
        # Validate configuration and load all settings
        self._validate_and_load_configuration()
        
        # Find RuneScape window and initialize mouse
        self.window_region = jake.screenshot_utils.find_runescape_window(self.window_title)
        
        # Initialize mouse for all mouse interactions
        self.mouse = jake.pixel_clicker.PixelClicker(
            self.window_region, 
            use_human_paths=use_human_paths, 
            config_manager=config_manager if use_human_paths else None
        )
        
        self.initialized = True
        print(f"Attack bot initialized with window region: {self.window_region}")
        self.print_config_summary()
    
    def _validate_and_load_configuration(self):
        """
        Validate that all required configuration is present and load all settings.
        Raises ValueError if any required configuration is missing.
        """
        # Load all configuration sections
        self.health_config = self.config_manager.get_health_bar_config()
        self.food_config = self.config_manager.get_food_area_config()
        self.loot_config = self.config_manager.get_loot_pickup_config()
        self.combat_config = self.config_manager.get_combat_config()
        self.debug_config = self.config_manager.get_debug_config()
        
        # Load specific configuration values
        self.health_bar_position = self.config_manager.get_health_bar_position()
        self.food_area_coordinates = self.config_manager.get_food_area_coordinates()
        self.inventory_area_coordinates = self.config_manager.get_inventory_area_coordinates()
        
        # Load boolean flags
        self.food_area_enabled = self.config_manager.is_food_area_enabled()
        self.loot_pickup_enabled = self.config_manager.is_loot_pickup_enabled()
        self.random_mouse_movement_enabled = self.config_manager.is_random_mouse_movement_enabled()
        self.breaks_enabled = self.config_manager.is_breaks_enabled()
        
        # Load combat settings
        self.default_target_color = self.combat_config.get('default_target_color', '00FFFFFA')
        self.pixel_method = self.combat_config.get('pixel_method', 'smart')
        self.red_threshold = self.food_config.get('red_threshold', 5)
        
        # Load loot settings
        self.loot_color = self.loot_config.get('loot_color', 'AA00FFFF')
        self.loot_tolerance = self.loot_config.get('tolerance', 10)
        self.loot_max_distance = self.loot_config.get('max_distance', 500)
        self.loot_save_debug = self.loot_config.get('save_debug', True)
        self.loot_bury = self.loot_config.get('bury', False)
        
        # Load break settings
        self.break_interval_min = self.combat_config.get('break_interval_min', 29)
        self.break_interval_max = self.combat_config.get('break_interval_max', 33)
        self.break_duration_min = self.combat_config.get('break_duration_min', 2)
        self.break_duration_max = self.combat_config.get('break_duration_max', 6)
        
        # Validate required configuration
        self._validate_required_config()
        
        print("Configuration validation and loading completed")
    
    def _validate_required_config(self):
        """
        Validate that all required configuration is present.
        Raises ValueError if any required configuration is missing.
        """
        # Health bar position is required
        if self.health_bar_position is None:
            raise ValueError("Health bar position is required but not configured. Please configure health bar position in your config file.")
        
        # If food area is enabled, coordinates must be provided
        if self.food_area_enabled and self.food_area_coordinates is None:
            raise ValueError("Food area is enabled but coordinates are not configured. Please configure food area coordinates in your config file.")
        
        # If loot pickup is enabled and burying is enabled, inventory area must be provided
        if self.loot_pickup_enabled and self.loot_bury and self.inventory_area_coordinates is None:
            raise ValueError("Loot pickup with burying is enabled but inventory area is not configured. Please configure inventory area coordinates in your config file.")
            
    def print_config_summary(self):
        """
        Print a summary of the bot's configuration settings.
        """
        print("\n=== Attack Bot Configuration Summary ===")
        print(f"Health bar position: {self.health_bar_position}")
        print(f"Default target color: #{self.default_target_color}")
        print(f"Pixel selection method: {self.pixel_method}")
        
        # Food area settings
        print(f"Auto-eating: {'Enabled' if self.food_area_enabled else 'Disabled'}")
        if self.food_area_enabled:
            print(f"  Food area coordinates: {self.food_area_coordinates}")
            print(f"  Health monitoring threshold: {self.red_threshold}")
        
        # Loot pickup settings
        print(f"Loot pickup: {'Enabled' if self.loot_pickup_enabled else 'Disabled'}")
        if self.loot_pickup_enabled:
            print(f"  Loot color: #{self.loot_color}")
            print(f"  Tolerance: {self.loot_tolerance}")
            print(f"  Max distance: {self.loot_max_distance}")
            print(f"  Bury items: {'Yes' if self.loot_bury else 'No'}")
            print(f"  Save debug screenshots: {'Yes' if self.loot_save_debug else 'No'}")
        
        # Combat behavior settings
        print(f"Random mouse movement: {'Enabled' if self.random_mouse_movement_enabled else 'Disabled'}")
        print(f"Automatic breaks: {'Enabled' if self.breaks_enabled else 'Disabled'}")
        if self.breaks_enabled:
            print(f"  Break intervals: {self.break_interval_min}-{self.break_interval_max} minutes")
            print(f"  Break duration: {self.break_duration_min}-{self.break_duration_max} minutes")
        
        # Human movement settings
        print(f"Human-like movement: {'Enabled' if self.use_human_paths else 'Disabled'}")
        print()
    
    def click_random_pixel_by_color(self, hex_color: str, tolerance: int = 10, method: str = "smart") -> bool:
        """
        Find pixels with specified color and click on a random one
        
        Args:
            hex_color: Target hex color to find
            tolerance: Color tolerance for matching
            method: "random" for original method, "smart" for blob-based selection
        """
        # Use mouse for color-based clicking
        if method == "smart":
            screenshot = jake.screenshot_utils.capture_screen_region(self.window_region)
            downsample_factor = 4  # Can be made configurable
            selected_pixel = jake.pixel_selection.smart_pixel_select(screenshot, hex_color, tolerance, return_debug=False, downsample_factor=downsample_factor)
            
            if selected_pixel is None:
                print(f"No pixels found with color {hex_color} using method '{method}'")
                return False
            
            # Handle the return type properly
            if isinstance(selected_pixel, tuple) and len(selected_pixel) == 2:
                pixel_x, pixel_y = selected_pixel
            else:
                print(f"Unexpected pixel selection result: {selected_pixel}")
                return False
            
            # Convert to absolute screen coordinates
            window_x, window_y = self.window_region[0], self.window_region[1]
            screen_x = window_x + pixel_x
            screen_y = window_y + pixel_y
            
            # Use mouse for movement and clicking
            return self.mouse.move_mouse(screen_x, screen_y, "left")
        else:
            # Use mouse's built-in color-based clicking
            return self.mouse.click_random_pixel_by_color(hex_color, tolerance, verify_click=False)
    
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
            # Capture screenshot of the RuneScape window
            screenshot = jake.screenshot_utils.capture_screen_region(self.window_region)
            
            # Calculate screen center relative to the window
            window_width = self.window_region[2]
            window_height = self.window_region[3]
            center_x = window_width // 2
            center_y = window_height // 2
            
            print(f"Searching for loot with color #{loot_color} within {max_distance} pixels of center ({center_x}, {center_y})")
            
            # Find all pixels with the loot color
            loot_pixels = jake.color_utils.find_pixels_by_color(screenshot, loot_color, tolerance)
            
            if not loot_pixels:
                print(f"No loot pixels found with color #{loot_color}")
                if save_debug:
                    jake.screenshot_utils.save_debug_screenshot(
                        self.window_region,
                        f"loot_debug_no_pixels_{loot_color}",
                        color_detection=(loot_color, tolerance),
                        save_original=True
                    )
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
                    # Mark center and range circle
                    jake.screenshot_utils.save_debug_screenshot(
                        self.window_region,
                        f"loot_debug_outside_range_{loot_color}",
                        target_positions=[(center_x, center_y, "white")],
                        color_detection=(loot_color, tolerance),
                        save_original=True
                    )
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
                    
                    if best_centroid is None:
                        print("No valid centroid found")
                        return False
                        
                    selected_pixel = best_centroid
                    pixel_x, pixel_y = selected_pixel
                    print(f"Selected cluster {best_cluster} centroid at ({pixel_x}, {pixel_y}) from {len(valid_loot_pixels)} valid pixels (distance to center: {min_distance:.1f})")
                    
                    # Draw cluster circles in debug mode
                    if save_debug:
                        # Mark selected pixel and center
                        target_positions = [
                            (pixel_x, pixel_y, "red"),  # Selected pixel
                            (center_x, center_y, "white"),  # Center point
                        ]
                        
                        jake.screenshot_utils.save_debug_screenshot(
                            self.window_region,
                            f"loot_debug_success_{loot_color}",
                            target_positions=target_positions,
                            color_detection=(loot_color, tolerance),
                            save_original=True
                        )
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
                success = self.mouse.move_mouse(screen_x, screen_y, "right")
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
                menu_screenshot = jake.screenshot_utils.capture_screen_region(menu_region)
                
                # Find loot color pixels in the menu area
                menu_loot_pixels = jake.color_utils.find_pixels_by_color(menu_screenshot, loot_color, tolerance)
                
                if not menu_loot_pixels:
                    print("No loot color found in menu box")
                    if save_debug:
                        jake.screenshot_utils.save_debug_screenshot(
                            menu_region,
                            f"loot_menu_no_pixels_{loot_color}",
                            color_detection=(loot_color, tolerance),
                            save_original=True
                        )
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
                            # Mark selected menu pixel
                            target_positions = [
                                (menu_pixel_x, menu_pixel_y, "red"),  # Selected menu pixel
                            ]
                            
                            jake.screenshot_utils.save_debug_screenshot(
                                menu_region,
                                f"loot_menu_success_{loot_color}",
                                target_positions=target_positions,
                                color_detection=(loot_color, tolerance),
                                save_original=True
                            )
                else:
                    print("No loot pixels found in menu")
                    return False
                
                # Convert to absolute screen coordinates
                absolute_menu_x = menu_start_x + menu_pixel_x
                absolute_menu_y = menu_start_y + menu_pixel_y
                
                print(f"Left-clicking on menu option at ({menu_pixel_x}, {menu_pixel_y}) -> screen ({absolute_menu_x}, {absolute_menu_y})")
                
                # Left-click on the menu option
                success = self.mouse.move_mouse(absolute_menu_x, absolute_menu_y, "left")
                if not success:
                    print("Failed to click on menu option")
                    return False
                print("Successfully clicked on menu option!")
                
                if save_debug:
                    # Save debug screenshot of menu area
                    # Mark selected menu pixel
                    target_positions = [
                        (menu_pixel_x, menu_pixel_y, "red"),  # Selected menu pixel
                    ]
                    
                    jake.screenshot_utils.save_debug_screenshot(
                        menu_region,
                        f"loot_menu_success_{loot_color}",
                        target_positions=target_positions,
                        color_detection=(loot_color, tolerance),
                        save_original=True
                    )
                
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
                    success = self.mouse.move_mouse(random_inv_x, random_inv_y, "left")
                    if not success:
                        print("Failed to click in inventory area")
                        return False
                    print("Successfully clicked in inventory area!")
                    
                    # Wait a bit after burying before random mouse movement
                    print("Waiting 0.5 seconds after burying...")
                    time.sleep(0.5)
                    
                    # Random mouse movement after burying (human-like behavior)
                    print("Moving mouse randomly after burying...")
                    self.mouse.move_mouse_randomly(distance=100)
                    
                    if save_debug:
                        # Save debug screenshot of inventory click
                        inv_region = (inv_x1, inv_y1, inv_x2 - inv_x1, inv_y2 - inv_y1)
                        
                        # Mark click point
                        click_x = random_inv_x - inv_x1
                        click_y = random_inv_y - inv_y1
                        target_positions = [
                            (click_x, click_y, "red"),  # Click point
                        ]
                        
                        jake.screenshot_utils.save_debug_screenshot(
                            inv_region,
                            f"loot_bury_click_{loot_color}",
                            target_positions=target_positions,
                            save_original=True
                        )
                
                return True
                
            except Exception as e:
                print(f"Error in loot pickup process: {e}")
                return False
                
        except Exception as e:
            print(f"Error in loot pickup: {e}")
            return False
    
    def attack_sequence(self, target_hex_color: Optional[str] = None, wait_time: float = 4.0):
        """
        Complete attack sequence: find target, click, check combat by color, and auto-eat
        """
        # Use default target color from config if not provided
        if target_hex_color is None:
            target_hex_color = self.default_target_color
            
        print(f"Starting attack sequence for color: {target_hex_color}")
        assert self.health_bar_position is not None
        health_x, health_y = self.health_bar_position
        food_area = self.food_area_coordinates if self.food_area_enabled else None
        
        # Step 0: Check if already in combat (mob auto-attacked after previous death)
        print("Step 0: Checking if already in combat...")
        combat_detected = self.check_combat_status_by_color(health_x, health_y, mode="combat", tolerance=30)
        
        if combat_detected:
            print("Already in combat! Skipping target selection and monitoring for mob death...")
            # Skip to combat monitoring phase
            return self.monitor_combat_and_health(health_x, health_y, food_area)
        
        # Step 1: Find and click on target pixel
        print("Step 1: Finding and clicking on target...")
        # At this point, target_hex_color is guaranteed to be a string
        assert target_hex_color is not None
        if not self.click_random_pixel_by_color(target_hex_color, method=self.pixel_method):
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
            return self.monitor_combat_and_health(health_x, health_y, food_area)
    
    def monitor_combat_and_health(self, health_x: int, health_y: int, 
                                 food_area: Optional[Tuple[int, int, int, int]]) -> bool:
        """
        Monitor combat status and health during combat
        
        Args:
            health_x: X coordinate of health bar pixel
            health_y: Y coordinate of health bar pixel
            food_area: Food area coordinates for auto-eating
            
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
            if self.random_mouse_movement_enabled and random.random() < 0.05:
                self.mouse.move_mouse_randomly(distance=50)
            
            # Check for mob death first
            death_detected = self.check_combat_status_by_color(health_x, health_y, mode="death", tolerance=30)
            
            if death_detected:
                print("Mob is dead!")
                
                # Check if loot pickup is enabled
                if self.loot_pickup_enabled:
                    print("Waiting 1 second before attempting to pickup loot...")
                    time.sleep(3)
                    
                    print("Attempting to pickup loot...")
                    
                    # Try to pickup loot with pre-loaded settings
                    loot_picked = self.pickup_loot(
                        loot_color=self.loot_color,
                        tolerance=self.loot_tolerance,
                        max_distance=self.loot_max_distance,
                        save_debug=self.loot_save_debug,
                        bury=self.loot_bury,
                        inventory_area=self.inventory_area_coordinates
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
                left_color = jake.screenshot_utils.get_pixel_color_at_position(middle_left_x, middle_left_y)
                
                # Define pure red color (255, 0, 0)
                pure_red = (255, 0, 0)
                
                # Calculate color distance to pure red for both points
                left_distance = jake.color_utils.calculate_color_distance(left_color, pure_red)
                
                # Check if BOTH points are close to pure red (small distance = closer to red)
                if left_distance <= self.red_threshold:
                    print(f"Low health detected! Both points are close to red:")
                    print(f"Left pixel: RGB{left_color} (distance to red: {left_distance:.1f})")
                    
                    # Click randomly in food area
                    x1, y1, x2, y2 = food_area
                    random_x = random.randint(x1, x2)
                    random_y = random.randint(y1, y2)
                    
                    print(f"Eating food at ({random_x}, {random_y})")
                    
                    try:
                        success = self.mouse.move_mouse(random_x, random_y, "left")
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
            pixel_color = jake.screenshot_utils.get_pixel_color_at_position(x, y)
            pixel_hex = jake.color_utils.rgb_to_hex(pixel_color)
            
            # print(f"Health bar pixel ({x}, {y}) color: RGB{pixel_color} = #{pixel_hex}")
            
            if mode == "combat":
                # Check for green combat color (#048834)
                target_color = "048834"
                if jake.color_utils.colors_match(pixel_hex, target_color, tolerance):
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
                if jake.color_utils.colors_match(pixel_hex, target_color, tolerance):
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

    def run(self, target_hex_color: Optional[str] = None, max_cycles: Optional[int] = None):
        """
        Run the attack bot in a continuous loop
        
        Args:
            target_hex_color: Target color to attack (uses default from config if None)
            max_cycles: Maximum number of cycles to run (None for infinite)
        """
        if not self.initialized:
            print("Attack Bot is not properly initialized. Cannot run.")
            return
        
        print("Starting Attack Bot")
        print("Press 'q' to quit")
        
        cycle_count = 0
        session_start_time = time.time()
        last_break_time = session_start_time
        self.running = True
        
        try:
            while self.running:
                # Check max cycles
                if max_cycles and cycle_count >= max_cycles:
                    print(f"\nReached maximum cycles ({max_cycles}). Stopping bot.")
                    break
                
                cycle_count += 1
                print(f"\nStarting cycle {cycle_count}")
                
                # Check if it's time for a break
                if self.breaks_enabled:
                    current_time = time.time()
                    session_duration = current_time - session_start_time
                    time_since_last_break = current_time - last_break_time
                    
                    # Get break settings from bot's pre-loaded config
                    break_interval = random.uniform(
                        self.break_interval_min * 60,
                        self.break_interval_max * 60
                    )
                    
                    if time_since_last_break >= break_interval:
                        # Calculate break duration from bot's pre-loaded config
                        break_duration = random.uniform(
                            self.break_duration_min * 60,
                            self.break_duration_max * 60
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
                        while time.time() - break_start < break_duration and self.running:
                            if keyboard.is_pressed('q'):
                                print("Stopping attack bot during break...")
                                self.running = False
                                break
                            
                            # Show countdown every 30 seconds
                            remaining = break_duration - (time.time() - break_start)
                            if int(remaining) % 30 == 0 and remaining > 0:
                                print(f"Break remaining: {remaining / 60:.1f} minutes")
                            
                            time.sleep(1)
                        
                        if self.running:
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
                
                # Run one attack sequence
                success = self.attack_sequence(target_hex_color)
                
                if success:
                    print("Attack successful! Waiting before next attack...")
                else:
                    print("Attack failed or no targets found. Retrying...")
                
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Attack Bot stopped") 