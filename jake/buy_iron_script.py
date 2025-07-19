#!/usr/bin/env python3
"""
Buy Iron Script

This bot implements an iron buying sequence with the following steps:
1. Click on a ladder to climb down (user-defined box)
2. Wait for specified time
3. Move towards vendor (click in vendor region box)
4. Click on vendor (target color)
5. Buy iron ore (click in user-defined box)
6. Deposit in bank (target color)
7. Repeat from step 1
"""

import time
import random
import jake.screenshot_utils
import jake.pixel_clicker
from jake.config_manager import ConfigurationManager
from typing import Optional

class BuyIronBot:
    """Bot that handles buying iron ore from vendor and depositing in bank."""
    
    def __init__(self, config_file: str = "buy_iron_config.json"):
        """
        Initialize the buy iron bot.
        
        Args:
            config_file: Path to the configuration file
        """
        self.initialized = False
        
        try:
            self.config_manager = ConfigurationManager(config_file)
            self.config = self.config_manager.config
            
            # Load buy iron configuration
            self.buy_iron_config = self.config.get("buy_iron", {})
            if not self.buy_iron_config.get("enabled", False):
                raise ValueError("Buy iron bot is not enabled in configuration")
            
            # Load buy iron-specific settings
            self.ladder_color = self.buy_iron_config.get("ladder_color")
            self.wait_time = self.buy_iron_config.get("wait_time", 5.0)
            self.vendor_color = self.buy_iron_config.get("vendor_color")
            self.buy_box = self.buy_iron_config.get("buy_box")
            self.bank_color = self.buy_iron_config.get("bank_color")
            self.color_tolerance = self.buy_iron_config.get("color_tolerance", 20)
            self.vendor_click_wait = self.buy_iron_config.get("vendor_click_wait", 5.0)
            self.verify_clicks = self.buy_iron_config.get("verify_clicks", True)
            self.inventory_deposit_box = self.buy_iron_config.get("inventory_deposit_box")
            self.vendor_region_box = self.buy_iron_config.get("vendor_region_box")
            self.ladder_time = 15 # time to walk to ladder from vendor

            # Load general bot settings
            self.human_movement = self.config.get("human_movement", {})
            self.debug_config = self.config.get("debug", {})
            
            # Debug settings
            self.debug_enabled = self.debug_config.get("save_screenshots", True)
            self.screenshot_dir = self.debug_config.get("screenshot_dir", "debug_screenshots")
            
            # Window detection
            self.window_title = "RuneLite"
            self.window_region = jake.screenshot_utils.find_runescape_window(self.window_title)
            
            # Validate required configuration
            self._validate_configuration()
            
            # Mouse movement and pixel clicking
            self.mouse = jake.pixel_clicker.PixelClicker(self.window_region, use_human_paths=True)
            
            self.initialized = True
            
            print("Buy Iron Bot initialized successfully")
            print(f"Ladder color: #{self.ladder_color}")
            print(f"Wait time: {self.wait_time}s")
            print(f"Vendor color: #{self.vendor_color}")
            print(f"Vendor region box: {self.vendor_region_box}")
            print(f"Buy box: {self.buy_box}")
            print(f"Bank color: #{self.bank_color}")
            print(f"Inventory deposit box: {self.inventory_deposit_box}")
            print(f"Color tolerance: {self.color_tolerance}")
            print(f"Debug mode: {'Enabled' if self.debug_enabled else 'Disabled'}")
            
        except Exception as e:
            print(f"Failed to initialize Buy Iron Bot: {e}")
            self.initialized = False
            raise
    
    def _validate_configuration(self):
        """
        Validate that all required configuration is present and valid.
        Raises ValueError if any required configuration is missing.
        """
        if not self.vendor_region_box:
            raise ValueError("Vendor region box is required but not configured")
        
        if not self.vendor_color:
            raise ValueError("Vendor color is required but not configured")
        
        if not self.buy_box:
            raise ValueError("Buy box is required but not configured")
        
        if not self.bank_color:
            raise ValueError("Bank color is required but not configured")
        
        if not self.inventory_deposit_box:
            raise ValueError("Inventory deposit box is required but not configured")
        
        if not self.ladder_color:
            raise ValueError("Ladder color is required but not configured")
        
        print("Configuration validation passed")

    def wait(self, seconds: float, random_addition: float = 5.0) -> None:
        """
        Wait for a specified time plus a random additional amount.
        
        Args:
            seconds: Base time to wait in seconds
            random_addition: Maximum random additional time in seconds (default: 5.0)
        """
        total_wait = seconds + random.uniform(0, random_addition)
        print(f"Waiting {total_wait:.1f} seconds")
        time.sleep(total_wait)

    def move_towards_vendor(self) -> bool:
        """
        Move towards vendor by clicking in the vendor region box
        
        Returns:
            True if successful, False otherwise
        """
        print("Clicking randomly in vendor region box...")
        if not self.mouse.click_random_in_box(self.vendor_region_box, "left"):
            print("Failed to click in vendor region box")
            return False
        
        # Wait a bit for vendor to appear
        self.wait(8)
        return True
    
    def click_vendor(self) -> bool:
        print("\n=== Step 4: Clicking on vendor ===")
        
        # Debug screenshot showing vendor color detection
        if self.debug_enabled:
            jake.screenshot_utils.save_debug_screenshot(
                self.window_region,
                "vendor_color_detection",
                self.screenshot_dir,
                color_detection=(self.vendor_color, self.color_tolerance),
                save_original=True
            )
        
        # Click on vendor with optional verification
        if not self.mouse.click_random_pixel_by_color(
            self.vendor_color,
            self.color_tolerance,
            verify_click=self.verify_clicks,
            max_attempts=10
        ):
            print("Failed to click on vendor - check debug screenshots")
            return False

        return True
    
    def deposit_in_bank(self) -> bool:
        print("\n=== Step 6: Bank interaction ===")
        
        # Step 6a: Click on banker
        print("Step 6a: Clicking on banker")
        if not self.mouse.click_random_pixel_by_color(self.bank_color, self.color_tolerance, verify_click=self.verify_clicks):
            print("Failed to click on banker")
            return False
        
        # Step 6b: Wait for bank interface to open
        self.wait(self.wait_time)
        
        # Step 6c: Click on inventory box to deposit items
        print("Step 6c: Clicking on inventory box to deposit items")
        return self.mouse.click_random_in_box(self.inventory_deposit_box, "left")
    
    def run_cycle(self) -> bool:
        """
        Run one complete buy iron cycle
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        print("\n" + "="*50)
        print("Starting new buy iron cycle")
        print("="*50)
        
        try:
            # Step 1: Climb down ladder
            print("\n=== Step 1: Climbing down ladder ===")
            if not self.mouse.click_random_pixel_by_color(self.ladder_color, self.color_tolerance):
                print("Failed to climb down ladder")
                return False
            self.wait(self.wait_time)

            # Step 2: Move towards vendor
            if not self.move_towards_vendor():
                print("Failed to move towards vendor")
                return False

            # Step 3: Click on vendor
            if not self.click_vendor():
                print("Failed to click on vendor")
                return False
  
            self.wait(self.vendor_click_wait)
            
            # Step 4: Buy iron ore
            print("\n=== Step 4: Buying iron ore ===")
            if not self.mouse.click_random_in_box(self.buy_box, "left"):
                print("Failed to buy iron ore")
                return False
            
            # Step 5: Climb up ladder (same as step 1)
            print("\n=== Step 5: Climbing up ladder ===")
            if not self.mouse.click_random_pixel_by_color(self.ladder_color, self.color_tolerance):
                print("Failed to climb up ladder")
                return False
            self.wait(self.ladder_time)

            # Step 6: Deposit in bank
            if not self.deposit_in_bank():
                print("Failed to deposit in bank")
                return False
            
            print("\n" + "="*50)
            print("Buy iron cycle completed successfully")
            print("="*50)
            return True
            
        except Exception as e:
            print(f"Error during buy iron cycle: {e}")
            return False
    
    def run(self, max_cycles: Optional[int] = None):
        """
        Run the buy iron bot
        
        Args:
            max_cycles: Maximum number of cycles to run (None for infinite)
        """
        if not self.initialized:
            print("Buy Iron Bot is not properly initialized. Cannot run.")
            return
        
        print("Starting Buy Iron Bot")
        print("Press 'q' to quit")
        
        cycle_count = 0
        
        try:
            while True:
                # Check max cycles
                if max_cycles and cycle_count >= max_cycles:
                    print(f"\nReached maximum cycles ({max_cycles}). Stopping bot.")
                    break
                
                cycle_count += 1
                print(f"\nStarting cycle {cycle_count}")
                
                # Run one cycle
                success = self.run_cycle()
                
                if not success:
                    print(f"Cycle {cycle_count} failed. Retrying...")
                    self.wait(5)
                    continue
                
                # Wait between cycles
                print(f"Waiting before next cycle...")
                self.wait(2.0)
                
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Buy Iron Bot stopped")