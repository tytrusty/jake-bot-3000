import numpy as np
import os
from scipy.spatial import KDTree
import time
import pyautogui
import random
from typing import List, Tuple, Optional

class HumanPath:
    """
    A class that finds and executes human-like mouse paths based on displacement.
    Uses kd-tree to efficiently find the closest path for a given displacement.
    """
    
    def __init__(self, paths_file: str = "mouse_paths_augmented.npy", 
                 sample_rate: int = 50, smoothing: bool = True,
                 use_random_selection: bool = True, k: int = 8,
                 use_iterative_movement: bool = True, max_iterations: int = 5,
                 tolerance: float = 10.0, speed_range: Tuple[float, float] = (0.5, 3.0)):
        """
        Initialize the HumanPath finder.
        
        Args:
            paths_file: Path to the .npy file containing mouse paths
            sample_rate: How many points per second to move (default: 50)
            smoothing: Whether to apply smoothing to the path (default: True)
            use_random_selection: Whether to randomly select from k nearest neighbors (default: True)
            k: Number of nearest neighbors to consider when using random selection (default: 8)
            use_iterative_movement: Whether to use iterative movement for better accuracy (default: True)
            max_iterations: Maximum number of movement iterations (default: 5)
            tolerance: Distance tolerance in pixels for iterative movement (default: 10.0)
            speed_range: Tuple of (min_speed, max_speed) multipliers for random speed variation (default: (0.5, 3.0))
        """
        self.sample_rate = sample_rate
        self.smoothing = smoothing
        self.use_random_selection = use_random_selection
        self.k = k
        self.use_iterative_movement = use_iterative_movement
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.speed_range = speed_range
        
        self.paths = []
        self.displacements = []
        self.kd_tree = None
        
        # Cache for storing selected paths to avoid recalculation
        self.path_cache = {}  # Maps displacement -> (path_idx, distance, k)
        
        # Load and process paths
        self._load_paths(paths_file)
        self._build_kd_tree()
        
        print(f"HumanPath initialized with {len(self.paths)} paths")
        print(f"Displacement range: {self._get_displacement_stats()}")
        print(f"Random selection: {use_random_selection}, k: {k}")
        print(f"Iterative movement: {use_iterative_movement}, max_iterations: {max_iterations}, tolerance: {tolerance}")
        print(f"Speed range: {speed_range[0]:.1f}x to {speed_range[1]:.1f}x base speed")
    
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
    
    def find_k_nearest_paths(self, target_displacement: Tuple[float, float], 
                           k: int = 8) -> List[Tuple[int, float]]:
        """
        Find the k nearest paths for a given displacement.
        
        Args:
            target_displacement: (dx, dy) displacement vector
            k: Number of nearest neighbors to return (default: 8)
        
        Returns:
            List of tuples (path_index, distance) for the k nearest paths
        """
        if self.kd_tree is None:
            raise ValueError("KD-tree not built")
        
        # Query the kd-tree
        distances, indices = self.kd_tree.query([target_displacement], k=k)
        
        # Return list of (index, distance) tuples
        return list(zip(indices[0], distances[0]))
    
    def select_random_path_from_k_nearest(self, target_displacement: Tuple[float, float], 
                                        k: int = 8) -> Tuple[int, float]:
        """
        Find k nearest paths and randomly select one of them.
        
        Args:
            target_displacement: (dx, dy) displacement vector
            k: Number of nearest neighbors to consider (default: 8)
        
        Returns:
            Tuple of (path_index, distance) for the randomly selected path
        """
        k_nearest = self.find_k_nearest_paths(target_displacement, k)
        return random.choice(k_nearest)
    
    def get_path_for_displacement(self, target_displacement: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Get a path for a given displacement.
        
        Args:
            target_displacement: (dx, dy) displacement vector
        
        Returns:
            List of (x, y) coordinates forming the path
        """
        if self.use_random_selection:
            path_idx, distance = self.select_random_path_from_k_nearest(target_displacement, self.k)
        else:
            path_idx, distance = self.find_closest_path(target_displacement)
        
        path = self.paths[path_idx]
        # print(f'Path: {path}')
        # print(f"path idx: {path_idx}")
        # print(f"distance: {distance}")
        
        if self.smoothing:
            path = self._smooth_path(path)
        
        return path
    
    def move_mouse_to_target(self, start_pos: Tuple[int, int], 
                           target_pos: Tuple[int, int], 
                           visualize: bool = False) -> List[Tuple[int, int]]:
        """
        Move mouse from start position to target position using human-like path.
        If iterative movement is enabled, builds a complete path by combining multiple smaller paths.
        
        Args:
            start_pos: Starting (x, y) screen coordinates
            target_pos: Target (x, y) screen coordinates
            visualize: Whether to return path for visualization
        
        Returns:
            List of (x, y) coordinates that were visited during movement
        """
        if self.use_iterative_movement:
            return self._build_iterative_path(start_pos, target_pos, visualize)
        else:
            return self._build_single_path(start_pos, target_pos, visualize)
    
    def _build_single_path(self, start_pos: Tuple[int, int], 
                          target_pos: Tuple[int, int], 
                          visualize: bool = False) -> List[Tuple[int, int]]:
        """
        Build a single path from start to target position.
        
        Args:
            start_pos: Starting (x, y) screen coordinates
            target_pos: Target (x, y) screen coordinates
            visualize: Whether to return path for visualization
        
        Returns:
            List of (x, y) coordinates forming the path
        """
        # Calculate displacement
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        displacement = (dx, dy)
        
        # Find a path for this displacement
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
    
    def _build_iterative_path(self, start_pos: Tuple[int, int], 
                             target_pos: Tuple[int, int], 
                             visualize: bool = False) -> List[Tuple[int, int]]:
        """
        Build a complete path iteratively by combining multiple smaller paths.
        
        Args:
            start_pos: Starting (x, y) screen coordinates
            target_pos: Target (x, y) screen coordinates
            visualize: Whether to return path for visualization
        
        Returns:
            List of (x, y) coordinates forming the complete path
        """
        complete_path = []
        current_pos = start_pos
        target_x, target_y = target_pos
        
        print(f"Building iterative path from {start_pos} to {target_pos}")
        
        for iteration in range(self.max_iterations):
            # Calculate current distance to target
            current_x, current_y = current_pos
            distance_to_target = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
            
            print(f"Iteration {iteration + 1}: Distance to target = {distance_to_target:.1f} pixels")
            
            # Check if we're close enough to target
            if distance_to_target <= self.tolerance:
                print(f"Target reached! Final distance: {distance_to_target:.1f} pixels")
                # Add final position to path
                complete_path.append(target_pos)
                break
            
            # Build a path segment from current position to target
            segment_path = self._build_single_path(current_pos, target_pos, visualize=True)
            
            if not segment_path:
                print(f"Iteration {iteration + 1}: Failed to generate path segment")
                break
            
            # Add the segment to the complete path (excluding the first point to avoid duplication)
            if complete_path:
                complete_path.extend(segment_path[1:])
            else:
                complete_path.extend(segment_path)
            
            # Update current position to the end of this segment
            current_pos = segment_path[-1]
            
            # If we're very close to target, add the final position and break
            if distance_to_target <= self.tolerance:
                complete_path.append(target_pos)
                break
        
        # Execute the complete path if not visualizing
        if not visualize and complete_path:
            self._execute_path(complete_path)
        
        return complete_path
    
    def _execute_path(self, path: List[Tuple[int, int]]):
        """Execute the mouse movement along the given path."""
        print(f"Executing path with {len(path)} points")
        if not path:
            return
        
        # Move to first position
        pyautogui.moveTo(path[0][0], path[0][1], duration=0.01)
        
        # Move through the rest of the path with random speed variation
        for x, y in path[1:]:
            # Sample a random speed multiplier for this movement
            speed_multiplier = random.uniform(self.speed_range[0], self.speed_range[1])
            # Calculate duration based on sample rate and speed multiplier
            duration = (1.0 / self.sample_rate) * speed_multiplier
            pyautogui.moveTo(x, y, duration=duration)
    
    def move_mouse(self, target_x: int, target_y: int) -> bool:
        """
        Move mouse to target using human-like path building.
        Uses current mouse position as start and builds path iteratively if enabled.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            
        Returns:
            True if movement successful, False otherwise
        """
        try:
            # Get current mouse position
            current_pos = pyautogui.position()
            target_pos = (target_x, target_y)
            
            # Build and execute the path
            path = self.move_mouse_to_target(current_pos, target_pos, visualize=False)
            
            return len(path) > 0
                
        except Exception as e:
            print(f"Error in mouse movement: {e}")
            return False
    
    def move_mouse_and_click(self, target_x: int, target_y: int, 
                           click_type: str = "left") -> bool:
        """
        Move mouse to target using human-like path building and perform a click.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            click_type: Type of click to perform ("left", "right", "double")
            
        Returns:
            True if movement and click successful, False otherwise
        """
        try:
            # Perform movement
            movement_success = self.move_mouse(target_x, target_y)
            
            if not movement_success:
                print("Movement failed, cannot perform click")
                return False
            
            # Get final position and perform click
            final_x, final_y = pyautogui.position()
            
            if click_type == "left":
                pyautogui.click(final_x, final_y)
            elif click_type == "right":
                pyautogui.rightClick(final_x, final_y)
            elif click_type == "double":
                pyautogui.doubleClick(final_x, final_y)
            else:
                print(f"Unknown click type: {click_type}")
                return False
            
            print(f"Successfully clicked at ({final_x}, {final_y}) with {click_type} click")
            return True
            
        except Exception as e:
            print(f"Error in mouse movement with click: {e}")
            return False
    
    def get_path_info(self, displacement: Tuple[float, float], 
                     use_random_selection: bool = True, k: int = 8) -> dict:
        """
        Get detailed information about the path for a given displacement.
        
        Args:
            displacement: (dx, dy) displacement vector
            use_random_selection: Whether to randomly select from k nearest neighbors (default: True)
            k: Number of nearest neighbors to consider when using random selection (default: 8)
            use_cache: Whether to use cached result if available (default: True)
        
        Returns:
            Dictionary with path information
        """
        if use_random_selection:
            path_idx, distance = self.select_random_path_from_k_nearest(displacement, k)
        else:
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

def test_human_path(path_file: str):
    """Test function to demonstrate HumanPath usage."""
    try:
        # Initialize HumanPath
        human_path = HumanPath(path_file)
        
        # Test finding paths for different displacements
        test_displacements = [
            (100, 100),
            (-50, 200),
            (300, -150),
            (0, 100),
            (100, 0)
        ]
        
        print("\nTesting path finding with random selection (k=8):")
        for disp in test_displacements:
            info = human_path.get_path_info(disp, use_random_selection=True, k=8)
            print(f"Displacement {disp}: Path {info['path_index']} "
                  f"(distance: {info['distance']:.2f}, length: {info['path_length']:.1f})")
        
        print("\nTesting k-nearest neighbors functionality:")
        test_displacement = (100, 100)
        k_nearest = human_path.find_k_nearest_paths(test_displacement, k=5)
        print(f"5 nearest paths for displacement {test_displacement}:")
        for i, (path_idx, distance) in enumerate(k_nearest):
            print(f"  {i+1}. Path {path_idx} (distance: {distance:.2f})")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    # Read in first argument as path file
    import sys
    path_file = sys.argv[1]
    test_human_path(path_file) 