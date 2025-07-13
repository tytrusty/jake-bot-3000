import pygame
import time
import threading
import numpy as np
import os
from pynput import mouse

class PygameMousePathRecorder:
    def __init__(self, sample_rate=50, screen_size=(1500, 1500), save_path="mouse_paths.npy"):
        self.sample_rate = sample_rate
        self.screen_size = screen_size
        self.center = (screen_size[0] // 2, screen_size[1] // 2)
        self.recording = False
        self.start_pos = None
        self.path = []
        self.paths = []
        self.save_path = save_path

        # Load existing paths
        if os.path.exists(self.save_path):
            print(f"Loading existing paths from {self.save_path}")
            self.paths = list(np.load(self.save_path, allow_pickle=True))
            print(f"Loaded {len(self.paths)} paths.")

        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Mouse Path Recorder (Radial View)")
        self.clock = pygame.time.Clock()
        self.running = True

    def _sample_mouse_position(self):
        from pynput.mouse import Controller
        mouse_controller = Controller()

        while self.recording:
            pos = mouse_controller.position
            if self.start_pos is None:
                self.start_pos = pos
            dx = pos[0] - self.start_pos[0]
            dy = pos[1] - self.start_pos[1]
            self.path.append((dx, dy))
            time.sleep(1 / self.sample_rate)

    def _on_click(self, x, y, button, pressed):
        if pressed:
            if not self.recording:
                print("Started recording...")
                self.recording = True
                self.path = []
                self.start_pos = None
                self.sampling_thread = threading.Thread(target=self._sample_mouse_position)
                self.sampling_thread.start()
            else:
                print("Stopped recording.")
                self.recording = False
                self.sampling_thread.join()
                self.paths.append(self.path.copy())

    def _draw_paths(self):
        self.screen.fill((30, 30, 30))
        for path in self.paths:
            points = [(int(self.center[0] + dx), int(self.center[1] + dy)) for dx, dy in path]
            if len(points) > 1:
                pygame.draw.lines(self.screen, (0, 200, 255), False, points, 2)
        pygame.display.flip()

    def _handle_keypress(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.save_paths()
                print(f"Saved {len(self.paths)} paths to {self.save_path}")

    def run(self):
        listener = mouse.Listener(on_click=self._on_click)
        listener.start()
        print("Click once to start recording, click again to stop. Press 's' to save. Close window or Ctrl+C to quit.")

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self._handle_keypress(event)

            self._draw_paths()
            self.clock.tick(60)

        listener.stop()
        self.save_paths()
        pygame.quit()

    def save_paths(self):
        # Append to existing file if it exists
        if os.path.exists(self.save_path):
            existing = list(np.load(self.save_path, allow_pickle=True))
            combined = existing + self.paths
        else:
            combined = self.paths

        np.save(self.save_path, np.array(combined, dtype=object))

if __name__ == "__main__":
    recorder = PygameMousePathRecorder()
    try:
        recorder.run()
    except KeyboardInterrupt:
        print("\nInterrupted — saving before exit.")
        recorder.save_paths()
        pygame.quit()
