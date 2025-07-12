import pygame
import sys
import numpy as np
from human_path_finder import HumanPath
import random
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

offset = (100, 100)

class PygamePathTest:
    def __init__(self, width=1200, height=800):
        """Initialize the pygame test environment."""
        self.width = width
        self.height = height
        self.screen = None
        self.clock = None
        self.human_path = None
        self.targets = []
        self.paths = []
        self.current_path = []
        self.moving = True
        self.window_pos = None
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.CYAN = (0, 255, 255)
        self.MAGENTA = (255, 0, 255)
        self.GRAY = (128, 128, 128)
        
        self.init_pygame()
        self.init_human_path()
        self.generate_targets()
    
    def init_pygame(self):
        """Initialize pygame and create the window."""
        import os

        # Set the initial window position
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{offset[0]},{offset[1]}'

        pygame.init()

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Human Path Test - Click to move mouse")
        self.clock = pygame.time.Clock()
        
        # Get window position
        self.window_pos = (offset[0], offset[1])
        print(f"Window position: {self.window_pos}")
        
        # Set up font
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
    
    def init_human_path(self):
        """Initialize the HumanPath finder."""
        try:
            self.human_path = HumanPath()
            print("HumanPath initialized successfully")
        except Exception as e:
            print(f"Failed to initialize HumanPath: {e}")
            print("Make sure you have mouse_paths_augmented.npy file")
            sys.exit(1)
    
    def generate_targets(self):
        """Generate a single target for testing."""
        self.targets = []
        
        # Place target in the center of the screen
        x = self.width // 2
        y = self.height // 2
        
        # Add some randomness
        x += random.randint(-100, 100)
        y += random.randint(-100, 100)
        
        # Keep within screen bounds
        x = max(50, min(x, self.width - 50))
        y = max(50, min(y, self.height - 50))
        
        self.targets.append((x, y))
    
    def draw_target(self, pos, color=None, size=15):
        """Draw a target circle at the given position."""
        if color is None:
            color = self.RED
        
        pygame.draw.circle(self.screen, color, pos, size)
        pygame.draw.circle(self.screen, self.WHITE, pos, size, 2)
    
    def draw_path(self, path, color=None, width=2):
        """Draw a path as a series of connected lines."""
        if not path or len(path) < 2:
            return
        
        if color is None:
            color = self.CYAN
        
        # Draw the path
        for i in range(len(path) - 1):
            start_pos = path[i]
            end_pos = path[i + 1]
            pygame.draw.line(self.screen, color, start_pos, end_pos, width)
        
        # Draw points along the path
        for i, pos in enumerate(path):
            if i == 0:  # Start point
                pygame.draw.circle(self.screen, self.GREEN, pos, 4)
            elif i == len(path) - 1:  # End point
                pygame.draw.circle(self.screen, self.RED, pos, 4)
            else:  # Intermediate points
                pygame.draw.circle(self.screen, self.YELLOW, pos, 2)
    
    def draw_info_panel(self):
        """Draw information panel."""
        info_lines = [
            f"Target: 1",
            f"Paths drawn: {len(self.paths)}",
            f"Moving: {self.moving}",
            "",
            "Controls:",
            "Click: Move to target",
            "R: Reset",
            "Q: Quit"
        ]
        
        y_offset = 10
        for line in info_lines:
            if line == "":
                y_offset += 10
                continue
            
            text_surface = self.small_font.render(line, True, self.WHITE)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    def draw_displacement_info(self, start_pos, target_pos):
        """Draw displacement information."""
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        
        info_text = f"Displacement: ({dx}, {dy})"
        text_surface = self.font.render(info_text, True, self.WHITE)
        self.screen.blit(text_surface, (10, self.height - 60))
        
        # Get path info
        if self.human_path:
            path_info = self.human_path.get_path_info((dx, dy))
            path_text = f"Path {path_info['path_index']} (dist: {path_info['distance']:.1f})"
            text_surface = self.small_font.render(path_text, True, self.WHITE)
            self.screen.blit(text_surface, (10, self.height - 40))
    
    def move_to_target(self, target_pos):
        """Move mouse to target using human-like path."""
        print(f"Moving to {target_pos}")
        if not self.human_path:
            return
        
        # Get current mouse position
        current_pos = pygame.mouse.get_pos()
        
        # Get the path for this movement
        path = self.human_path.move_mouse_to_target(
            current_pos, target_pos, visualize=True
        )
        
        # Store the path for visualization
        self.paths.append({
            'start': current_pos,
            'target': target_pos,
            'path': path,
            'color': self.get_random_color()
        })
        
        # Actually move the mouse with window offset
        if self.window_pos:
            # Convert pygame coordinates to screen coordinates
            screen_start_x = self.window_pos[0] + current_pos[0]
            screen_start_y = self.window_pos[1] + current_pos[1]
            
            # Convert path coordinates to screen coordinates
            screen_path = []
            for x, y in path:
                screen_x = self.window_pos[0] + x
                screen_y = self.window_pos[1] + y
                screen_path.append((screen_x, screen_y))
            
            print(f"Window offset: {self.window_pos}")
            print(f"Screen start: ({screen_start_x}, {screen_start_y})")
            print(f"Path length: {len(screen_path)}")
            
            # Execute the path with screen coordinates
            self.human_path._execute_path(screen_path, (screen_start_x, screen_start_y))
        else:
            # Fallback if window position not available
            self.human_path._execute_path(path, current_pos)
    
    def get_random_color(self):
        """Get a random color for path visualization."""
        colors = [self.CYAN, self.MAGENTA, self.YELLOW, self.GREEN, self.BLUE]
        return random.choice(colors)
    
    def reset(self):
        """Reset the visualization."""
        self.paths = []
        self.moving = False
    

    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_r:
                    self.reset()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Find closest target
                    mouse_pos = pygame.mouse.get_pos()
                    closest_target = min(self.targets, 
                                       key=lambda t: ((t[0] - mouse_pos[0])**2 + 
                                                    (t[1] - mouse_pos[1])**2)**0.5)
                    self.move_to_target(closest_target)
        
        return True
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        # Draw target
        target = self.targets[0]
        self.draw_target(target, self.RED)
        
        # Draw target label
        text_surface = self.small_font.render("TARGET", True, self.WHITE)
        self.screen.blit(text_surface, (target[0] - 25, target[1] - 25))
        
        # Draw all paths
        for path_data in self.paths:
            self.draw_path(path_data['path'], path_data['color'])
        
        # Draw current mouse position
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, self.WHITE, mouse_pos, 8, 2)
        
        # Draw info panels
        self.draw_info_panel()
        
        if self.paths:
            last_path = self.paths[-1]
            self.draw_displacement_info(last_path['start'], last_path['target'])
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        print("Pygame Path Test Started")
        print("Controls:")
        print("- Click near a target to move to it")
        print("- Press SPACE to move to next target")
        print("- Press R to reset")
        print("- Press Q to quit")
        
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        print("Test completed!")

def main():
    """Main function to run the pygame test."""
    try:
        test = PygamePathTest()
        test.run()
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 