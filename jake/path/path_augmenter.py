import numpy as np
import os
from math import cos, sin, radians

def rotate_point(x, y, angle_degrees):
    """
    Rotate a point (x, y) around the origin by the given angle in degrees.
    
    Args:
        x, y: Coordinates of the point
        angle_degrees: Rotation angle in degrees (positive = counterclockwise)
    
    Returns:
        tuple: (new_x, new_y) coordinates after rotation
    """
    angle_rad = radians(angle_degrees)
    cos_a = cos(angle_rad)
    sin_a = sin(angle_rad)
    
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    return (new_x, new_y)

def rotate_path(path, angle_degrees):
    """
    Rotate an entire path around the origin by the given angle.
    
    Args:
        path: List of (x, y) coordinate tuples
        angle_degrees: Rotation angle in degrees
    
    Returns:
        list: New path with rotated coordinates
    """
    rotated_path = []
    for x, y in path:
        new_x, new_y = rotate_point(x, y, angle_degrees)
        rotated_path.append((new_x, new_y))
    
    return rotated_path

def augment_mouse_paths(input_file="mouse_paths.npy", output_file="mouse_paths_augmented.npy", 
                       rotation_angles=[90, 180, 270]):
    """
    Augment mouse paths by rotating each path around the origin.
    
    Args:
        input_file: Path to the input mouse paths file
        output_file: Path to save the augmented mouse paths
        rotation_angles: List of rotation angles in degrees (default: 90, 180, 270)
                        This will create 4 total variations (original + 3 rotations)
    
    Returns:
        int: Total number of paths after augmentation
    """
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return 0
    
    # Load the original mouse paths
    print(f"Loading mouse paths from {input_file}...")
    original_paths = np.load(input_file, allow_pickle=True)
    print(f"Loaded {len(original_paths)} original paths")
    
    # Initialize augmented paths list with original paths
    augmented_paths = list(original_paths)
    
    # Add rotated versions of each path
    for angle in rotation_angles:
        print(f"Creating {angle}° rotations...")
        for i, path in enumerate(original_paths):
            if len(path) > 0:  # Only rotate non-empty paths
                rotated_path = rotate_path(path, angle)
                augmented_paths.append(rotated_path)
    
    # Convert to numpy array and save
    augmented_array = np.array(augmented_paths, dtype=object)
    np.save(output_file, augmented_array)
    
    total_paths = len(augmented_paths)
    print(f"Augmentation complete!")
    print(f"Original paths: {len(original_paths)}")
    print(f"Augmented paths: {total_paths}")
    print(f"Augmentation factor: {total_paths / len(original_paths):.1f}x")
    print(f"Saved to {output_file}")
    
    return total_paths

def visualize_augmentation_sample(input_file="mouse_paths.npy", output_file="mouse_paths_augmented.npy"):
    """
    Create a sample visualization to show the augmentation effect.
    This function creates a simple plot showing original and augmented paths.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        import matplotlib.colors as mcolors
        
        # Load original and augmented paths
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found!")
            return
        
        if not os.path.exists(output_file):
            print(f"Error: {output_file} not found! Run augmentation first.")
            return
        
        original_paths = np.load(input_file, allow_pickle=True)
        augmented_paths = np.load(output_file, allow_pickle=True)
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot original paths
        ax1.set_title("Original Paths", fontsize=14, fontweight='bold')
        ax1.set_xlabel("X Offset (pixels)")
        ax1.set_ylabel("Y Offset (pixels)")
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')
        
        # Plot first few original paths in different colors
        colors = plt.cm.Set1(np.linspace(0, 1, min(5, len(original_paths))))
        for i, path in enumerate(original_paths[:5]):
            if len(path) >= 2:
                path_array = np.array(path)
                ax1.plot(path_array[:, 0], path_array[:, 1], 
                        color=colors[i], linewidth=2, alpha=0.8, 
                        label=f'Path {i+1}')
        
        ax1.legend()
        
        # Plot augmented paths
        ax2.set_title("Augmented Paths (with rotations)", fontsize=14, fontweight='bold')
        ax2.set_xlabel("X Offset (pixels)")
        ax2.set_ylabel("Y Offset (pixels)")
        ax2.grid(True, alpha=0.3)
        ax2.set_aspect('equal')
        
        # Plot first original path and its rotations
        if len(original_paths) > 0:
            original_path = original_paths[0]
            if len(original_path) >= 2:
                # Original path
                path_array = np.array(original_path)
                ax2.plot(path_array[:, 0], path_array[:, 1], 
                        color='blue', linewidth=3, alpha=0.8, 
                        label='Original')
                
                # Rotated versions
                rotation_angles = [90, 180, 270]
                colors_rot = ['red', 'green', 'orange']
                
                for i, (angle, color) in enumerate(zip(rotation_angles, colors_rot)):
                    rotated_path = rotate_path(original_path, angle)
                    if len(rotated_path) >= 2:
                        rot_array = np.array(rotated_path)
                        ax2.plot(rot_array[:, 0], rot_array[:, 1], 
                                color=color, linewidth=2, alpha=0.7, 
                                label=f'{angle}° rotation')
        
        ax2.legend()
        
        # Set consistent limits
        all_points_orig = np.vstack([np.array(path) for path in original_paths if len(path) > 0])
        all_points_aug = np.vstack([np.array(path) for path in augmented_paths if len(path) > 0])
        
        if len(all_points_orig) > 0 and len(all_points_aug) > 0:
            all_points = np.vstack([all_points_orig, all_points_aug])
            x_min, y_min = all_points.min(axis=0)
            x_max, y_max = all_points.max(axis=0)
            padding = max(x_max - x_min, y_max - y_min) * 0.1
            
            ax1.set_xlim(x_min - padding, x_max + padding)
            ax1.set_ylim(y_min - padding, y_max + padding)
            ax2.set_xlim(x_min - padding, x_max + padding)
            ax2.set_ylim(y_min - padding, y_max + padding)
        
        plt.tight_layout()
        plt.savefig("augmentation_sample.png", dpi=300, bbox_inches='tight')
        print("Sample visualization saved as augmentation_sample.png")
        plt.show()
        
    except ImportError:
        print("Matplotlib not available. Skipping visualization.")

def main():
    """Main function to run path augmentation."""
    print("Mouse Path Augmenter")
    print("=" * 30)
    
    # Check if input file exists
    if not os.path.exists("mouse_paths.npy"):
        print("Error: mouse_paths.npy not found!")
        print("Please run data_collection.py first to record some mouse paths.")
        return
    
    # Run augmentation
    print("Starting path augmentation...")

    # 8 rotations
    rotation_angles = [45, 90, 135, 180, 225, 270, 315]
    # 16 rotations from 0 to 360, excluding 0
    rotation_angles = list(range(24, 360, 24))
    print(rotation_angles)
    total_paths = augment_mouse_paths(rotation_angles=rotation_angles)
    
    if total_paths > 0:
        print(f"\nAugmentation successful! Created {total_paths} total paths.")
        
        # Create sample visualization
        print("\nCreating sample visualization...")
        visualize_augmentation_sample()
        
        print(f"\nFiles created:")
        print(f"- mouse_paths_augmented.npy (augmented data)")
        print(f"- augmentation_sample.png (visualization sample)")
        
        print(f"\nYou can now use the augmented data with your visualization script:")
        print(f"python path_visualizer.py")
        print(f"# Or specify the augmented file:")
        print(f"# from path_visualizer import visualize_mouse_paths")
        print(f"# visualize_mouse_paths('mouse_paths_augmented.npy', 'augmented_visualization.png')")

if __name__ == "__main__":
    main() 