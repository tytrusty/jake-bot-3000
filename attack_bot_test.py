#!/usr/bin/env python3
"""
Test script for the RuneScape Attack Bot
Demonstrates finding pixels by color and checking combat status
"""

from runescape_bot import RuneScapeBot
import time
import pyautogui

def test_pixel_finding():
    """Test finding pixels with a specific color"""
    print("=== Testing Pixel Finding (Left Half of Screen) ===")
    
    bot = RuneScapeBot()
    
    # Get screen dimensions
    screen_width = pyautogui.size().width
    screen_height = pyautogui.size().height
    print(f"Screen dimensions: {screen_width}x{screen_height}")
    print(f"Scanning left half: 0,0 to {screen_width//2},{screen_height}")
    
    # Test color (you can change this to any hex color)
    test_color = "FF00FFFA"  # Magenta-like color
    print(f"Looking for pixels with color: {test_color}")
    
    # Find pixels with debug screenshot
    pixels = bot.find_pixels_by_color(test_color, tolerance=10, save_debug=True)
    
    if pixels:
        print(f"Found {len(pixels)} pixels!")
        print("First 5 pixel coordinates (relative to left half):")
        for i, (x, y) in enumerate(pixels[:5]):
            print(f"  {i+1}: ({x}, {y})")
        
        # Test clicking on a random pixel
        print("\nTesting random pixel click...")
        success = bot.click_random_pixel_by_color(test_color)
        if success:
            print("Successfully clicked on a random pixel!")
        else:
            print("Failed to click on pixel")
    else:
        print("No pixels found with that color")
        print("Check debug_screenshots/ folder for the screenshot")

def test_combat_detection():
    """Test combat status detection"""
    print("\n=== Testing Combat Detection ===")
    
    bot = RuneScapeBot()
    
    # Find RuneScape window
    window_region = bot.find_runescape_window()
    if not window_region:
        print("Could not find RuneScape window!")
        return
    
    bot.window_region = window_region
    print(f"Found window at: {window_region}")
    
    # Check combat status
    print("Checking combat status...")
    in_combat = bot.check_combat_status("combat_indicator")
    
    if in_combat:
        print("Player is currently in combat!")
    else:
        print("Player is not in combat")

def test_attack_sequence():
    """Test the complete attack sequence"""
    print("\n=== Testing Attack Sequence ===")
    
    bot = RuneScapeBot()
    
    # Find RuneScape window
    window_region = bot.find_runescape_window()
    if not window_region:
        print("Could not find RuneScape window!")
        return
    
    bot.window_region = window_region
    print(f"Found window at: {window_region}")
    
    # Test attack sequence
    target_color = "FF00FFFA"  # Change this to your target color
    combat_template = "combat_indicator"  # Change this to your combat template
    
    print(f"Running attack sequence with color: {target_color}")
    print("Make sure you have a combat template saved as 'combat_indicator.png'")
    
    success = bot.attack_sequence(target_color, combat_template, wait_time=2.0)
    
    if success:
        print("Attack sequence completed successfully!")
    else:
        print("Attack sequence failed")

def test_debug_screenshots():
    """Test debug screenshot functionality"""
    print("\n=== Testing Debug Screenshots ===")
    
    bot = RuneScapeBot()
    
    # Find RuneScape window
    window_region = bot.find_runescape_window()
    if not window_region:
        print("Could not find RuneScape window!")
        return
    
    bot.window_region = window_region
    print(f"Found window at: {window_region}")
    
    # Test different colors
    test_colors = ["FF00FFFA", "FF0000FF", "00FF00FF", "0000FFFF"]
    
    for color in test_colors:
        print(f"\nTesting color: {color}")
        pixels = bot.find_pixels_by_color(color, tolerance=10, save_debug=True)
        
        if pixels:
            print(f"Found {len(pixels)} pixels with color {color}")
        else:
            print(f"No pixels found with color {color}")
        
        time.sleep(1)  # Brief pause between tests
    
    print("\nAll debug screenshots saved to debug_screenshots/ folder")

def main():
    """Main test menu"""
    print("RuneScape Attack Bot - Test Suite")
    print("=" * 40)
    print("1. Test pixel finding")
    print("2. Test combat detection")
    print("3. Test complete attack sequence")
    print("4. Test debug screenshots")
    print("5. Run all tests")
    print("6. Exit")
    
    while True:
        choice = input("\nChoose a test (1-6): ").strip()
        
        if choice == "1":
            test_pixel_finding()
        elif choice == "2":
            test_combat_detection()
        elif choice == "3":
            test_attack_sequence()
        elif choice == "4":
            test_debug_screenshots()
        elif choice == "5":
            print("Running all tests...")
            test_pixel_finding()
            time.sleep(2)
            test_combat_detection()
            time.sleep(2)
            test_attack_sequence()
            time.sleep(2)
            test_debug_screenshots()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 