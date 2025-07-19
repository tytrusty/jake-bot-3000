import cv2
import numpy as np
import pyautogui
import os
from PIL import Image, ImageGrab
from typing import Tuple, Optional, List
import jake.color_utils

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
            filename = "debug_screenshot.png"
        
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
            filename = "debug_highlighted.png"
        
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

def find_runescape_window(window_title: str = "RuneLite") -> Tuple[int, int, int, int]:
    """
    Find the RuneScape window and return its coordinates (x, y, width, height)
    
    Args:
        window_title: Title of the window to search for (default: "RuneLite")
        
    Returns:
        Tuple of (x, y, width, height) coordinates or None if not found
    """
    try:
        # Try to find window by title
        import win32gui
        import win32con
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title_text = win32gui.GetWindowText(hwnd)
                if window_title.lower() in window_title_text.lower():
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
                    windows.append((x, y, w, h))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            return windows[0]  # Return the first matching window
        else:
            raise ValueError(f"Could not find window with title containing '{window_title}'")
            
    except ImportError:
        raise ImportError("win32gui not available. Please install pywin32: pip install pywin32")
    except Exception as e:
        raise Exception(f"Error finding window: {e}")

def save_debug_screenshot(region: Tuple[int, int, int, int],
                         action: str,
                         screenshot_dir: str = "debug_screenshots",
                         target_positions: Optional[List[Tuple[int, int, str]]] = None,
                         color_detection: Optional[Tuple[str, int]] = None,
                         save_original: bool = False) -> Tuple[bool, str]:
    """
    Save a debug screenshot with optional markings and color detection
    
    Args:
        region: Screen region to capture (x, y, width, height)
        action: Description of the action being performed
        screenshot_dir: Directory to save screenshots in
        target_positions: List of (x, y, color_name) tuples to mark with circles
                         color_name can be "green", "red", "blue", "yellow", etc.
        color_detection: Tuple of (hex_color, tolerance) for color detection
        save_original: Whether to save the original unmarked screenshot
        
    Returns:
        Tuple of (success, filename) where success indicates if operation completed
    """
    try:
        # Create screenshot directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Capture screenshot
        screenshot = capture_screen_region(region)
        if screenshot is None:
            print("Failed to capture debug screenshot")
            return False, ""
        
        # Create a copy for marking
        debug_screenshot = screenshot.copy()
        
        # Color mapping for different target types
        color_map = {
            "green": (0, 255, 0),
            "red": (0, 0, 255),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "white": (255, 255, 255),
            "black": (0, 0, 0)
        }
        
        # Mark target positions if provided
        if target_positions:
            for x, y, color_name in target_positions:
                color = color_map.get(color_name.lower(), (0, 255, 0))  # Default to green
                cv2.circle(debug_screenshot, (int(x), int(y)), 10, color, 2)
                cv2.circle(debug_screenshot, (int(x), int(y)), 2, color, -1)
        
        # Perform color detection if requested
        detection_result = None
        if color_detection:
            hex_color, tolerance = color_detection
            matching_pixels = jake.color_utils.find_pixels_by_color(
                screenshot, hex_color, tolerance
            )
            
            if matching_pixels:
                print(f"Color found! {len(matching_pixels)} pixels detected")
                # Mark all matching pixels with red dots
                for x, y in matching_pixels:
                    cv2.circle(debug_screenshot, (x, y), 2, (0, 128, 255), 2)  # Red dot
                detection_result = True
            else:
                print("Color not found on screen")
                detection_result = False
        
        # Determine filename based on what we're doing
        if color_detection:
            if detection_result:
                filename = f"{screenshot_dir}/{action}_color_found.png"
            else:
                filename = f"{screenshot_dir}/{action}_color_not_found.png"
        else:
            filename = f"{screenshot_dir}/{action}.png"
        
        cv2.imwrite(filename, debug_screenshot)
        print(f"Debug screenshot saved: {filename}")
        
        # Save original screenshot if requested
        if save_original:
            original_filename = f"{screenshot_dir}/{action}_original.png"
            cv2.imwrite(original_filename, screenshot)
            print(f"Original screenshot saved: {original_filename}")
        
        return True, filename
        
    except Exception as e:
        print(f"Error saving debug screenshot: {e}")
        return False, ""

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