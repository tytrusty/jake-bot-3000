#!/usr/bin/env python3
"""
Interactive GUI Configuration Tool for RuneScape Bot

This script provides a step-by-step GUI interface for configuring the RuneScape bot.
It includes visual overlays for area selection and real-time configuration preview.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
import sys
import time
import threading
import argparse
from typing import Optional, Tuple, Dict, Any
import pyautogui
import jake.screenshot_utils
import jake.color_utils
from jake.config_manager import ConfigurationManager

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive GUI Configuration Tool for RuneScape Bot")
    parser.add_argument("--config", "-c", type=str, default="bot_config.json",
                       help="Configuration file to edit (default: bot_config.json)")
    return parser.parse_args()

class ConfigGUI:
    def __init__(self, config_file: str = "bot_config.json"):
        self.root = tk.Tk()
        self.root.title("RuneScape Bot Configuration")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Store config file path
        self.config_file = config_file
        
        # Initialize configuration manager for defaults
        self.config_manager = ConfigurationManager(config_file)
        
        # Configuration data - use config manager's default config
        self.config = self.config_manager.config.copy()
        
        # Override defaults for better user experience
        self.config["human_movement"]["enabled"] = True
        self.config["human_movement"]["speed_range"] = [0.5, 2.0]  # Normal speed
        self.config["combat"]["enable_breaks"] = True
        self.current_step = 0
        self.steps = [
            "Human Movement",
            "Health Bar",
            "Food Area", 
            "Loot Pickup",
            "Combat Settings",
            "Review & Save"
        ]
        
        # Overlay window for area selection
        self.overlay_window = None
        self.selection_start = None
        self.selection_end = None
        self.selection_canvas = None
        
        # Track drawn elements for persistent display
        self.drawn_elements: Dict[str, Optional[Tuple[Any, ...]]] = {
            'health_bar': None,  # (x, y, color)
            'food_area': None,   # (x1, y1, x2, y2)
            'inventory_area': None,  # (x1, y1, x2, y2)
        }
        
        # Setup GUI
        self._setup_gui()
        self._load_config()
        
    def _setup_gui(self):
        """Setup the main GUI layout."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title with config file name
        title_text = f"RuneScape Bot Configuration - {os.path.basename(self.config_file)}"
        title_label = ttk.Label(main_frame, text=title_text, 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                      maximum=len(self.steps))
        progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Step label
        self.step_label = ttk.Label(main_frame, text="", font=("Arial", 12, "bold"))
        self.step_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        
        # Navigation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        self.prev_button = ttk.Button(button_frame, text="Previous", command=self._prev_step)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_button = ttk.Button(button_frame, text="Next", command=self._next_step)
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(button_frame, text="Save Config", command=self._save_config)
        self.save_button.pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Initialize first step
        self._show_step(0)
    
    def _draw_persistent_elements(self):
        """Draw all configured elements on the overlay."""
        if not self.overlay_window or not self.selection_canvas:
            return
        
        # Clear previous persistent elements
        self.selection_canvas.delete("persistent")
        
        # Draw health bar position
        if self.drawn_elements['health_bar']:
            x, y, color = self.drawn_elements['health_bar']
            # Draw crosshair
            size = 20
            self.selection_canvas.create_line(x-size, y, x+size, y, fill="red", width=2, tags="persistent")
            self.selection_canvas.create_line(x, y-size, x, y+size, fill="red", width=2, tags="persistent")
            # Draw circle
            self.selection_canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="white", width=2, tags="persistent")
            # Draw label
            self.selection_canvas.create_text(x, y-25, text="Health Bar", fill="red", font=("Arial", 10, "bold"), tags="persistent")
            # Draw color preview
            self.selection_canvas.create_rectangle(x+15, y-10, x+35, y+10, fill=f"#{color}", outline="white", width=1, tags="persistent")
        
        # Draw food area
        if self.drawn_elements['food_area']:
            x1, y1, x2, y2 = self.drawn_elements['food_area']
            # Draw rectangle
            self.selection_canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags="persistent")
            # Draw label
            self.selection_canvas.create_text((x1+x2)//2, y1-10, text="Food Area", fill="green", font=("Arial", 10, "bold"), tags="persistent")
            # Draw corner indicators
            corner_size = 8
            for corner in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                cx, cy = corner
                self.selection_canvas.create_oval(cx-corner_size, cy-corner_size, cx+corner_size, cy+corner_size, 
                                                fill="green", outline="white", width=1, tags="persistent")
        
        # Draw inventory area
        if self.drawn_elements['inventory_area']:
            x1, y1, x2, y2 = self.drawn_elements['inventory_area']
            # Draw rectangle
            self.selection_canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=2, tags="persistent")
            # Draw label
            self.selection_canvas.create_text((x1+x2)//2, y1-10, text="Inventory Area", fill="blue", font=("Arial", 10, "bold"), tags="persistent")
            # Draw corner indicators
            corner_size = 8
            for corner in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                cx, cy = corner
                self.selection_canvas.create_oval(cx-corner_size, cy-corner_size, cx+corner_size, cy+corner_size, 
                                                fill="blue", outline="white", width=1, tags="persistent")
    
    def _update_drawn_elements(self):
        """Update drawn elements based on current configuration."""
        # Update health bar
        health_config = self.config.get('health_bar', {})
        if health_config.get('x') is not None and health_config.get('y') is not None:
            self.drawn_elements['health_bar'] = (
                health_config['x'], 
                health_config['y'], 
                health_config.get('color', '000000')
            )
        
        # Update food area
        food_config = self.config.get('food_area', {})
        if food_config.get('enabled') and food_config.get('coordinates'):
            self.drawn_elements['food_area'] = tuple(food_config['coordinates'])
        
        # Update inventory area
        loot_config = self.config.get('loot_pickup', {})
        if loot_config.get('inventory_area'):
            self.drawn_elements['inventory_area'] = tuple(loot_config['inventory_area'])
    
    def _show_step(self, step_index: int):
        """Show the specified configuration step."""
        self.current_step = step_index
        self.progress_var.set(step_index + 1)
        self.step_label.config(text=f"Step {step_index + 1}: {self.steps[step_index]}")
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show step-specific content
        if step_index == 0:
            self._show_human_movement_step()
        elif step_index == 1:
            self._show_health_bar_step()
        elif step_index == 2:
            self._show_food_area_step()
        elif step_index == 3:
            self._show_loot_pickup_step()
        elif step_index == 4:
            self._show_combat_settings_step()
        elif step_index == 5:
            self._show_review_step()
        
        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if step_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if step_index < len(self.steps) - 1 else tk.DISABLED)
        
        # Update status
        self.status_var.set(f"Step {step_index + 1} of {len(self.steps)}")
    
    def _show_human_movement_step(self):
        """Show human movement configuration step."""
        # Enable/disable checkbox
        enabled_var = tk.BooleanVar(value=self.config["human_movement"]["enabled"])
        enabled_check = ttk.Checkbutton(self.content_frame, text="Enable human-like mouse movement",
                                       variable=enabled_var, command=lambda: self._update_config("human_movement", "enabled", enabled_var.get()))
        enabled_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Speed range frame
        speed_frame = ttk.LabelFrame(self.content_frame, text="Speed Range", padding="10")
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(speed_frame, text="Speed range determines how fast the mouse moves:").pack(anchor=tk.W)
        
        speed_options = [
            ("Slow (0.2x to 0.5x)", [0.2, 0.5]),
            ("Normal (0.5x to 2.0x)", [0.5, 2.0]),
            ("Fast (1.5x to 3.0x)", [1.5, 3.0])
        ]
        
        # Determine which option is currently selected
        current_speed = self.config["human_movement"]["speed_range"]
        current_option = "Normal (0.5x to 2.0x)"  # Default
        for text, values in speed_options:
            if values == current_speed:
                current_option = text
                break
        
        speed_var = tk.StringVar(value=current_option)
        for text, values in speed_options:
            ttk.Radiobutton(speed_frame, text=text, variable=speed_var, value=text,
                           command=lambda t=text, v=values: self._update_speed_range(v)).pack(anchor=tk.W)
        
        # Custom speed range
        custom_frame = ttk.Frame(speed_frame)
        custom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(custom_frame, text="Custom range:").pack(side=tk.LEFT)
        
        min_speed_var = tk.StringVar(value=str(self.config["human_movement"]["speed_range"][0]))
        max_speed_var = tk.StringVar(value=str(self.config["human_movement"]["speed_range"][1]))
        
        ttk.Entry(custom_frame, textvariable=min_speed_var, width=8).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(custom_frame, text="to").pack(side=tk.LEFT)
        ttk.Entry(custom_frame, textvariable=max_speed_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        def update_custom_speed():
            try:
                min_speed = float(min_speed_var.get())
                max_speed = float(max_speed_var.get())
                self._update_speed_range([min_speed, max_speed])
            except ValueError:
                pass
        
        min_speed_var.trace("w", lambda *args: update_custom_speed())
        max_speed_var.trace("w", lambda *args: update_custom_speed())
    
    def _show_health_bar_step(self):
        """Show health bar configuration step."""
        # Instructions
        instructions = ttk.Label(self.content_frame, text="Configure the health bar position for combat monitoring.\n"
                                "You need to attack a mob to make their health bar appear.", 
                                font=("Arial", 10))
        instructions.pack(pady=(0, 20))
        
        # Current position display
        pos_frame = ttk.LabelFrame(self.content_frame, text="Current Health Bar Position", padding="10")
        pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.health_pos_var = tk.StringVar()
        if self.config["health_bar"]["x"] is not None:
            self.health_pos_var.set(f"Position: ({self.config['health_bar']['x']}, {self.config['health_bar']['y']})\n"
                                   f"Color: #{self.config['health_bar']['color']}")
        else:
            self.health_pos_var.set("Not configured")
        
        ttk.Label(pos_frame, textvariable=self.health_pos_var).pack()
        
        # Buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Select Health Bar Position", 
                  command=self._select_health_bar_position).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Position", 
                  command=self._clear_health_bar_position).pack(side=tk.LEFT)
    
    def _show_food_area_step(self):
        """Show food area configuration step."""
        # Enable/disable checkbox
        enabled_var = tk.BooleanVar(value=self.config["food_area"]["enabled"])
        enabled_check = ttk.Checkbutton(self.content_frame, text="Enable auto-eating",
                                       variable=enabled_var, command=lambda: self._update_config("food_area", "enabled", enabled_var.get()))
        enabled_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Current area display
        area_frame = ttk.LabelFrame(self.content_frame, text="Food Area", padding="10")
        area_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.food_area_var = tk.StringVar()
        if self.config["food_area"]["coordinates"] is not None:
            coords = self.config["food_area"]["coordinates"]
            self.food_area_var.set(f"Area: ({coords[0]}, {coords[1]}) to ({coords[2]}, {coords[3]})")
        else:
            self.food_area_var.set("Not configured")
        
        ttk.Label(area_frame, textvariable=self.food_area_var).pack()
        
        # Red threshold
        threshold_frame = ttk.Frame(self.content_frame)
        threshold_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(threshold_frame, text="Red threshold for health monitoring:").pack(side=tk.LEFT)
        
        threshold_var = tk.StringVar(value=str(self.config["food_area"]["red_threshold"]))
        threshold_entry = ttk.Entry(threshold_frame, textvariable=threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        def update_threshold(*args):
            try:
                threshold = int(threshold_var.get())
                self._update_config("food_area", "red_threshold", threshold)
            except ValueError:
                pass
        
        threshold_var.trace("w", update_threshold)
        
        # Buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(button_frame, text="Select Food Area", 
                  command=self._select_food_area).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Area", 
                  command=self._clear_food_area).pack(side=tk.LEFT)
    
    def _show_loot_pickup_step(self):
        """Show loot pickup configuration step."""
        # Enable/disable checkbox
        enabled_var = tk.BooleanVar(value=self.config["loot_pickup"]["enabled"])
        enabled_check = ttk.Checkbutton(self.content_frame, text="Enable loot pickup",
                                       variable=enabled_var, command=lambda: self._update_config("loot_pickup", "enabled", enabled_var.get()))
        enabled_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Loot color selection
        color_frame = ttk.LabelFrame(self.content_frame, text="Loot Color", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        color_button_frame = ttk.Frame(color_frame)
        color_button_frame.pack()
        
        self.loot_color_var = tk.StringVar(value=self.config["loot_pickup"]["loot_color"])
        ttk.Label(color_button_frame, text="Color:").pack(side=tk.LEFT)
        ttk.Entry(color_button_frame, textvariable=self.loot_color_var, width=12).pack(side=tk.LEFT, padx=(5, 10))
        
        # Color preview
        self.color_preview = tk.Canvas(color_button_frame, width=30, height=20, bg="white", relief=tk.SUNKEN)
        self.color_preview.pack(side=tk.LEFT)
        
        ttk.Button(color_button_frame, text="Pick Color", 
                  command=self._pick_loot_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # Update color preview
        self._update_color_preview()
        
        # Tolerance and distance
        settings_frame = ttk.LabelFrame(self.content_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tolerance
        tolerance_frame = ttk.Frame(settings_frame)
        tolerance_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(tolerance_frame, text="Color tolerance:").pack(side=tk.LEFT)
        tolerance_var = tk.StringVar(value=str(self.config["loot_pickup"]["tolerance"]))
        ttk.Entry(tolerance_frame, textvariable=tolerance_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Max distance
        distance_frame = ttk.Frame(settings_frame)
        distance_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(distance_frame, text="Max distance:").pack(side=tk.LEFT)
        distance_var = tk.StringVar(value=str(self.config["loot_pickup"]["max_distance"]))
        ttk.Entry(distance_frame, textvariable=distance_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Update functions
        def update_tolerance(*args):
            try:
                tolerance = int(tolerance_var.get())
                self._update_config("loot_pickup", "tolerance", tolerance)
            except ValueError:
                pass
        
        def update_distance(*args):
            try:
                distance = int(distance_var.get())
                self._update_config("loot_pickup", "max_distance", distance)
            except ValueError:
                pass
        
        tolerance_var.trace("w", update_tolerance)
        distance_var.trace("w", update_distance)
        
        # Inventory area for burying
        bury_frame = ttk.LabelFrame(self.content_frame, text="Burying Items", padding="10")
        bury_frame.pack(fill=tk.X, pady=(0, 10))
        
        bury_var = tk.BooleanVar(value=self.config["loot_pickup"]["bury"])
        bury_check = ttk.Checkbutton(bury_frame, text="Enable burying items after pickup",
                                    variable=bury_var, command=lambda: self._update_config("loot_pickup", "bury", bury_var.get()))
        bury_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Inventory area display
        self.inventory_area_var = tk.StringVar()
        if self.config["loot_pickup"]["inventory_area"] is not None:
            coords = self.config["loot_pickup"]["inventory_area"]
            self.inventory_area_var.set(f"Area: ({coords[0]}, {coords[1]}) to ({coords[2]}, {coords[3]})")
        else:
            self.inventory_area_var.set("Not configured")
        
        ttk.Label(bury_frame, textvariable=self.inventory_area_var).pack()
        
        # Buttons
        button_frame = ttk.Frame(bury_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Select Inventory Area", 
                  command=self._select_inventory_area).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Area", 
                  command=self._clear_inventory_area).pack(side=tk.LEFT)
    
    def _show_combat_settings_step(self):
        """Show combat settings configuration step."""
        # Target color
        target_frame = ttk.LabelFrame(self.content_frame, text="Target Color", padding="10")
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        target_button_frame = ttk.Frame(target_frame)
        target_button_frame.pack()
        
        self.target_color_var = tk.StringVar(value=self.config["combat"]["default_target_color"])
        ttk.Label(target_button_frame, text="Default target color:").pack(side=tk.LEFT)
        ttk.Entry(target_button_frame, textvariable=self.target_color_var, width=12).pack(side=tk.LEFT, padx=(5, 10))
        
        # Target color preview
        self.target_color_preview = tk.Canvas(target_button_frame, width=30, height=20, bg="white", relief=tk.SUNKEN)
        self.target_color_preview.pack(side=tk.LEFT)
        
        ttk.Button(target_button_frame, text="Pick Color", 
                  command=self._pick_target_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # Update target color preview
        self._update_target_color_preview()
        
        # Pixel method
        method_frame = ttk.LabelFrame(self.content_frame, text="Pixel Selection Method", padding="10")
        method_frame.pack(fill=tk.X, pady=(0, 10))
        
        method_var = tk.StringVar(value=self.config["combat"]["pixel_method"])
        ttk.Radiobutton(method_frame, text="Smart (blob-based with green exclusion)", 
                       variable=method_var, value="smart").pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="Random (original method)", 
                       variable=method_var, value="random").pack(anchor=tk.W)
        
        def update_method(*args):
            self._update_config("combat", "pixel_method", method_var.get())
        
        method_var.trace("w", update_method)
        
        # Random mouse movement
        mouse_frame = ttk.LabelFrame(self.content_frame, text="Mouse Movement", padding="10")
        mouse_frame.pack(fill=tk.X, pady=(0, 10))
        
        mouse_var = tk.BooleanVar(value=self.config["combat"]["random_mouse_movement"])
        mouse_check = ttk.Checkbutton(mouse_frame, text="Enable random mouse movement during combat",
                                     variable=mouse_var, command=lambda: self._update_config("combat", "random_mouse_movement", mouse_var.get()))
        mouse_check.pack(anchor=tk.W)
        
        # Break system
        break_var = tk.BooleanVar(value=self.config["combat"]["enable_breaks"])
        break_check = ttk.Checkbutton(self.content_frame, text="Enable automatic breaks",
                                     variable=break_var, command=lambda: self._update_config("combat", "enable_breaks", break_var.get()))
        break_check.pack(anchor=tk.W, pady=(0, 5))
        
        # Break settings frame
        break_settings_frame = ttk.LabelFrame(self.content_frame, text="Break Settings", padding="10")
        break_settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Break interval
        interval_frame = ttk.Frame(break_settings_frame)
        interval_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(interval_frame, text="Break interval (minutes):").pack(side=tk.LEFT)
        
        min_interval_var = tk.StringVar(value=str(self.config["combat"]["break_interval_min"]))
        max_interval_var = tk.StringVar(value=str(self.config["combat"]["break_interval_max"]))
        
        ttk.Entry(interval_frame, textvariable=min_interval_var, width=8).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(interval_frame, text="to").pack(side=tk.LEFT)
        ttk.Entry(interval_frame, textvariable=max_interval_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        # Break duration
        duration_frame = ttk.Frame(break_settings_frame)
        duration_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(duration_frame, text="Break duration (minutes):").pack(side=tk.LEFT)
        
        min_duration_var = tk.StringVar(value=str(self.config["combat"]["break_duration_min"]))
        max_duration_var = tk.StringVar(value=str(self.config["combat"]["break_duration_max"]))
        
        ttk.Entry(duration_frame, textvariable=min_duration_var, width=8).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(duration_frame, text="to").pack(side=tk.LEFT)
        ttk.Entry(duration_frame, textvariable=max_duration_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        def update_break_settings(*args):
            try:
                min_interval = int(min_interval_var.get())
                max_interval = int(max_interval_var.get())
                min_duration = int(min_duration_var.get())
                max_duration = int(max_duration_var.get())
                
                self._update_config("combat", "break_interval_min", min_interval)
                self._update_config("combat", "break_interval_max", max_interval)
                self._update_config("combat", "break_duration_min", min_duration)
                self._update_config("combat", "break_duration_max", max_duration)
            except ValueError:
                pass
        
        min_interval_var.trace("w", update_break_settings)
        max_interval_var.trace("w", update_break_settings)
        min_duration_var.trace("w", update_break_settings)
        max_duration_var.trace("w", update_break_settings)
    
    def _show_review_step(self):
        """Show review and save step."""
        # Title
        title_label = ttk.Label(self.content_frame, text="Review Configuration", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Configuration summary
        summary_frame = ttk.LabelFrame(self.content_frame, text="Configuration Summary", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.review_text = tk.Text(summary_frame, height=15, width=60, wrap=tk.WORD)
        self.review_text.pack(fill=tk.BOTH, expand=True)
        
        # Update review content
        self._update_review_content()
        
        # Visual preview button
        preview_frame = ttk.Frame(self.content_frame)
        preview_frame.pack(pady=(10, 0))
        
        ttk.Button(preview_frame, text="Show Visual Preview", 
                  command=self._show_visual_preview).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(preview_frame, text="Refresh Summary", 
                  command=self._update_review_content).pack(side=tk.LEFT)
    
    def _update_review_content(self):
        """Update the review content with current configuration."""
        summary_text = f"Configuration Summary - {os.path.basename(self.config_file)}\n"
        summary_text += "=" * 50 + "\n\n"
        
        # Human movement
        human_config = self.config.get("human_movement", {})
        summary_text += f"Human-like Movement: {'Enabled' if human_config.get('enabled') else 'Disabled'}\n"
        if human_config.get('enabled'):
            speed_range = human_config.get('speed_range', [0.5, 2.0])
            summary_text += f"  Speed Range: {speed_range[0]:.1f}x to {speed_range[1]:.1f}x\n"
        summary_text += "\n"
        
        # Health bar
        health_config = self.config.get("health_bar", {})
        if health_config.get('x') is not None:
            summary_text += f"Health Bar: ({health_config['x']}, {health_config['y']})\n"
            summary_text += f"  Color: #{health_config.get('color', 'N/A')}\n"
        else:
            summary_text += "Health Bar: Not configured\n"
        summary_text += "\n"
        
        # Food area
        food_config = self.config.get("food_area", {})
        summary_text += f"Auto-eating: {'Enabled' if food_config.get('enabled') else 'Disabled'}\n"
        if food_config.get('enabled'):
            coords = food_config.get('coordinates')
            if coords:
                summary_text += f"  Food Area: ({coords[0]}, {coords[1]}) to ({coords[2]}, {coords[3]})\n"
            summary_text += f"  Red Threshold: {food_config.get('red_threshold', 5)}\n"
        summary_text += "\n"
        
        # Loot pickup
        loot_config = self.config.get("loot_pickup", {})
        summary_text += f"Loot Pickup: {'Enabled' if loot_config.get('enabled') else 'Disabled'}\n"
        if loot_config.get('enabled'):
            summary_text += f"  Loot Color: #{loot_config.get('loot_color', 'AA00FFFF')}\n"
            summary_text += f"  Tolerance: {loot_config.get('tolerance', 20)}\n"
            summary_text += f"  Max Distance: {loot_config.get('max_distance', 500)}\n"
            summary_text += f"  Bury Items: {'Yes' if loot_config.get('bury') else 'No'}\n"
            
            inv_coords = loot_config.get('inventory_area')
            if inv_coords:
                summary_text += f"  Inventory Area: ({inv_coords[0]}, {inv_coords[1]}) to ({inv_coords[2]}, {inv_coords[3]})\n"
        summary_text += "\n"
        
        # Combat settings
        combat_config = self.config.get("combat", {})
        summary_text += f"Default Target Color: #{combat_config.get('default_target_color', '00FFFFFA')}\n"
        summary_text += f"Pixel Method: {combat_config.get('pixel_method', 'smart')}\n"
        summary_text += f"Random Mouse Movement: {'Enabled' if combat_config.get('random_mouse_movement') else 'Disabled'}\n"
        summary_text += f"Automatic Breaks: {'Enabled' if combat_config.get('enable_breaks') else 'Disabled'}\n"
        
        if combat_config.get('enable_breaks'):
            summary_text += f"  Break Intervals: {combat_config.get('break_interval_min', 29)}-{combat_config.get('break_interval_max', 33)} minutes\n"
            summary_text += f"  Break Duration: {combat_config.get('break_duration_min', 2)}-{combat_config.get('break_duration_max', 6)} minutes\n"
        
        summary_text += "\n"
        summary_text += f"Configuration will be saved to: {self.config_file}\n"
        
        # Update the text widget
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(tk.END, summary_text)
    
    def _show_visual_preview(self):
        """Show visual preview of all configured elements."""
        # Find RuneScape window
        window_region = jake.screenshot_utils.find_runescape_window("RuneLite")
        if not window_region:
            messagebox.showerror("Error", "RuneScape window not found. Make sure RuneLite is running.")
            return
        
        # Create preview overlay
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Configuration Visual Preview")
        self.preview_window.geometry(f"{window_region[2]}x{window_region[3]}+{window_region[0]}+{window_region[1]}")
        self.preview_window.attributes('-topmost', True)
        self.preview_window.attributes('-alpha', 0.3)
        self.preview_window.overrideredirect(True)
        
        # Create canvas for drawing
        self.preview_canvas = tk.Canvas(self.preview_window, width=window_region[2], height=window_region[3], 
                                      bg='black', highlightthickness=0)
        self.preview_canvas.pack()
        
        # Draw all configured elements
        self._draw_all_configured_elements()
        
        # Add instructions
        self.preview_canvas.create_text(10, 30, text="Configuration Visual Preview", 
                                      fill="white", font=("Arial", 14, "bold"), anchor="nw")
        self.preview_canvas.create_text(10, 50, text="Press Escape to close", 
                                      fill="white", font=("Arial", 10), anchor="nw")
        
        # Bind escape to close
        self.preview_window.bind("<Escape>", lambda e: self._close_preview())
        
        # Focus the preview window
        self.preview_window.focus_set()
    
    def _draw_all_configured_elements(self):
        """Draw all configured elements on the preview canvas."""
        if not self.preview_canvas:
            return
        
        # Clear canvas
        self.preview_canvas.delete("all")
        
        # Draw health bar position
        health_config = self.config.get('health_bar', {})
        if health_config.get('x') is not None and health_config.get('y') is not None:
            x, y = health_config['x'], health_config['y']
            color = health_config.get('color', '000000')
            
            # Draw crosshair
            size = 25
            self.preview_canvas.create_line(x-size, y, x+size, y, fill="red", width=3, tags="preview")
            self.preview_canvas.create_line(x, y-size, x, y+size, fill="red", width=3, tags="preview")
            
            # Draw circle
            self.preview_canvas.create_oval(x-8, y-8, x+8, y+8, fill="red", outline="white", width=2, tags="preview")
            
            # Draw label with background
            label_text = "Health Bar"
            self.preview_canvas.create_rectangle(x-40, y-35, x+40, y-15, fill="black", outline="red", width=2, tags="preview")
            self.preview_canvas.create_text(x, y-25, text=label_text, fill="red", font=("Arial", 10, "bold"), tags="preview")
            
            # Draw color preview
            self.preview_canvas.create_rectangle(x+45, y-12, x+65, y+12, fill=f"#{color}", outline="white", width=1, tags="preview")
            self.preview_canvas.create_text(x+80, y, text=f"#{color}", fill="white", font=("Arial", 8), anchor="w", tags="preview")
        
        # Draw food area
        food_config = self.config.get('food_area', {})
        if food_config.get('enabled') and food_config.get('coordinates'):
            x1, y1, x2, y2 = food_config['coordinates']
            
            # Draw rectangle with pattern
            self.preview_canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=3, tags="preview")
            
            # Draw diagonal pattern
            for i in range(0, x2-x1, 20):
                self.preview_canvas.create_line(x1+i, y1, x1+i+20, y2, fill="green", width=1, tags="preview")
            
            # Draw label with background
            label_text = "Food Area"
            label_x = (x1 + x2) // 2
            label_y = y1 - 15
            self.preview_canvas.create_rectangle(label_x-40, label_y-10, label_x+40, label_y+10, fill="black", outline="green", width=2, tags="preview")
            self.preview_canvas.create_text(label_x, label_y, text=label_text, fill="green", font=("Arial", 10, "bold"), tags="preview")
            
            # Draw corner indicators
            corner_size = 10
            for corner in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                cx, cy = corner
                self.preview_canvas.create_oval(cx-corner_size, cy-corner_size, cx+corner_size, cy+corner_size, 
                                              fill="green", outline="white", width=2, tags="preview")
        
        # Draw inventory area
        loot_config = self.config.get('loot_pickup', {})
        if loot_config.get('inventory_area'):
            x1, y1, x2, y2 = loot_config['inventory_area']
            
            # Draw rectangle with pattern
            self.preview_canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=3, tags="preview")
            
            # Draw grid pattern
            for i in range(0, x2-x1, 15):
                self.preview_canvas.create_line(x1+i, y1, x1+i, y2, fill="blue", width=1, tags="preview")
            for i in range(0, y2-y1, 15):
                self.preview_canvas.create_line(x1, y1+i, x2, y1+i, fill="blue", width=1, tags="preview")
            
            # Draw label with background
            label_text = "Inventory Area"
            label_x = (x1 + x2) // 2
            label_y = y1 - 15
            self.preview_canvas.create_rectangle(label_x-50, label_y-10, label_x+50, label_y+10, fill="black", outline="blue", width=2, tags="preview")
            self.preview_canvas.create_text(label_x, label_y, text=label_text, fill="blue", font=("Arial", 10, "bold"), tags="preview")
            
            # Draw corner indicators
            corner_size = 10
            for corner in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                cx, cy = corner
                self.preview_canvas.create_oval(cx-corner_size, cy-corner_size, cx+corner_size, cy+corner_size, 
                                              fill="blue", outline="white", width=2, tags="preview")
        
        # Draw legend
        self._draw_legend()
    
    def _draw_legend(self):
        """Draw a legend explaining the visual elements."""
        if not self.preview_canvas:
            return
            
        # Get canvas dimensions
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Position legend in bottom left
        legend_width = 200
        legend_height = 120
        legend_x = 10
        legend_y = canvas_height - legend_height - 10  # 10 pixels from bottom
        
        # Legend background
        self.preview_canvas.create_rectangle(legend_x, legend_y, legend_x+legend_width, legend_y+legend_height, 
                                          fill="black", outline="white", width=2, tags="preview")
        
        # Legend title
        self.preview_canvas.create_text(legend_x+legend_width//2, legend_y+10, text="Legend", 
                                      fill="white", font=("Arial", 12, "bold"), tags="preview")
        
        # Health bar legend
        self.preview_canvas.create_line(legend_x+10, legend_y+30, legend_x+30, legend_y+30, fill="red", width=3, tags="preview")
        self.preview_canvas.create_text(legend_x+35, legend_y+30, text="Health Bar Position", 
                                      fill="white", font=("Arial", 9), anchor="w", tags="preview")
        
        # Food area legend
        self.preview_canvas.create_rectangle(legend_x+10, legend_y+55, legend_x+30, legend_y+75, outline="green", width=2, tags="preview")
        self.preview_canvas.create_text(legend_x+35, legend_y+65, text="Food Area", 
                                      fill="white", font=("Arial", 9), anchor="w", tags="preview")
        
        # Inventory area legend
        self.preview_canvas.create_rectangle(legend_x+10, legend_y+80, legend_x+30, legend_y+100, outline="blue", width=2, tags="preview")
        self.preview_canvas.create_text(legend_x+35, legend_y+90, text="Inventory Area", 
                                      fill="white", font=("Arial", 9), anchor="w", tags="preview")
    
    def _close_preview(self):
        """Close the visual preview window."""
        if hasattr(self, 'preview_window') and self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
            self.preview_canvas = None
    
    def _prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _next_step(self):
        """Go to next step."""
        if self.current_step < len(self.steps) - 1:
            self._show_step(self.current_step + 1)
    
    def _update_config(self, section: str, key: str, value: Any):
        """Update configuration value."""
        self.config[section][key] = value
        if self.current_step == 5:  # Review step
            self._update_review_content()
    
    def _update_speed_range(self, speed_range: list):
        """Update speed range configuration."""
        self.config["human_movement"]["speed_range"] = speed_range
        if self.current_step == 5:  # Review step
            self._update_review_content()
    
    def _update_color_preview(self):
        """Update loot color preview."""
        try:
            color = self.loot_color_var.get()
            if color.startswith('#'):
                color = color[1:]
            rgb = jake.color_utils.hex_to_rgb(color)
            hex_color = f"#{color}"
            self.color_preview.config(bg=hex_color)
        except:
            self.color_preview.config(bg="white")
    
    def _update_target_color_preview(self):
        """Update target color preview."""
        try:
            color = self.target_color_var.get()
            if color.startswith('#'):
                color = color[1:]
            rgb = jake.color_utils.hex_to_rgb(color)
            hex_color = f"#{color}"
            self.target_color_preview.config(bg=hex_color)
        except:
            self.target_color_preview.config(bg="white")
    
    def _pick_loot_color(self):
        """Pick loot color using color chooser."""
        color = colorchooser.askcolor(title="Pick Loot Color")[1]
        if color:
            # Convert RGB to hex
            hex_color = color[1:]  # Remove #
            self.loot_color_var.set(hex_color)
            self._update_config("loot_pickup", "loot_color", hex_color)
            self._update_color_preview()
    
    def _pick_target_color(self):
        """Pick target color using color chooser."""
        color = colorchooser.askcolor(title="Pick Target Color")[1]
        if color:
            # Convert RGB to hex
            hex_color = color[1:]  # Remove #
            self.target_color_var.set(hex_color)
            self._update_config("combat", "default_target_color", hex_color)
            self._update_target_color_preview()
    
    def _select_health_bar_position(self):
        """Select health bar position with overlay."""
        def get_position():
            # Create overlay for position selection
            self._create_position_selection_overlay("health_bar", "Select Health Bar Position")
            
            # Check if canvas was created successfully
            if self.selection_canvas:
                # Instructions for click-based selection
                self.selection_canvas.create_text(10, 70, text="Click on the health bar pixel (green #048834)", 
                                                fill="white", font=("Arial", 10), anchor="nw")
                self.selection_canvas.create_text(10, 90, text="Press Enter to confirm, Escape to cancel", 
                                                fill="white", font=("Arial", 10), anchor="nw")
                
                # Bind click event for position capture
                self.selection_canvas.bind("<Button-1>", self._on_health_bar_click)
        
        # Show instructions
        messagebox.showinfo("Health Bar Position", 
                           "Click OK, then click on the health bar pixel (green #048834)\n"
                           "The pixel will be captured when you click.")
        get_position()
    
    def _on_health_bar_click(self, event):
        """Handle health bar position click."""
        x, y = event.x, event.y
        rgb_color = jake.screenshot_utils.get_pixel_color_at_position(x, y)
        hex_color = jake.color_utils.rgb_to_hex(rgb_color)
        
        # Update configuration
        self.config["health_bar"]["x"] = x
        self.config["health_bar"]["y"] = y
        self.config["health_bar"]["color"] = hex_color
        
        # Update GUI
        self._update_health_bar_display(x, y, hex_color)
        
        # Close overlay
        self._close_overlay()
        
        # Show confirmation
        messagebox.showinfo("Position Selected", f"Health bar position set to ({x}, {y}) with color #{hex_color}")
    
    def _update_health_bar_display(self, x: int, y: int, color: str):
        """Update health bar display and drawn elements."""
        self.health_pos_var.set(f"Position: ({x}, {y})\nColor: #{color}")
        
        # Update drawn elements
        self._update_drawn_elements()
        
        # Redraw persistent elements if overlay is active
        if self.overlay_window:
            self._draw_persistent_elements()
    
    def _clear_health_bar_position(self):
        """Clear health bar position configuration."""
        self.config["health_bar"]["x"] = None
        self.config["health_bar"]["y"] = None
        self.config["health_bar"]["color"] = None
        self.health_pos_var.set("Not configured")
        
        # Update drawn elements
        self.drawn_elements['health_bar'] = None
        if self.overlay_window:
            self._draw_persistent_elements()
    
    def _select_food_area(self):
        """Select food area with overlay."""
        self._create_area_selection_overlay("food_area", "Select Food Area")
    
    def _clear_food_area(self):
        """Clear food area configuration."""
        self.config["food_area"]["coordinates"] = None
        self.food_area_var.set("Not configured")
        
        # Update drawn elements
        self.drawn_elements['food_area'] = None
        if self.overlay_window:
            self._draw_persistent_elements()
    
    def _select_inventory_area(self):
        """Select inventory area with overlay."""
        self._create_area_selection_overlay("inventory_area", "Select Inventory Area")
    
    def _clear_inventory_area(self):
        """Clear inventory area configuration."""
        self.config["loot_pickup"]["inventory_area"] = None
        self.inventory_area_var.set("Not configured")
        
        # Update drawn elements
        self.drawn_elements['inventory_area'] = None
        if self.overlay_window:
            self._draw_persistent_elements()
    
    def _create_area_selection_overlay(self, config_key: str, title: str):
        """Create overlay window for area selection."""
        # Find RuneScape window
        window_region = jake.screenshot_utils.find_runescape_window("RuneLite")
        if not window_region:
            messagebox.showerror("Error", "RuneScape window not found. Make sure RuneLite is running.")
            return
        
        # Create overlay window
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title(title)
        self.overlay_window.geometry(f"{window_region[2]}x{window_region[3]}+{window_region[0]}+{window_region[1]}")
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.3)
        self.overlay_window.overrideredirect(True)
        
        # Create canvas for drawing
        self.selection_canvas = tk.Canvas(self.overlay_window, width=window_region[2], height=window_region[3], 
                                        bg='black', highlightthickness=0)
        self.selection_canvas.pack()
        
        # Draw persistent elements
        self._draw_persistent_elements()
        
        # Bind mouse events
        self.selection_canvas.bind("<Button-1>", self._on_selection_start)
        self.selection_canvas.bind("<B1-Motion>", self._on_selection_drag)
        self.selection_canvas.bind("<ButtonRelease-1>", self._on_selection_end)
        
        # Add instructions
        self.selection_canvas.create_text(10, 30, text="Click and drag to select area", 
                                        fill="white", font=("Arial", 12, "bold"), anchor="nw")
        self.selection_canvas.create_text(10, 50, text="Press Enter to confirm, Escape to cancel", 
                                        fill="white", font=("Arial", 10), anchor="nw")
        
        # Bind keyboard events
        self.overlay_window.bind("<Return>", self._on_selection_confirm)
        self.overlay_window.bind("<Escape>", lambda e: self._close_overlay())
        
        # Store config key for later use
        self.current_config_key = config_key
    
    def _create_position_selection_overlay(self, config_key: str, title: str):
        """Create overlay window for position selection."""
        # Find RuneScape window
        window_region = jake.screenshot_utils.find_runescape_window("RuneLite")
        if not window_region:
            messagebox.showerror("Error", "RuneScape window not found. Make sure RuneLite is running.")
            return
        
        # Create overlay window
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title(title)
        self.overlay_window.geometry(f"{window_region[2]}x{window_region[3]}+{window_region[0]}+{window_region[1]}")
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.3)
        self.overlay_window.overrideredirect(True)
        
        # Create canvas for drawing
        self.selection_canvas = tk.Canvas(self.overlay_window, width=window_region[2], height=window_region[3], 
                                        bg='black', highlightthickness=0)
        self.selection_canvas.pack()
        
        # Draw persistent elements
        self._draw_persistent_elements()
        
        # Add instructions
        self.selection_canvas.create_text(10, 30, text="Position your mouse on the target pixel", 
                                        fill="white", font=("Arial", 12, "bold"), anchor="nw")
        self.selection_canvas.create_text(10, 50, text="Position will be captured in 3 seconds", 
                                        fill="white", font=("Arial", 10), anchor="nw")
        
        # Store config key for later use
        self.current_config_key = config_key
    
    def _on_selection_start(self, event):
        """Handle selection start."""
        self.selection_start = (event.x, event.y)
        self.selection_end = (event.x, event.y)
    
    def _on_selection_drag(self, event):
        """Handle selection drag."""
        if self.selection_start:
            self.selection_end = (event.x, event.y)
            self._draw_selection()
    
    def _on_selection_end(self, event):
        """Handle selection end."""
        if self.selection_start and self.selection_end:
            self._draw_selection()
    
    def _draw_selection(self):
        """Draw the current selection rectangle."""
        if not self.selection_canvas or not self.selection_start or not self.selection_end:
            return
        
        # Clear previous selection
        self.selection_canvas.delete("selection")
        
        # Draw new selection
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # Rectangle
        self.selection_canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2, tags="selection")
        
        # Dimensions text
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        text_x = min(x1, x2) + width // 2
        text_y = min(y1, y2) + height // 2
        self.selection_canvas.create_text(text_x, text_y, text=f"{width} x {height}", 
                                        fill='red', font=('Arial', 12, 'bold'), tags="selection")
    
    def _on_selection_confirm(self, event):
        """Confirm area selection."""
        if self.selection_start and self.selection_end:
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end
            
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            coords = [x1, y1, x2, y2]
            
            # Update configuration based on current step
            if self.current_config_key == "food_area": # Food area step
                self._update_config("food_area", "coordinates", coords)
                self.food_area_var.set(f"Area: ({x1}, {y1}) to ({x2}, {y2})")
                
                # Update drawn elements
                self.drawn_elements['food_area'] = tuple(coords)
                
            elif self.current_config_key == "inventory_area": # Loot pickup step
                self._update_config("loot_pickup", "inventory_area", coords)
                self.inventory_area_var.set(f"Area: ({x1}, {y1}) to ({x2}, {y2})")
                
                # Update drawn elements
                self.drawn_elements['inventory_area'] = tuple(coords)
            
            # Redraw persistent elements
            self._draw_persistent_elements()
            
            messagebox.showinfo("Area Selected", f"Area selected: ({x1}, {y1}) to ({x2}, {y2})")
        
        self._close_overlay()
    
    def _on_selection_cancel(self, event):
        """Cancel area selection."""
        self._close_overlay()
    
    def _close_overlay(self):
        """Close the overlay window."""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.selection_canvas = None
            self.selection_start = None
            self.selection_end = None
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            config_file = self.config_file
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            messagebox.showinfo("Configuration Saved", f"Configuration saved to {config_file}")
            print(f"Configuration saved to {config_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            print(f"Error saving configuration: {e}")
    
    def _load_config(self):
        """Load existing configuration if available."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with current config
                for key, value in loaded_config.items():
                    if key in self.config:
                        if isinstance(value, dict) and isinstance(self.config[key], dict):
                            self.config[key].update(value)
                        else:
                            self.config[key] = value
                    else:
                        self.config[key] = value
                
                print("Configuration loaded from bot_config.json")
                
                # Initialize drawn elements from loaded config
                self._update_drawn_elements()
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()

def main():
    """Main function."""
    args = parse_arguments()
    app = ConfigGUI(args.config)
    app.run()

if __name__ == "__main__":
    main() 