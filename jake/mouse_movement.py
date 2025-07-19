import pyautogui
import pydirectinput
import random
import time
import math
from typing import Tuple, List, Optional, Union
import numpy as np

class BezierMouseMovement:
    def __init__(self, speed_factor: Union[float, Tuple[float, float]] = 1.0, jitter_factor: float = 0.1):
        """
        Initialize mouse movement controller
        
        Args:
            speed_factor: Controls overall movement speed. Can be:
                - float: Single speed factor (1.0 = normal, 0.5 = slower, 2.0 = faster)
                - tuple: Speed range (min, max) to randomly sample from for each movement
            jitter_factor: Controls how much random perturbation to add (0.0 = straight line, 0.2 = lots of jitter)
        """
        # Handle speed_factor as either single value or range
        if isinstance(speed_factor, (list, tuple)) and len(speed_factor) == 2:
            self.speed_range = (float(speed_factor[0]), float(speed_factor[1]))
            self.speed_factor = None  # Will be sampled for each movement
        else:
            self.speed_range = None
            self.speed_factor = float(speed_factor)
        
        self.jitter_factor = jitter_factor
        
        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # Small pause between movements
    
    def _get_speed_factor(self) -> float:
        """
        Get the current speed factor, either from the fixed value or by sampling from the range
        
        Returns:
            Current speed factor to use for this movement
        """
        if self.speed_range is not None:
            # Randomly sample from the speed range
            return random.uniform(self.speed_range[0], self.speed_range[1])
        else:
            # Use the fixed speed factor
            return self.speed_factor if self.speed_factor is not None else 1.0
    
    def generate_bezier_curve(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                             num_points: int = 50) -> List[Tuple[int, int]]:
        """
        Generate a Bezier curve path from start to end position with random control points
        using NumPy's polynomial evaluation for efficiency
        
        Args:
            start_pos: Starting (x, y) coordinates
            end_pos: Ending (x, y) coordinates
            num_points: Number of points to generate along the curve
            
        Returns:
            List of (x, y) coordinates forming the path
        """
        x1, y1 = start_pos
        x4, y4 = end_pos
        
        # Calculate straight-line distance
        distance = math.sqrt((x4 - x1)**2 + (y4 - y1)**2)
        
        # Generate 2 random control points along the path with perturbation
        # Control points will be at 1/3 and 2/3 along the straight line path
        t1, t2 = 1/3, 2/3
        
        # Base control points (1/3 and 2/3 along straight line)
        x2_base = x1 + t1 * (x4 - x1)
        y2_base = y1 + t1 * (y4 - y1)
        x3_base = x1 + t2 * (x4 - x1)
        y3_base = y1 + t2 * (y4 - y1)
        
        # Add random perturbation perpendicular to the path
        # Calculate perpendicular vector
        dx = x4 - x1
        dy = y4 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Normalize and rotate 90 degrees
            perp_x = -dy / length
            perp_y = dx / length
            
            # Add random perturbation
            max_perturbation = distance * self.jitter_factor
            perturb1 = random.uniform(-max_perturbation, max_perturbation)
            perturb2 = random.uniform(-max_perturbation, max_perturbation)
            
            x2 = int(x2_base + perp_x * perturb1)
            y2 = int(y2_base + perp_y * perturb1)
            x3 = int(x3_base + perp_x * perturb2)
            y3 = int(y3_base + perp_y * perturb2)
        else:
            # If start and end are the same, just use base points
            x2, y2 = int(x2_base), int(y2_base)
            x3, y3 = int(x3_base), int(y3_base)
        
        # Generate parameter values t from 0 to 1
        t_values = np.linspace(0, 1, num_points)
        
        # Calculate Bezier curve using NumPy polynomial evaluation
        # Cubic Bezier: B(t) = (1-t)³P₁ + 3(1-t)²tP₂ + 3(1-t)t²P₃ + t³P₄
        # This can be rewritten as: B(t) = P₁ + 3t(P₂-P₁) + 3t²(P₃-2P₂+P₁) + t³(P₄-3P₃+3P₂-P₁)
        
        # Calculate coefficients for the polynomial
        # For x coordinates
        x_coeffs = np.array([
            x1,  # constant term
            3 * (x2 - x1),  # linear term
            3 * (x3 - 2*x2 + x1),  # quadratic term
            x4 - 3*x3 + 3*x2 - x1  # cubic term
        ])
        
        # For y coordinates
        y_coeffs = np.array([
            y1,  # constant term
            3 * (y2 - y1),  # linear term
            3 * (y3 - 2*y2 + y1),  # quadratic term
            y4 - 3*y3 + 3*y2 - y1  # cubic term
        ])
        
        # Evaluate polynomials using NumPy
        x_points = np.polyval(x_coeffs[::-1], t_values)  # Reverse for polyval
        y_points = np.polyval(y_coeffs[::-1], t_values)  # Reverse for polyval
        
        # Convert to integer coordinates and return as list of tuples
        points = [(int(x), int(y)) for x, y in zip(x_points, y_points)]
        
        return points
    
    def move_mouse_to(self, target_x: int, target_y: int, 
                     duration: Optional[float] = None, 
                     ease_in_out: bool = True) -> bool:
        """
        Move mouse from current position to target using Bezier curve
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            duration: Movement duration in seconds (None = auto-calculate)
            ease_in_out: Whether to use ease-in-out timing
            
        Returns:
            True if movement successful, False otherwise
        """
        try:
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate distance for auto-duration
            if duration is None:
                distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
                # Base duration: 0.5 seconds for 500 pixels, scaled by speed factor
                duration = max(0.1, (distance / 500) * 0.5 / self._get_speed_factor())
            
            # Generate Bezier curve path
            path = self.generate_bezier_curve((current_x, current_y), (target_x, target_y))
            
            # Calculate timing for each point
            num_points = len(path)
            if ease_in_out:
                # Ease-in-out timing: slow at start/end, fast in middle
                timings = []
                for i in range(num_points):
                    t = i / (num_points - 1)
                    # Ease-in-out function: smooth acceleration and deceleration
                    if t < 0.5:
                        ease_t = 2 * t * t
                    else:
                        ease_t = 1 - 2 * (1 - t) * (1 - t)
                    timings.append(ease_t * duration)
            else:
                # Linear timing
                timings = [i / (num_points - 1) * duration for i in range(num_points)]
            
            # Execute the movement
            start_time = time.time()
            for i, (x, y) in enumerate(path):
                # Move to point
                pyautogui.moveTo(x, y)
                
                # Wait until next timing point
                if i < len(path) - 1:
                    next_time = start_time + timings[i + 1]
                    sleep_time = next_time - time.time()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            
            return True
            
        except Exception as e:
            print(f"Error in mouse movement: {e}")
            return False
    
    def click_at(self, x: int, y: int, 
                button: str = "left", 
                duration: Optional[float] = None,
                ease_in_out: bool = True) -> bool:
        """
        Move mouse to position and click using natural movement
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            button: Mouse button ("left", "right", "middle")
            duration: Movement duration (None = auto-calculate)
            ease_in_out: Whether to use ease-in-out timing
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            # Move to position first
            if not self.move_mouse_to(x, y, duration, ease_in_out):
                return False
            
            # Small pause before clicking (human-like)
            time.sleep(random.uniform(0.05, 0.15))
            
            # Perform the click
            if button == "left":
                pydirectinput.click(x, y)
            elif button == "right":
                pydirectinput.rightClick(x, y)
            elif button == "middle":
                pydirectinput.middleClick(x, y)
            else:
                print(f"Unknown button type: {button}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error in mouse click: {e}")
            return False
    
    def double_click_at(self, x: int, y: int, 
                       duration: Optional[float] = None,
                       ease_in_out: bool = True) -> bool:
        """
        Move mouse to position and double-click using natural movement
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Movement duration (None = auto-calculate)
            ease_in_out: Whether to use ease-in-out timing
            
        Returns:
            True if double-click successful, False otherwise
        """
        try:
            # Move to position first
            if not self.move_mouse_to(x, y, duration, ease_in_out):
                return False
            
            # Small pause before double-clicking (human-like)
            time.sleep(random.uniform(0.05, 0.15))
            
            # Perform the double-click
            pydirectinput.doubleClick(x, y)
            
            return True
            
        except Exception as e:
            print(f"Error in mouse double-click: {e}")
            return False
    
    def set_speed_factor(self, speed_factor: Union[float, Tuple[float, float]]):
        """
        Set the speed factor for mouse movements
        
        Args:
            speed_factor: Can be:
                - float: Single speed factor
                - tuple: Speed range (min, max) to randomly sample from
        """
        if isinstance(speed_factor, (list, tuple)) and len(speed_factor) == 2:
            self.speed_range = (max(0.1, float(speed_factor[0])), max(0.1, float(speed_factor[1])))
            self.speed_factor = None
        else:
            self.speed_range = None
            self.speed_factor = max(0.1, float(speed_factor))  # Minimum 0.1x speed
    
    def set_jitter_factor(self, jitter_factor: float):
        """Set the jitter factor for path perturbation"""
        self.jitter_factor = max(0.0, min(1.0, jitter_factor))  # Clamp between 0.0 and 1.0

# Example usage and testing
if __name__ == "__main__":
    # Create mouse movement controller with speed range
    mouse = MouseMovement(speed_factor=(0.8, 1.5), jitter_factor=0.15)
    
    print("Mouse Movement Test")
    print("Testing speed range: (0.8, 1.5) - each movement will use a random speed in this range")
    print("Move your mouse to see the natural movement in action...")
    
    # Test movement to current position + offset
    current_x, current_y = pyautogui.position()
    target_x = current_x + 200
    target_y = current_y + 100
    
    print(f"Moving from ({current_x}, {current_y}) to ({target_x}, {target_y})")
    
    # Test different movement types
    print("\n1. Moving mouse...")
    mouse.move_mouse_to(target_x, target_y)
    
    time.sleep(1)
    
    print("2. Clicking...")
    mouse.click_at(target_x + 50, target_y + 50)
    
    time.sleep(1)
    
    print("3. Double-clicking...")
    mouse.double_click_at(target_x - 50, target_y - 50)
    
    # Test changing to fixed speed
    print("\n4. Testing fixed speed...")
    mouse.set_speed_factor(1.2)
    mouse.move_mouse_to(target_x + 100, target_y + 100)
    
    # Test changing back to speed range
    print("\n5. Testing speed range again...")
    mouse.set_speed_factor((0.5, 2.0))
    mouse.move_mouse_to(target_x - 100, target_y - 100)
    
    print("Test complete!") 