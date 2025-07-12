import numpy as np
import random
from scipy.ndimage import label, binary_dilation
from typing import List, Tuple, Optional, Union
import cv2
import color_utils

def random_pixel_select(screenshot: np.ndarray, target_hex: str, tolerance: int = 10) -> Optional[Tuple[int, int]]:
    """
    Original random pixel selection method
    
    Args:
        screenshot: OpenCV image array (BGR format)
        target_hex: Target hex color to find
        tolerance: Color tolerance for matching
        
    Returns:
        Random (x, y) coordinate of matching pixel, or None if no pixels found
    """
    pixel_coords = color_utils.find_pixels_by_color(screenshot, target_hex, tolerance)
    
    if not pixel_coords:
        print(f"No pixels found with color {target_hex}")
        return None
    
    # Select a random pixel
    random_pixel = random.choice(pixel_coords)
    return random_pixel

def smart_pixel_select(screenshot: np.ndarray, target_hex: str, tolerance: int = 10, return_debug: bool = False, downsample_factor: int = 4, center_falloff: float = 4.0):
    """
    Smart pixel selection using blob detection and green exclusion
    
    Args:
        screenshot: OpenCV image array (BGR format)
        target_hex: Target hex color to find (e.g., "00FFFFFA" for blue)
        tolerance: Color tolerance for matching
        return_debug: If True, returns additional debug information
        downsample_factor: Factor to downsample image for faster processing (1 = no downsampling)
        
    Returns:
        If return_debug=False: Random (x, y) coordinate from filtered blobs, or None if no valid blobs found
        If return_debug=True: Tuple of (selected_pixel, labeled_blobs, filtered_target_mask) or (None, None, None)
    """
    print("Smart pixel selection")
    
    # Downsample the image for faster processing
    if downsample_factor > 1:
        original_shape = screenshot.shape
        print(f"Downsampling from {original_shape[1]}x{original_shape[0]} to {original_shape[1]//downsample_factor}x{original_shape[0]//downsample_factor}")
        downsampled_screenshot = cv2.resize(screenshot, (screenshot.shape[1]//downsample_factor, screenshot.shape[0]//downsample_factor), interpolation=cv2.INTER_AREA)
    else:
        downsampled_screenshot = screenshot
    
    # Convert BGR to RGB (OpenCV uses BGR)
    rgb_screen = cv2.cvtColor(downsampled_screenshot, cv2.COLOR_BGR2RGB)
    
    # Get target RGB color
    target_rgb = color_utils.hex_to_rgb(target_hex)
    
    # Extract RGB channels
    r, g, b = rgb_screen[:, :, 0], rgb_screen[:, :, 1], rgb_screen[:, :, 2]
    
    color_distance = color_utils.calculate_color_distance(rgb_screen, target_rgb)
    target_mask = color_distance <= tolerance
    green_mask = (g > 200) & (r < 20) & (b < 20)
    
    # Label connected components in the target mask
    structure = np.ones((3, 3), dtype=np.uint8)  # 8-connectivity
    labeled_blobs, num_blobs = label(target_mask, structure=structure)
    
    # exclude blobs with less than minimum pixels (adjusted for downsampling)
    blob_counts = np.bincount(labeled_blobs.flatten())
    min_pixels = 1000 // (downsample_factor ** 2)  # Scale minimum pixels by downsampling factor
    # print("blob counts: ", blob_counts)
    # print(f"min_pixels threshold: {min_pixels} (adjusted for {downsample_factor}x downsampling)")
    
    # Create a mapping to reindex blobs (0 = background, 1+ = valid blobs)
    valid_blob_indices = []
    new_label = 1
    
    for old_label in range(1, len(blob_counts)):
        if blob_counts[old_label] >= min_pixels:
            valid_blob_indices.append((old_label, new_label))
            new_label += 1
    
    # Create new labeled image with reindexed blobs
    new_labeled_blobs = np.zeros_like(labeled_blobs)
    for old_label, new_label in valid_blob_indices:
        new_labeled_blobs[labeled_blobs == old_label] = new_label
    
    labeled_blobs = new_labeled_blobs
    num_blobs = len(valid_blob_indices)
    
    print(f"Found {num_blobs} candidate targets")
    
    # Output mask with only isolated target blobs (not touching green)
    filtered_target_mask = np.zeros_like(target_mask, dtype=bool)

    num_valid_blobs = 0
    
    for i in range(1, num_blobs + 1):
        blob_mask = (labeled_blobs == i)
        
        # Dilate blob to get neighbors
        dilation_structure = np.ones((5, 5), dtype=np.uint8)
        dilated_blob = binary_dilation(blob_mask, structure=dilation_structure)

        # save dilated_blob as image
        # dilated_blob_image = dilated_blob * 255
        # cv2.imwrite(f"dilated_blob_{i}.png", dilated_blob_image)
        
        # Exclude original blob area — just look at its border
        border_mask = dilated_blob & ~blob_mask

        # save border_mask as image
        # border_mask_image = border_mask * 255
        # cv2.imwrite(f"border_mask_{i}.png", border_mask_image)
        
        # Check if green is in the border
        if not np.any(green_mask & border_mask):
            filtered_target_mask |= blob_mask
            # print(f"Blob {i}: Valid (no green neighbors)")
            num_valid_blobs += 1
        else:
            # print(f"Blob {i}: Excluded (has green neighbors)")
            pass
    
    print(f"Found {num_valid_blobs} valid targets")
    
    # Find coordinates of filtered pixels
    filtered_pixels = np.where(filtered_target_mask)
    if len(filtered_pixels[0]) == 0:
        print("No valid blobs found (all had green neighbors)")
        if return_debug:
            return None, labeled_blobs, filtered_target_mask
        return None
    
    # Convert to list of (x, y) coordinates
    pixel_coords = list(zip(filtered_pixels[1], filtered_pixels[0]))  # x, y
    x_coords = filtered_pixels[1]
    y_coords = filtered_pixels[0]
    
    # print(f"Found {len(pixel_coords)} valid pixels from {num_blobs} blobs")
    
    # Calculate center and dimensions of the image
    center_x = rgb_screen.shape[1] // 2
    center_y = rgb_screen.shape[0] // 2
    width = rgb_screen.shape[1]
    height = rgb_screen.shape[0]
    
    # Calculate distance-based probabilities (vectorized)
    if len(pixel_coords) > 0:
        
        # Calculate normalized distances from center (vectorized)
        normalized_x = (x_coords - center_x) / width
        normalized_y = (y_coords - center_y) / height
        distances = np.sqrt(normalized_x ** 2 + normalized_y ** 2)
        
        # Calculate probabilities using exponential decay (vectorized)
        probabilities = np.exp(-distances * center_falloff)
        
        # Normalize probabilities
        total_prob = np.sum(probabilities)
        if total_prob > 0:
            probabilities = probabilities / total_prob
        else:
            # Fallback to uniform if all probabilities are zero
            probabilities = np.ones(len(pixel_coords)) / len(pixel_coords)

        # Select pixel based on weighted probability
        selected_pixel = random.choices(pixel_coords, weights=probabilities.tolist(), k=1)[0]
    else:
        selected_pixel = None
    
    # Debug visualization of probability distribution
    if return_debug and selected_pixel is not None:

        # normalize probabilities to 0-1
        probabilities = (probabilities - np.min(probabilities)) / (np.max(probabilities) - np.min(probabilities))
        
        # Create probability heatmap
        prob_heatmap = np.zeros_like(filtered_target_mask, dtype=np.float32)
        for i, (x, y) in enumerate(pixel_coords):
            prob_heatmap[y, x] = probabilities[i]
        
        # Apply colormap for visualization
        prob_heatmap_normalized = (prob_heatmap * 255).astype(np.uint8)
        prob_heatmap_colored = cv2.applyColorMap(prob_heatmap_normalized, cv2.COLORMAP_JET)
        
        # Add center marker
        cv2.circle(prob_heatmap_colored, (center_x, center_y), 5, (255, 255, 255), -1)  # White center
        cv2.circle(prob_heatmap_colored, (center_x, center_y), 3, (0, 0, 0), -1)  # Black dot
        
        # Add selected pixel marker
        cv2.circle(prob_heatmap_colored, selected_pixel, 8, (0, 255, 0), 2)  # Green circle
        
        # Save probability heatmap
        cv2.imwrite("debug_screenshots/probability_heatmap.png", prob_heatmap_colored)
        print(f"Probability heatmap saved to debug_screenshots/probability_heatmap.png")
        if selected_pixel in pixel_coords:
            pixel_index = pixel_coords.index(selected_pixel)
            print(f"Selected pixel at {selected_pixel} with probability {probabilities[pixel_index]:.4f}")
    
    random_pixel = selected_pixel
    
    # Upsample coordinates back to original resolution
    if downsample_factor > 1:
        original_x = random_pixel[0] * downsample_factor + downsample_factor // 2  # Center of the downsampled pixel
        original_y = random_pixel[1] * downsample_factor + downsample_factor // 2
        random_pixel = (original_x, original_y)
        # print(f"Upsampled coordinates from {random_pixel[0]//downsample_factor},{random_pixel[1]//downsample_factor} to {original_x},{original_y}")
    
    if return_debug:
        # Upsample debug images back to original resolution
        if downsample_factor > 1:
            upsampled_labeled_blobs = cv2.resize(labeled_blobs.astype(np.uint8), (screenshot.shape[1], screenshot.shape[0]), interpolation=cv2.INTER_NEAREST)
            upsampled_filtered_mask = cv2.resize(filtered_target_mask.astype(np.uint8), (screenshot.shape[1], screenshot.shape[0]), interpolation=cv2.INTER_NEAREST)
            # Also upsample probability heatmap if it exists
            if 'prob_heatmap' in locals():
                upsampled_prob_heatmap = cv2.resize(prob_heatmap, (screenshot.shape[1], screenshot.shape[0]), interpolation=cv2.INTER_LINEAR)
                return random_pixel, upsampled_labeled_blobs, upsampled_filtered_mask.astype(bool), upsampled_prob_heatmap
            else:
                return random_pixel, upsampled_labeled_blobs, upsampled_filtered_mask.astype(bool)
        else:
            # Return probability heatmap if it exists
            if 'prob_heatmap' in locals():
                return random_pixel, labeled_blobs, filtered_target_mask, prob_heatmap
            else:
                return random_pixel, labeled_blobs, filtered_target_mask
    return random_pixel
 
def select_pixel(screenshot: np.ndarray, target_hex: str, tolerance: int = 1, 
                method: str = "smart") -> Optional[Tuple[int, int]]:
    """
    Main pixel selection function with method choice
    
    Args:
        screenshot: OpenCV image array (BGR format)
        target_hex: Target hex color to find
        tolerance: Color tolerance for matching
        method: "random" or "smart"
        
    Returns:
        Selected (x, y) coordinate, or None if no pixels found
    """
    if method == "random":
        return random_pixel_select(screenshot, target_hex, tolerance)
    elif method == "smart":
        return smart_pixel_select(screenshot, target_hex, tolerance)
    else:
        print(f"Unknown selection method: {method}. Using 'smart'")
        return smart_pixel_select(screenshot, target_hex, tolerance)

# Example usage
if __name__ == "__main__":
    print("Pixel Selection Test")
    
    # This would be used with actual screenshot data
    # For testing, we'd need to capture a real screenshot
    print("Import this module to use pixel selection functions")
    print("Available functions:")
    print("- random_pixel_select(): Original random selection")
    print("- smart_pixel_select(): Blob-based selection with green exclusion")
    print("- select_pixel(): Main function with method choice") 