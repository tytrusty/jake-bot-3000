import cv2
import numpy as np
import pyautogui
import time
import os
from PIL import Image, ImageGrab
from typing import Tuple, Optional, List

def capture_screen_region(region: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Capture a specific region of the screen
    
    Args:
        region: (x, y, width, height) coordinates
        
    Returns:
        OpenCV image array in BGR format
    """
    x, y, w, h = region
    screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def capture_left_half_screen() -> np.ndarray:
    """
    Capture the left 50% of the screen
    
    Returns:
        OpenCV image array of left half screen
    """
    # Get screen dimensions
    screen_width = pyautogui.size().width
    screen_height = pyautogui.size().height
    
    # Calculate left half region
    left_half_region = (0, 0, screen_width, screen_height)
    
    return capture_screen_region(left_half_region)

def get_left_half_region() -> Tuple[int, int, int, int]:
    """
    Get the coordinates for the left 50% of the screen
    
    Returns:
        (x, y, width, height) for left half of screen
    """
    screen_width = pyautogui.size().width
    screen_height = pyautogui.size().height
    return (0, 0, screen_width // 2, screen_height)

def save_screenshot(filename: Optional[str] = None, 
                   region: Optional[Tuple[int, int, int, int]] = None) -> str:
    """
    Save a screenshot for debugging purposes
    
    Args:
        filename: Optional filename (auto-generated if None)
        region: Optional region to capture (full screen if None)
        
    Returns:
        Path to the saved screenshot
    """
    try:
        if filename is None:
            timestamp = int(time.time())
            filename = f"debug_screenshot_{timestamp}.png"
        
        if region is None:
            # Capture full screen
            region = (0, 0, pyautogui.size().width, pyautogui.size().height)
        
        # Capture the region
        screenshot = capture_screen_region(region)
        
        # Save to debug directory
        debug_dir = "debug_screenshots"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        filepath = os.path.join(debug_dir, filename)
        cv2.imwrite(filepath, screenshot)
        
        print(f"Screenshot saved: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        return ""

def save_screenshot_with_highlights(pixels: List[Tuple[int, int]], 
                                  filename: Optional[str] = None, 
                                  hex_color: str = "FF00FFFA") -> str:
    """
    Save a screenshot with highlighted pixels for debugging
    
    Args:
        pixels: List of (x, y) coordinates to highlight
        filename: Optional filename (auto-generated if None)
        hex_color: Color that was searched for (for display)
        
    Returns:
        Path to the saved highlighted screenshot
    """
    try:
        if filename is None:
            timestamp = int(time.time())
            filename = f"debug_highlighted_{timestamp}.png"
        
        # Capture the left half of the screen
        screenshot = capture_left_half_screen()
        
        # Draw circles around found pixels
        for x, y in pixels:
            cv2.circle(screenshot, (x, y), 3, (0, 255, 0), -1)  # Green circle
            cv2.circle(screenshot, (x, y), 5, (255, 0, 0), 2)   # Blue outline
        
        # Add text showing pixel count and region info
        cv2.putText(screenshot, f"Found {len(pixels)} pixels in left half", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screenshot, f"Color: {hex_color}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Save to debug directory
        debug_dir = "debug_screenshots"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        filepath = os.path.join(debug_dir, filename)
        cv2.imwrite(filepath, screenshot)
        
        print(f"Highlighted screenshot saved: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error saving highlighted screenshot: {e}")
        return ""

def get_pixel_color_at_position(x: int, y: int) -> Tuple[int, int, int]:
    """
    Get the RGB color of a pixel at the specified screen position
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        RGB color tuple
    """
    try:
        # Capture a small region around the pixel
        region = (x, y, 1, 1)
        screenshot = capture_screen_region(region)
        
        # Get the pixel color (OpenCV uses BGR, so convert to RGB)
        bgr_color = screenshot[0, 0]
        rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])  # BGR to RGB
        
        return rgb_color
        
    except Exception as e:
        print(f"Error getting pixel color: {e}")
        return (0, 0, 0)  # Return black on error

# Example usage
if __name__ == "__main__":
    print("Screenshot Utils Test")
    
    # Test capturing and saving a screenshot
    print("1. Capturing screenshot...")
    filepath = save_screenshot()
    print(f"Screenshot saved to: {filepath}")
    
    # Test getting pixel color
    print("\n2. Getting pixel color at (100, 100)...")
    color = get_pixel_color_at_position(100, 100)
    print(f"Pixel color: RGB{color}")
    
    print("Test complete!") 