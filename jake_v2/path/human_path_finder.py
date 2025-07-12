import numpy as np
import os
from scipy.spatial import KDTree
import time
import pyautogui
from typing import List, Tuple, Optional

class HumanPath:
    """
    A class that finds and executes human-like mouse paths based on displacement.
    Uses kd-tree to efficiently find the closest path for a given displacement.
    """
    
    def __init__(self, paths_file: str = "mouse_paths_augmented.npy", 
                 sample_rate: int = 50, smoothing: bool = True):
        """
        Initialize the HumanPath finder.
        
        Args:
            paths_file: Path to the .npy file containing mouse paths
            sample_rate: How many points per second to move (default: 50)
            smoothing: Whether to apply smoothing to the path (default: True)
        """
        self.sample_rate = sample_rate
        self.smoothing = smoothing
        self.paths = []
        self.displacements = []
        self.kd_tree = None
        
        # Load and process paths
        self._load_paths(paths_file)
        self._build_kd_tree()
        
        print(f"HumanPath initialized with {len(self.paths)} paths")
        print(f"Displacement range: {self._get_displacement_stats()}")
    
    def _load_paths(self, paths_file: str):
        """Load mouse paths from file and calculate their final displacements."""
        if not os.path.exists(paths_file):
            raise FileNotFoundError(f"Paths file not found: {paths_file}")
        
        print(f"Loading paths from {paths_file}...")
        loaded_paths = np.load(paths_file, allow_pickle=True)
        
        for path in loaded_paths:
            if len(path) >= 2:  # Only use paths with at least 2 points
                # Calculate final displacement (end point - start point)
                start_x, start_y = path[0]
                end_x, end_y = path[-1]
                displacement = (end_x - start_x, end_y - start_y)
                
                # Store path and its displacement
                self.paths.append(path)
                self.displacements.append(displacement)
        
        print(f"Loaded {len(self.paths)} valid paths")
    
    def _build_kd_tree(self):
        """Build kd-tree from displacement vectors for efficient nearest neighbor search."""
        if not self.displacements:
            raise ValueError("No displacements available to build kd-tree")
        
        # Convert displacements to numpy array
        displacement_array = np.array(self.displacements)
        self.kd_tree = KDTree(displacement_array)
        
        print("KD-tree built successfully")
    
    def _get_displacement_stats(self) -> str:
        """Get statistics about the displacement range."""
        if not self.displacements:
            return "No displacements"
        
        disp_array = np.array(self.displacements)
        min_disp = disp_array.min(axis=0)
        max_disp = disp_array.max(axis=0)
        mean_disp = disp_array.mean(axis=0)
        
        return f"X: {min_disp[0]:.1f} to {max_disp[0]:.1f} (mean: {mean_disp[0]:.1f}), " \
               f"Y: {min_disp[1]:.1f} to {max_disp[1]:.1f} (mean: {mean_disp[1]:.1f})"
    
    def _smooth_path(self, path: List[Tuple[float, float]], 
                    window_size: int = 3) -> List[Tuple[float, float]]:
        """Apply simple moving average smoothing to the path."""
        if len(path) < window_size:
            return path
        
        smoothed_path = []
        half_window = window_size // 2
        
        for i in range(len(path)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(path), i + half_window + 1)
            
            # Calculate average of window
            window_points = path[start_idx:end_idx]
            avg_x = sum(p[0] for p in window_points) / len(window_points)
            avg_y = sum(p[1] for p in window_points) / len(window_points)
            
            smoothed_path.append((avg_x, avg_y))
        
        return smoothed_path
    
    def find_closest_path(self, target_displacement: Tuple[float, float], 
                         k: int = 1) -> Tuple[int, float]:
        """
        Find the closest path for a given displacement.
        
        Args:
            target_displacement: (dx, dy) displacement vector
            k: Number of nearest neighbors to return (default: 1)
        
        Returns:
            Tuple of (path_index, distance) for the closest path
        """
        if self.kd_tree is None:
            raise ValueError("KD-tree not built")
        
        # Time the KD-tree lookup
        # start_time = time.time()
        
        # Query the kd-tree
        distances, indices = self.kd_tree.query([target_displacement], k=k)
        
        # Calculate lookup time
        # lookup_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        # print(f"KD-tree lookup: {lookup_time:.3f}ms for displacement {target_displacement}")
        
        if k == 1:
            return indices[0], distances[0]
        else:
            return indices[0], distances[0]
    
    def get_path_for_displacement(self, target_displacement: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Get the best path for a given displacement.
        
        Args:
            target_displacement: (dx, dy) displacement vector
        
        Returns:
            List of (x, y) coordinates forming the path
        """
        path_idx, distance = self.find_closest_path(target_displacement)
        path = self.paths[path_idx]
        
        if self.smoothing:
            path = self._smooth_path(path)
        
        return path
    
    def move_mouse_to_target(self, start_pos: Tuple[int, int], 
                           target_pos: Tuple[int, int], 
                           visualize: bool = False) -> List[Tuple[int, int]]:
        """
        Move mouse from start position to target position using human-like path.
        
        Args:
            start_pos: Starting (x, y) screen coordinates
            target_pos: Target (x, y) screen coordinates
            visualize: Whether to return path for visualization
        
        Returns:
            List of (x, y) coordinates that were visited during movement
        """
        # Calculate displacement
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        displacement = (dx, dy)
        
        # Find the best path for this displacement
        path = self.get_path_for_displacement(displacement)
        
        # Transform path from relative coordinates to absolute screen coordinates
        absolute_path = []
        for rel_x, rel_y in path:
            abs_x = int(start_pos[0] + rel_x)
            abs_y = int(start_pos[1] + rel_y)
            absolute_path.append((abs_x, abs_y))
        
        # Execute the mouse movement
        if not visualize:
            self._execute_path(absolute_path)
        
        return absolute_path
    
    def _execute_path(self, path: List[Tuple[int, int]]):
        """Execute the mouse movement along the given path."""
        print(f"Executing path: {path}")
        if not path:
            return
        
        # Move to first position
        pyautogui.moveTo(path[0][0], path[0][1], duration=0.01)
        
        # Move through the rest of the path
        for x, y in path[1:]:
            pyautogui.moveTo(x, y, duration=0.01)
            time.sleep(1.0 / self.sample_rate)
    
    def get_path_info(self, displacement: Tuple[float, float]) -> dict:
        """
        Get detailed information about the path for a given displacement.
        
        Args:
            displacement: (dx, dy) displacement vector
        
        Returns:
            Dictionary with path information
        """
        path_idx, distance = self.find_closest_path(displacement)
        path = self.paths[path_idx]
        
        # Calculate path statistics
        path_length = 0
        for i in range(1, len(path)):
            dx = path[i][0] - path[i-1][0]
            dy = path[i][1] - path[i-1][1]
            path_length += np.sqrt(dx*dx + dy*dy)
        
        return {
            'path_index': path_idx,
            'distance': distance,
            'path_length': path_length,
            'num_points': len(path),
            'actual_displacement': self.displacements[path_idx],
            'target_displacement': displacement
        }

def test_human_path():
    """Test function to demonstrate HumanPath usage."""
    try:
        # Initialize HumanPath
        human_path = HumanPath()
        
        # Test finding paths for different displacements
        test_displacements = [
            (100, 100),
            (-50, 200),
            (300, -150),
            (0, 100),
            (100, 0)
        ]
        
        print("\nTesting path finding:")
        for disp in test_displacements:
            info = human_path.get_path_info(disp)
            print(f"Displacement {disp}: Path {info['path_index']} "
                  f"(distance: {info['distance']:.2f}, length: {info['path_length']:.1f})")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_human_path() 