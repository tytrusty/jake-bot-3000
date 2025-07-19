#!/usr/bin/env python3
"""
Configuration Visualization Script

This script takes a bot configuration file and visualizes all the configured areas
by taking a screenshot of the RuneScape window and drawing labeled boxes on top.
"""

import json
import os
import sys
import cv2
import numpy as np
import pyautogui
import time
from typing import Dict, Any, Optional, Tuple

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jake.screenshot_utils
import jake.color_utils

def find_runescape_window(window_title: str = "RuneLite") -> Optional[Tuple[int, int, int, int]]:
    """
    Find the RuneScape window and return its coordinates (x, y, width, height)
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
            print(f"Could not find window with title containing '{window_title}'")
            return None
            
    except ImportError:
        print("win32gui not available. Please install pywin32: pip install pywin32")
        return None
    except Exception as e:
        print(f"Error finding window: {e}")
        return None

def draw_labeled_box(image: np.ndarray, coords: Tuple[int, int, int, int], 
                    label: str, color: Tuple[int, int, int], thickness: int = 2) -> np.ndarray:
    """
    Draw a labeled box on the image
    
    Args:
        image: OpenCV image to draw on
        coords: (x1, y1, x2, y2) coordinates
        label: Text label for the box
        color: BGR color tuple
        thickness: Line thickness
        
    Returns:
        Modified image with box and label
    """
    x1, y1, x2, y2 = coords
    
    # Draw rectangle
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
    
    # Position label above the box
    label_x = x1
    label_y = max(y1 - 10, text_height + 5)  # Ensure label is visible
    
    # Draw label background rectangle
    cv2.rectangle(image, 
                  (label_x - 2, label_y - text_height - 2),
                  (label_x + text_width + 2, label_y + baseline + 2),
                  color, -1)  # Filled rectangle
    
    # Draw label text
    cv2.putText(image, label, (label_x, label_y), font, font_scale, (255, 255, 255), thickness)
    
    return image

def draw_point_with_label(image: np.ndarray, point: Tuple[int, int], 
                         label: str, color: Tuple[int, int, int], 
                         radius: int = 5, thickness: int = 2) -> np.ndarray:
    """
    Draw a labeled point on the image
    
    Args:
        image: OpenCV image to draw on
        point: (x, y) coordinates
        label: Text label for the point
        color: BGR color tuple
        radius: Circle radius
        thickness: Line thickness
        
    Returns:
        Modified image with point and label
    """
    x, y = point
    
    # Draw circle
    cv2.circle(image, (x, y), radius, color, thickness)
    
    # Draw label
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
    
    # Position label to the right of the point
    label_x = x + radius + 5
    label_y = y + text_height // 2
    
    # Draw label background rectangle
    cv2.rectangle(image, 
                  (label_x - 2, label_y - text_height - 2),
                  (label_x + text_width + 2, label_y + baseline + 2),
                  color, -1)  # Filled rectangle
    
    # Draw label text
    cv2.putText(image, label, (label_x, label_y), font, font_scale, (255, 255, 255), thickness)
    
    return image

def visualize_config(config_file: str, output_file: str = "config_visualization.png"):
    """
    Visualize the bot configuration by taking a screenshot and drawing labeled areas
    
    Args:
        config_file: Path to the configuration JSON file
        output_file: Output image file path
    """
    print("=== Configuration Visualization ===")
    
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Loaded configuration from {config_file}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return
    
    # Find RuneScape window
    print("Finding RuneScape window...")
    window_region = find_runescape_window()
    if not window_region:
        print("Could not find RuneScape window. Make sure RuneScape is running.")
        return
    
    window_x, window_y, window_width, window_height = window_region
    print(f"Found RuneScape window at ({window_x}, {window_y}) with size {window_width}x{window_height}")
    
    # Take screenshot
    print("Taking screenshot...")
    screenshot = jake.screenshot_utils.capture_screen_region(window_region)
    if screenshot is None:
        print("Failed to capture screenshot")
        return
    
    # Convert to BGR for OpenCV drawing
    if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
        # Already BGR
        visualization = screenshot.copy()
    else:
        # Convert from RGB to BGR
        visualization = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    
    # Define colors for different elements
    colors = {
        'health_bar': (0, 255, 0),      # Green
        'food_area': (0, 165, 255),     # Golden (BGR: 0, 165, 255 = RGB: 255, 165, 0)
        'inventory_area': (255, 0, 255), # Magenta
        'loot_area': (255, 0, 0),       # Red
        'target_area': (0, 0, 255),     # Blue
        'minimap': (255, 255, 0),       # Cyan
        'fishing_spot': (0, 255, 255),  # Yellow
        'bank': (128, 0, 128),          # Purple
        'polling': (255, 165, 0)        # Orange
    }
    
    # Draw health bar position
    if config.get('health_bar', {}).get('x') is not None:
        health_x = config['health_bar']['x']
        health_y = config['health_bar']['y']
        health_color = config['health_bar'].get('color', 'Unknown')
        
        # Convert to window-relative coordinates
        rel_x = health_x - window_x
        rel_y = health_y - window_y
        
        if 0 <= rel_x < window_width and 0 <= rel_y < window_height:
            visualization = draw_point_with_label(
                visualization, (rel_x, rel_y), 
                f"Health Bar ({health_x}, {health_y}) #{health_color}", 
                colors['health_bar']
            )
            print(f"Drew health bar at ({rel_x}, {rel_y})")
        else:
            print(f"Health bar position ({rel_x}, {rel_y}) is outside window bounds")
    
    # Draw food area
    if config.get('food_area', {}).get('enabled', False) and config['food_area'].get('coordinates'):
        food_coords = config['food_area']['coordinates']
        x1, y1, x2, y2 = food_coords
        
        # Convert to window-relative coordinates
        rel_x1 = x1 - window_x
        rel_y1 = y1 - window_y
        rel_x2 = x2 - window_x
        rel_y2 = y2 - window_y
        
        # Check if area is within window bounds
        if (0 <= rel_x1 < window_width and 0 <= rel_y1 < window_height and 
            0 <= rel_x2 < window_width and 0 <= rel_y2 < window_height):
            visualization = draw_labeled_box(
                visualization, (rel_x1, rel_y1, rel_x2, rel_y2),
                f"Food Area ({x1},{y1},{x2},{y2})", 
                colors['food_area']
            )
            print(f"Drew food area: ({rel_x1}, {rel_y1}) to ({rel_x2}, {rel_y2})")
        else:
            print(f"Food area is outside window bounds")
    
    # Draw inventory area (for burying)
    if config.get('loot_pickup', {}).get('inventory_area'):
        inv_coords = config['loot_pickup']['inventory_area']
        x1, y1, x2, y2 = inv_coords
        
        # Convert to window-relative coordinates
        rel_x1 = x1 - window_x
        rel_y1 = y1 - window_y
        rel_x2 = x2 - window_x
        rel_y2 = y2 - window_y
        
        # Check if area is within window bounds
        if (0 <= rel_x1 < window_width and 0 <= rel_y1 < window_height and 
            0 <= rel_x2 < window_width and 0 <= rel_y2 < window_height):
            bury_text = " (Bury)" if config['loot_pickup'].get('bury', False) else ""
            visualization = draw_labeled_box(
                visualization, (rel_x1, rel_y1, rel_x2, rel_y2),
                f"Inventory Area{bury_text} ({x1},{y1},{x2},{y2})", 
                colors['inventory_area']
            )
            print(f"Drew inventory area: ({rel_x1}, {rel_y1}) to ({rel_x2}, {rel_y2})")
        else:
            print(f"Inventory area is outside window bounds")
    
    # Draw loot pickup area (center + max_distance circle)
    if config.get('loot_pickup', {}).get('enabled', False):
        max_distance = config['loot_pickup'].get('max_distance', 500)
        loot_color = config['loot_pickup'].get('loot_color', 'Unknown')
        
        # Calculate center of window
        center_x = window_width // 2
        center_y = window_height // 2
        
        # Draw center point
        visualization = draw_point_with_label(
            visualization, (center_x, center_y),
            f"Loot Center ({window_x + center_x}, {window_y + center_y})", 
            colors['loot_area']
        )
        
        # Draw loot pickup radius circle
        cv2.circle(visualization, (center_x, center_y), max_distance, colors['loot_area'], 2)
        
        # Add radius label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        radius_label = f"Loot Radius: {max_distance}px (#{loot_color})"
        (text_width, text_height), baseline = cv2.getTextSize(radius_label, font, font_scale, 2)
        
        # Position label at top of circle
        label_x = center_x - text_width // 2
        label_y = center_y - max_distance - 10
        
        if label_y >= text_height + 5:  # Ensure label is visible
            # Draw label background
            cv2.rectangle(visualization, 
                          (label_x - 2, label_y - text_height - 2),
                          (label_x + text_width + 2, label_y + baseline + 2),
                          colors['loot_area'], -1)
            
            # Draw label text
            cv2.putText(visualization, radius_label, (label_x, label_y), 
                       font, font_scale, (255, 255, 255), 2)
        
        print(f"Drew loot pickup area: center ({center_x}, {center_y}), radius {max_distance}")
    
    # Draw fishing configuration
    if config.get('fishing', {}).get('enabled', False):
        fishing_config = config['fishing']
        minimap_config = fishing_config.get('minimap', {})
        
        # Draw minimap circle
        if minimap_config.get('center_x') is not None and minimap_config.get('radius') is not None:
            center_x = minimap_config['center_x']
            center_y = minimap_config['center_y']
            radius = minimap_config['radius']
            
            # Convert to window-relative coordinates
            rel_center_x = center_x - window_x
            rel_center_y = center_y - window_y
            
            if (0 <= rel_center_x < window_width and 0 <= rel_center_y < window_height):
                # Draw minimap center point
                visualization = draw_point_with_label(
                    visualization, (rel_center_x, rel_center_y),
                    f"Minimap Center ({center_x}, {center_y})", 
                    colors['minimap']
                )
                
                # Draw minimap circle
                cv2.circle(visualization, (rel_center_x, rel_center_y), int(radius), colors['minimap'], 2)
                
                # Add radius label
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                radius_label = f"Minimap Radius: {radius:.1f}px"
                (text_width, text_height), baseline = cv2.getTextSize(radius_label, font, font_scale, 2)
                
                # Position label at top of circle
                label_x = rel_center_x - text_width // 2
                label_y = rel_center_y - int(radius) - 10
                
                if label_y >= text_height + 5:  # Ensure label is visible
                    # Draw label background
                    cv2.rectangle(visualization, 
                                  (label_x - 2, label_y - text_height - 2),
                                  (label_x + text_width + 2, label_y + baseline + 2),
                                  colors['minimap'], -1)
                    
                    # Draw label text
                    cv2.putText(visualization, radius_label, (label_x, label_y), 
                               font, font_scale, (255, 255, 255), 2)
                
                print(f"Drew minimap: center ({rel_center_x}, {rel_center_y}), radius {radius:.1f}")
            else:
                print(f"Minimap center ({rel_center_x}, {rel_center_y}) is outside window bounds")
        
        # Draw fishing spot color indicator (if configured)
        if fishing_config.get('fishing_spot_color'):
            # Draw a small colored rectangle to show the fishing spot color
            color_rect_x = 10
            color_rect_y = window_height - 80
            color_rect_size = 20
            
            # Convert hex color to BGR
            hex_color = fishing_config['fishing_spot_color']
            try:
                # Remove # if present
                if hex_color.startswith('#'):
                    hex_color = hex_color[1:]
                
                # Convert hex to RGB then to BGR
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                bgr_color = (b, g, r)
                
                # Draw color rectangle
                cv2.rectangle(visualization, 
                              (color_rect_x, color_rect_y),
                              (color_rect_x + color_rect_size, color_rect_y + color_rect_size),
                              bgr_color, -1)
                
                # Draw border
                cv2.rectangle(visualization, 
                              (color_rect_x, color_rect_y),
                              (color_rect_x + color_rect_size, color_rect_y + color_rect_size),
                              colors['fishing_spot'], 2)
                
                # Add label
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                label = f"Fishing Spot: #{fishing_config['fishing_spot_color']}"
                cv2.putText(visualization, label, (color_rect_x + color_rect_size + 5, color_rect_y + 15), 
                           font, font_scale, colors['fishing_spot'], 2)
                
                print(f"Drew fishing spot color indicator: #{fishing_config['fishing_spot_color']}")
            except (ValueError, IndexError):
                print(f"Invalid fishing spot color format: {fishing_config['fishing_spot_color']}")
        
        # Draw bank color indicator (if configured)
        if fishing_config.get('bank_color'):
            # Draw a small colored rectangle to show the bank color
            color_rect_x = 10
            color_rect_y = window_height - 50
            color_rect_size = 20
            
            # Convert hex color to BGR
            hex_color = fishing_config['bank_color']
            try:
                # Remove # if present
                if hex_color.startswith('#'):
                    hex_color = hex_color[1:]
                
                # Convert hex to RGB then to BGR
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                bgr_color = (b, g, r)
                
                # Draw color rectangle
                cv2.rectangle(visualization, 
                              (color_rect_x, color_rect_y),
                              (color_rect_x + color_rect_size, color_rect_y + color_rect_size),
                              bgr_color, -1)
                
                # Draw border
                cv2.rectangle(visualization, 
                              (color_rect_x, color_rect_y),
                              (color_rect_x + color_rect_size, color_rect_y + color_rect_size),
                              colors['bank'], 2)
                
                # Add label
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                label = f"Bank: #{fishing_config['bank_color']}"
                cv2.putText(visualization, label, (color_rect_x + color_rect_size + 5, color_rect_y + 15), 
                           font, font_scale, colors['bank'], 2)
                
                print(f"Drew bank color indicator: #{fishing_config['bank_color']}")
            except (ValueError, IndexError):
                print(f"Invalid bank color format: {fishing_config['bank_color']}")
        
        # Draw polling area (if configured)
        if fishing_config.get('polling_area', {}).get('x') is not None:
            polling_x = fishing_config['polling_area']['x']
            polling_y = fishing_config['polling_area']['y']
            polling_color = fishing_config['polling_area']['color']
            
            # Convert to window-relative coordinates
            rel_polling_x = polling_x - window_x
            rel_polling_y = polling_y - window_y
            
            if (0 <= rel_polling_x < window_width and 0 <= rel_polling_y < window_height):
                # Draw polling point
                visualization = draw_point_with_label(
                    visualization, (rel_polling_x, rel_polling_y),
                    f"Polling Area ({polling_x}, {polling_y}) #{polling_color}", 
                    colors['polling']
                )
                print(f"Drew polling area: ({rel_polling_x}, {rel_polling_y})")
            else:
                print(f"Polling area ({rel_polling_x}, {rel_polling_y}) is outside window bounds")
        
        # Draw drop boxes (if configured)
        if fishing_config.get('drop_boxes'):
            for i, drop_box in enumerate(fishing_config['drop_boxes']):
                x1 = drop_box['x1']
                y1 = drop_box['y1']
                x2 = drop_box['x2']
                y2 = drop_box['y2']
                drop_color = drop_box['color']
                
                # Convert to window-relative coordinates
                rel_x1 = x1 - window_x
                rel_y1 = y1 - window_y
                rel_x2 = x2 - window_x
                rel_y2 = y2 - window_y
                
                if (0 <= rel_x1 < window_width and 0 <= rel_y1 < window_height and 
                    0 <= rel_x2 < window_width and 0 <= rel_y2 < window_height):
                    # Draw drop box rectangle
                    visualization = draw_labeled_box(
                        visualization, (rel_x1, rel_y1, rel_x2, rel_y2),
                        f"Drop Box {i+1} ({x1},{y1},{x2},{y2}) #{drop_color}", 
                        colors['polling']
                    )
                    print(f"Drew drop box {i+1}: ({rel_x1}, {rel_y1}) to ({rel_x2}, {rel_y2})")
                else:
                    print(f"Drop box {i+1} is outside window bounds")
    
    # Add configuration summary text
    summary_lines = [
        "Configuration Summary:",
        f"Human Movement: {'Enabled' if config.get('human_movement', {}).get('enabled', False) else 'Disabled'}",
        f"Auto-eating: {'Enabled' if config.get('food_area', {}).get('enabled', False) else 'Disabled'}",
        f"Loot Pickup: {'Enabled' if config.get('loot_pickup', {}).get('enabled', False) else 'Disabled'}",
        f"Fishing Bot: {'Enabled' if config.get('fishing', {}).get('enabled', False) else 'Disabled'}",
        f"Target Color: #{config.get('combat', {}).get('default_target_color', 'Unknown')}",
        f"Pixel Method: {config.get('combat', {}).get('pixel_method', 'Unknown')}"
    ]
    
    # Add fishing-specific summary if enabled
    if config.get('fishing', {}).get('enabled', False):
        fishing_config = config['fishing']
        summary_lines.extend([
            f"Travel Delay: {fishing_config.get('travel_delay', 'Unknown')}s",
            f"Fishing Delay: {fishing_config.get('fishing_delay', 'Unknown')}s"
        ])
    
    # Draw summary text at bottom-left
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    line_height = 25
    y_offset = window_height - (len(summary_lines) * line_height) - 30  # Start from bottom
    
    for i, line in enumerate(summary_lines):
        y = y_offset + i * line_height
        
        # Draw text background
        (text_width, text_height), baseline = cv2.getTextSize(line, font, font_scale, 2)
        cv2.rectangle(visualization, 
                      (10 - 2, y - text_height - 2),
                      (10 + text_width + 2, y + baseline + 2),
                      (0, 0, 0), -1)  # Black background
        
        # Draw text
        cv2.putText(visualization, line, (10, y), font, font_scale, (255, 255, 255), 2)
    
    # Save the visualization
    try:
        cv2.imwrite(output_file, visualization)
        print(f"\nConfiguration visualization saved to: {output_file}")
        print(f"Window region: ({window_x}, {window_y}, {window_width}, {window_height})")
        
        # Show legend
        print("\nLegend:")
        print("Green dot: Health bar position")
        print("Yellow box: Food area")
        print("Magenta box: Inventory area (for burying)")
        print("Red circle: Loot pickup area")
        print("Blue: Target color area (not drawn)")
        print("Cyan circle: Minimap area (fishing)")
        print("Yellow rectangle: Fishing spot color indicator")
        print("Purple rectangle: Bank color indicator")
        print("Orange rectangles: Drop boxes (fishing completion areas)")
        
    except Exception as e:
        print(f"Error saving visualization: {e}")

def main():
    """Main function to run the visualization script."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_config.py <config_file> [output_file]")
        print("Example: python visualize_config.py bot_config.json config_viz.png")
        return
    
    config_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "config_visualization.png"
    
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}")
        return
    
    visualize_config(config_file, output_file)

if __name__ == "__main__":
    main() 