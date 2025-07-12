import numpy as np
from typing import Tuple, List
import cv2

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color string to RGB tuple
    
    Args:
        hex_color: Hex color string (e.g., "FF00FF" or "#FF00FF")
        
    Returns:
        RGB color tuple
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_hex(rgb_color: Tuple[int, int, int]) -> str:
    """
    Convert RGB tuple to hex color string
    
    Args:
        rgb_color: RGB color tuple
        
    Returns:
        Hex color string
    """
    r, g, b = rgb_color
    return f"{r:02X}{g:02X}{b:02X}"

def calculate_color_distance(color1, color2):
    """
    Calculate Euclidean distance between RGB colors
    
    Args:
        color1: First RGB color (tuple, list, or array)
        color2: Second RGB color (tuple, list, or array)
        
    Returns:
        Distance value (0 = identical, higher = more different)
        Can be scalar or array depending on input types
    """
    try:
        # Convert to numpy arrays for vectorized computation
        color1 = np.asarray(color1)
        color2 = np.asarray(color2)
        distance = np.sqrt(np.sum((color1 - color2) ** 2, axis=-1))
        return distance
        
    except Exception as e:
        print(f"Error calculating color distance: {e}")
        return float('inf')  # Return infinity on error

def colors_match(hex1: str, hex2: str, tolerance: int) -> bool:
    """
    Check if two hex colors match within tolerance
    
    Args:
        hex1: First hex color string
        hex2: Second hex color string
        tolerance: Maximum distance for colors to be considered matching
        
    Returns:
        True if colors match within tolerance
    """
    try:
        rgb1 = hex_to_rgb(hex1)
        rgb2 = hex_to_rgb(hex2)
        
        # Calculate color distance
        distance = calculate_color_distance(rgb1, rgb2)
        
        return distance <= tolerance
        
    except Exception as e:
        print(f"Error comparing colors: {e}")
        return False

def find_colors_in_region(screenshot: np.ndarray) -> List[Tuple[int, int, int]]:
    """
    Find all unique colors in a screenshot region
    
    Args:
        screenshot: OpenCV image array (BGR format)
        
    Returns:
        List of RGB colors sorted by frequency
    """
    try:
        # Convert BGR to RGB
        rgb_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        # Reshape to get all pixels as a list
        pixels = rgb_screen.reshape(-1, 3)
        
        # Count unique colors
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Sort by frequency (most common first)
        sorted_indices = np.argsort(counts)[::-1]
        sorted_colors = [tuple(unique_colors[i]) for i in sorted_indices]
        
        return sorted_colors
        
    except Exception as e:
        print(f"Error finding colors in region: {e}")
        return []

def find_pixels_by_color(screenshot: np.ndarray, target_hex: str, 
                        tolerance: int = 10) -> List[Tuple[int, int]]:
    """
    Find all pixels with the specified hex color within tolerance
    
    Args:
        screenshot: OpenCV image array (BGR format)
        target_hex: Target hex color to find
        tolerance: Color tolerance for matching
        
    Returns:
        List of (x, y) coordinates of matching pixels
    """
    try:
        # Convert hex to RGB
        target_rgb = hex_to_rgb(target_hex)
        
        # Convert BGR to RGB (OpenCV uses BGR)
        target_bgr = (target_rgb[2], target_rgb[1], target_rgb[0])
        
        # Find pixels within tolerance
        lower_bound = np.array([max(0, c - tolerance) for c in target_bgr])
        upper_bound = np.array([min(255, c + tolerance) for c in target_bgr])
        
        # Create mask for pixels within color range
        mask = cv2.inRange(screenshot, lower_bound, upper_bound)
        
        # Find coordinates of matching pixels
        matching_pixels = np.where(mask > 0)
        pixel_coords = list(zip(matching_pixels[1], matching_pixels[0]))  # x, y
        
        return pixel_coords
        
    except Exception as e:
        print(f"Error finding pixels by color: {e}")
        return []

def get_dominant_colors(screenshot: np.ndarray, num_colors: int = 10) -> List[Tuple[Tuple[int, int, int], int]]:
    """
    Get the most dominant colors in a screenshot
    
    Args:
        screenshot: OpenCV image array (BGR format)
        num_colors: Number of dominant colors to return
        
    Returns:
        List of (color, count) tuples sorted by frequency
    """
    try:
        # Convert BGR to RGB
        rgb_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        # Reshape to get all pixels as a list
        pixels = rgb_screen.reshape(-1, 3)
        
        # Count unique colors
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Sort by frequency (most common first)
        sorted_indices = np.argsort(counts)[::-1]
        
        # Return top N colors with their counts
        dominant_colors = []
        for i in range(min(num_colors, len(sorted_indices))):
            idx = sorted_indices[i]
            color = tuple(unique_colors[idx])
            count = counts[idx]
            dominant_colors.append((color, count))
        
        return dominant_colors
        
    except Exception as e:
        print(f"Error getting dominant colors: {e}")
        return []

def is_color_in_range(color: Tuple[int, int, int], 
                     target_color: Tuple[int, int, int], 
                     tolerance: int) -> bool:
    """
    Check if a color is within tolerance range of a target color
    
    Args:
        color: RGB color to check
        target_color: Target RGB color
        tolerance: Maximum distance for colors to be considered in range
        
    Returns:
        True if color is within tolerance range
    """
    distance = calculate_color_distance(color, target_color)
    return distance <= tolerance

# Example usage
if __name__ == "__main__":
    print("Color Utils Test")
    
    # Test color conversions
    print("1. Testing color conversions...")
    test_rgb = (255, 0, 128)
    test_hex = rgb_to_hex(test_rgb)
    converted_rgb = hex_to_rgb(test_hex)
    
    print(f"Original RGB: {test_rgb}")
    print(f"Converted to hex: {test_hex}")
    print(f"Converted back to RGB: {converted_rgb}")
    
    # Test color distance
    print("\n2. Testing color distance...")
    color1 = (255, 0, 0)  # Pure red
    color2 = (255, 10, 10)  # Slightly off red
    distance = calculate_color_distance(color1, color2)
    print(f"Distance between {color1} and {color2}: {distance:.2f}")
    
    # Test color matching
    print("\n3. Testing color matching...")
    hex1 = "FF0000"  # Pure red
    hex2 = "FF0A0A"  # Slightly off red
    matches = colors_match(hex1, hex2, tolerance=20)
    print(f"Colors {hex1} and {hex2} match within tolerance 20: {matches}")
    
    print("Test complete!") 