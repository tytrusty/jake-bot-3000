import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
import os

def calculate_path_length(path):
    """Calculate the total length of a path."""
    if len(path) < 2:
        return 0
    
    total_length = 0
    for i in range(1, len(path)):
        dx = path[i][0] - path[i-1][0]
        dy = path[i][1] - path[i-1][1]
        total_length += np.sqrt(dx*dx + dy*dy)
    
    return total_length

def visualize_mouse_paths(file_path="mouse_paths.npy", output_file="mouse_paths_visualization.png", plot_final_positions_only=False):
    """
    Visualize mouse paths with color coding based on path length.
    Paths are ordered from longest to shortest for better visualization.
    
    Args:
        file_path: Path to the .npy file containing mouse paths
        output_file: Output filename for the visualization
        plot_final_positions_only: If True, only plot the final positions of paths
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return
    
    # Load the mouse paths
    print(f"Loading mouse paths from {file_path}...")
    paths = np.load(file_path, allow_pickle=True)
    print(f"Loaded {len(paths)} paths")
    
    # Calculate path lengths and sort by length (descending)
    path_lengths = []
    for path in paths:
        length = calculate_path_length(path)
        path_lengths.append(length)
    
    # Sort paths by length (descending order)
    sorted_indices = np.argsort(path_lengths)[::-1]
    sorted_paths = [paths[i] for i in sorted_indices]
    sorted_lengths = [path_lengths[i] for i in sorted_indices]
    
    print(f"Path lengths range: {min(path_lengths):.2f} to {max(path_lengths):.2f}")
    
    # Create the visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Set up color mapping
    min_length = min(path_lengths)
    max_length = max(path_lengths)
    
    # Create a colormap (viridis for good color perception)
    cmap = plt.cm.viridis
    norm = mcolors.Normalize(vmin=min_length, vmax=max_length)
    
    # Plot paths or final positions
    if plot_final_positions_only:
        # Plot only final positions as colored points
        final_positions = []
        final_lengths = []
        
        for path, length in zip(sorted_paths, sorted_lengths):
            if len(path) >= 1:
                final_positions.append(path[-1])  # Last position
                final_lengths.append(length)
        
        if final_positions:
            final_positions = np.array(final_positions)
            colors = [cmap(norm(length)) for length in final_lengths]
            
            # Plot final positions as scatter points
            scatter = ax.scatter(final_positions[:, 0], final_positions[:, 1], 
                               c=final_lengths, cmap=cmap, s=30, alpha=0.8, 
                               edgecolors='white', linewidth=0.5)
            
            print(f"Plotted {len(final_positions)} final positions")
    else:
        # Plot full paths
        for i, (path, length) in enumerate(zip(sorted_paths, sorted_lengths)):
            if len(path) < 2:
                continue
                
            # Convert path to numpy array for easier handling
            path_array = np.array(path)
            
            # Create line segments
            segments = []
            for j in range(len(path_array) - 1):
                segments.append([path_array[j], path_array[j + 1]])
            
            # Create line collection with color based on length
            color = cmap(norm(length))
            lc = LineCollection(segments, color=color, alpha=0.7, linewidth=1.5)
            ax.add_collection(lc)
    
    # Set up the plot
    ax.set_xlabel('X Offset (pixels)', fontsize=12)
    ax.set_ylabel('Y Offset (pixels)', fontsize=12)
    
    if plot_final_positions_only:
        title = 'Mouse Path Final Positions\n(Colored by Path Length)'
    else:
        title = 'Mouse Paths Visualization\n(Colored by Length, Longest to Shortest)'
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add a colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
    cbar.set_label('Path Length (pixels)', fontsize=10)
    
    # Set equal aspect ratio and grid
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Auto-adjust limits based on data
    all_points = np.vstack([np.array(path) for path in paths if len(path) > 0])
    if len(all_points) > 0:
        x_min, y_min = all_points.min(axis=0)
        x_max, y_max = all_points.max(axis=0)
        
        # Add some padding
        padding = max(x_max - x_min, y_max - y_min) * 0.1
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)
    
    # Add statistics text
    stats_text = f"Total Paths: {len(paths)}\n"
    stats_text += f"Average Length: {np.mean(path_lengths):.1f} pixels\n"
    stats_text += f"Max Length: {max_length:.1f} pixels\n"
    stats_text += f"Min Length: {min_length:.1f} pixels"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=10)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved as {output_file}")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    # Create static visualization
    # print("Creating static visualization...")
    # visualize_mouse_paths(file_path="mouse_paths_augmented.npy", output_file="mouse_paths_visualization.png")
    
    # Create final positions visualization
    print("\nCreating final positions visualization...")
    visualize_mouse_paths(file_path="mouse_paths_augmented.npy", 
                         output_file="mouse_paths_final_positions.png", 
                         plot_final_positions_only=True) 