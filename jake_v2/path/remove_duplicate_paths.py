#!/usr/bin/env python3
"""
Script to remove duplicate paths from a path file.
Checks for duplicates based on final displacement with tolerance of 1e-8.
"""

import numpy as np
import os
import sys
from typing import List, Tuple, Set
import argparse

def calculate_displacement(path: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate the final displacement of a path.
    
    Args:
        path: List of (x, y) coordinates forming the path
    
    Returns:
        Tuple of (dx, dy) representing the final displacement
    """
    if len(path) < 2:
        return (0.0, 0.0)
    
    start_x, start_y = path[0]
    end_x, end_y = path[-1]
    return (end_x - start_x, end_y - start_y)

def calculate_displacement_distance(disp1: Tuple[float, float], disp2: Tuple[float, float]) -> float:
    """
    Calculate the Euclidean distance between two displacements.
    
    Args:
        disp1: First displacement (dx1, dy1)
        disp2: Second displacement (dx2, dy2)
    
    Returns:
        Euclidean distance between the displacements
    """
    dx = disp1[0] - disp2[0]
    dy = disp1[1] - disp2[1]
    return np.sqrt(dx*dx + dy*dy)

def find_duplicate_paths(paths: List[List[Tuple[float, float]]], tolerance: float = 1e-8) -> Tuple[List[List[Tuple[float, float]]], List[int]]:
    """
    Find and remove duplicate paths based on displacement similarity.
    
    Args:
        paths: List of paths, where each path is a list of (x, y) coordinates
        tolerance: Distance tolerance for considering displacements as duplicates (default: 1e-8)
    
    Returns:
        Tuple of (unique_paths, removed_indices)
    """
    if not paths:
        return [], []
    
    unique_paths = []
    removed_indices = []
    seen_displacements = []
    
    print(f"Processing {len(paths)} paths with tolerance {tolerance}")
    
    for i, path in enumerate(paths):
        if len(path) < 2:
            print(f"Warning: Path {i} has less than 2 points, skipping")
            removed_indices.append(i)
            continue
        
        current_displacement = calculate_displacement(path)
        
        # Check if this displacement is similar to any previously seen displacement
        is_duplicate = False
        for seen_disp in seen_displacements:
            distance = calculate_displacement_distance(current_displacement, seen_disp)
            if distance < tolerance:
                is_duplicate = True
                break
        
        if is_duplicate:
            removed_indices.append(i)
            print(f"Removing duplicate path {i} with displacement {current_displacement}")
        else:
            unique_paths.append(path)
            seen_displacements.append(current_displacement)
            print(f"Keeping path {i} with displacement {current_displacement}")
    
    return unique_paths, removed_indices

def load_paths(file_path: str) -> List[List[Tuple[float, float]]]:
    """
    Load paths from a .npy file.
    
    Args:
        file_path: Path to the .npy file containing paths
    
    Returns:
        List of paths, where each path is a list of (x, y) coordinates
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Path file not found: {file_path}")
    
    print(f"Loading paths from {file_path}...")
    paths = np.load(file_path, allow_pickle=True)
    
    # Convert numpy arrays to lists of tuples
    converted_paths = []
    for path in paths:
        if len(path) >= 2:
            # Convert each point to a tuple
            path_tuples = [(float(point[0]), float(point[1])) for point in path]
            converted_paths.append(path_tuples)
    
    print(f"Loaded {len(converted_paths)} valid paths")
    return converted_paths

def save_paths(paths: List[List[Tuple[float, float]]], file_path: str):
    """
    Save paths to a .npy file.
    
    Args:
        paths: List of paths to save
        file_path: Output file path
    """
    print(f"Saving {len(paths)} unique paths to {file_path}...")
    
    # Convert back to numpy arrays for saving
    numpy_paths = []
    for path in paths:
        path_array = np.array(path, dtype=np.float64)
        numpy_paths.append(path_array)
    
    np.save(file_path, np.array(numpy_paths, dtype=object))
    print(f"Successfully saved to {file_path}")

def analyze_paths(paths: List[List[Tuple[float, float]]]):
    """
    Analyze the paths and print statistics.
    
    Args:
        paths: List of paths to analyze
    """
    if not paths:
        print("No paths to analyze")
        return
    
    print("\n=== Path Analysis ===")
    print(f"Total paths: {len(paths)}")
    
    # Calculate displacement statistics
    displacements = []
    path_lengths = []
    
    for path in paths:
        if len(path) >= 2:
            # Calculate displacement
            disp = calculate_displacement(path)
            displacements.append(disp)
            
            # Calculate path length
            length = 0
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                length += np.sqrt(dx*dx + dy*dy)
            path_lengths.append(length)
    
    if displacements:
        disp_array = np.array(displacements)
        print(f"Displacement range:")
        print(f"  X: {disp_array[:, 0].min():.3f} to {disp_array[:, 0].max():.3f}")
        print(f"  Y: {disp_array[:, 1].min():.3f} to {disp_array[:, 1].max():.3f}")
        print(f"  Mean: ({disp_array[:, 0].mean():.3f}, {disp_array[:, 1].mean():.3f})")
    
    if path_lengths:
        length_array = np.array(path_lengths)
        print(f"Path length range: {length_array.min():.3f} to {length_array.max():.3f}")
        print(f"Mean path length: {length_array.mean():.3f}")

def main():
    """Main function to remove duplicate paths."""
    parser = argparse.ArgumentParser(description="Remove duplicate paths from a path file")
    parser.add_argument("input_file", help="Input .npy file containing paths")
    parser.add_argument("-o", "--output", help="Output file (default: input_file_cleaned.npy)")
    parser.add_argument("-t", "--tolerance", type=float, default=1e-8, 
                       help="Distance tolerance for duplicates (default: 1e-8)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be removed without actually removing")
    
    args = parser.parse_args()
    
    try:
        # Load paths
        paths = load_paths(args.input_file)
        
        if not paths:
            print("No valid paths found in file")
            return
        
        # Analyze original paths
        print("\n=== Original Paths ===")
        analyze_paths(paths)
        
        # Find duplicates
        unique_paths, removed_indices = find_duplicate_paths(paths, args.tolerance)
        
        print(f"\n=== Results ===")
        print(f"Original paths: {len(paths)}")
        print(f"Unique paths: {len(unique_paths)}")
        print(f"Removed paths: {len(removed_indices)}")
        print(f"Removal percentage: {len(removed_indices)/len(paths)*100:.1f}%")
        
        if removed_indices:
            print(f"Removed indices: {removed_indices}")
        
        # Analyze unique paths
        print("\n=== Unique Paths ===")
        analyze_paths(unique_paths)
        
        # Save or dry run
        if args.dry_run:
            print("\n=== DRY RUN ===")
            print("No files were modified. Use without --dry-run to actually save changes.")
        else:
            # Determine output file
            if args.output:
                output_file = args.output
            else:
                base_name = os.path.splitext(args.input_file)[0]
                output_file = f"{base_name}_cleaned.npy"
            
            # Save unique paths
            save_paths(unique_paths, output_file)
            
            print(f"\n=== Summary ===")
            print(f"Successfully removed {len(removed_indices)} duplicate paths")
            print(f"Saved {len(unique_paths)} unique paths to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 