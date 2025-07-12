# RuneScape Bot

A Python-based bot that monitors the RuneScape game window and can automatically click on elements using computer vision.

## Features

- **Window Detection**: Automatically finds and monitors the RuneScape window
- **Color-Based Targeting**: Find and click on pixels by hex color
- **Smart Pixel Selection**: Blob detection with green exclusion for better targeting
- **Template Matching**: Uses OpenCV to find specific elements on screen
- **Automated Clicking**: Clicks on detected elements using PyDirectInput (game-compatible)
- **Template Creation**: Easy-to-use template creation system
- **Combat Monitoring**: Automatic health monitoring and food consumption
- **Safety Features**: Failsafe mechanisms and easy exit options

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Additional Windows Dependencies** (for window detection):
   ```bash
   pip install pywin32
   ```

## Usage

### 1. Basic Setup

1. Start RuneScape and make sure it's visible on your screen
2. Run the main bot script:
   ```bash
   python runescape_bot.py
   ```

### 2. Creating Templates

Before the bot can click on elements, you need to create templates (images) of what you want it to recognize:

1. Run the template creator:
   ```bash
   python template_creator.py
   ```

2. Or manually save screenshots in the `templates/` folder with descriptive names (e.g., `tree.png`, `fishing_spot.png`)

### 3. Using the Bot

1. Choose option 1 to start the attack bot
2. Enter the target hex color (e.g., "00FFFFFA" for blue targets)
3. Choose pixel selection method:
   - **Smart**: Blob-based selection that excludes targets adjacent to green
   - **Random**: Original random pixel selection
4. Configure food area for auto-eating (optional)
5. The bot will continuously find targets and attack
6. Press 'q' to quit the bot

## How It Works

### Window Monitoring
- Uses `win32gui` to find the RuneScape window by title
- Captures only the game window region for efficiency
- Continuously monitors the window for changes

### Color-Based Targeting
- **Random Selection**: Finds all pixels matching a hex color and randomly selects one
- **Smart Selection**: Uses blob detection to find connected components of the target color
- **Green Exclusion**: Excludes blobs that are adjacent to green pixels (health bars)
- **Blob Analysis**: Uses scipy's connected component labeling and morphological operations

### Template Matching
- Uses OpenCV's template matching algorithm
- Compares saved template images with the current screen
- Configurable threshold for matching accuracy (default: 0.8)

### Clicking
- Uses PyDirectInput for reliable game input
- Calculates absolute screen coordinates from relative positions
- Supports left-click, right-click, and double-click

### Combat Monitoring
- Monitors health bar color changes to detect combat status
- Automatically consumes food when health is low
- Waits for mob death before targeting next enemy

## Configuration

### Adjusting Sensitivity
In `runescape_bot.py`, you can modify:
- `threshold`: Template matching accuracy (0.0-1.0, higher = more strict)
- `interval`: How often to scan for elements (in seconds)

### Window Title
Change `self.window_title` in the `RuneScapeBot` class if your RuneScape window has a different title.

## Safety Features

- **Failsafe**: Move mouse to top-left corner to stop the bot
- **Easy Exit**: Press 'q' to quit
- **Error Handling**: Graceful handling of missing windows/templates

## File Structure

```
runescape-pro/
├── runescape_bot.py      # Main bot script
├── pixel_selection.py    # Smart pixel selection logic
├── color_utils.py        # Color matching utilities
├── screenshot_utils.py   # Screenshot capture utilities
├── mouse_movement.py     # Natural mouse movement
├── template_creator.py   # Template creation utility
├── test_pixel_selection.py # Test script for pixel selection
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── health_bar_config.txt # Health bar position config
├── food_area_config.txt  # Food area configuration
└── templates/           # Template images folder
    ├── tree.png
    ├── fishing_spot.png
    └── ...
```

## Common Use Cases

### Woodcutting Bot
1. Create a template of a tree
2. Set the bot to monitor for the tree template
3. Bot will click on trees when they appear

### Fishing Bot
1. Create a template of a fishing spot
2. Set the bot to monitor for fishing spots
3. Bot will click on fishing spots when available

### Combat Bot
1. Enter the hex color of your target (e.g., "00FFFFFA" for blue enemies)
2. Choose smart pixel selection to avoid clicking on health bars
3. Configure food area for auto-eating
4. Bot will automatically find, attack, and monitor combat

## Troubleshooting

### "Could not find RuneScape window"
- Make sure RuneScape is running and visible
- Check if the window title contains "RuneScape"
- Try running as administrator if needed

### "Template not found"
- Create templates using the template creator
- Ensure template images are in the `templates/` folder
- Check that template names match exactly

### Bot not clicking accurately
- Adjust the `threshold` value (try 0.7-0.9)
- Make sure templates are clear and distinctive
- Check that the game window hasn't moved

### Performance issues
- Increase the `interval` between scans
- Use smaller, more specific templates
- Close unnecessary applications

## Legal Notice

⚠️ **Important**: Using bots in RuneScape may violate the game's Terms of Service and could result in account bans. This tool is for educational purposes only. Use at your own risk.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes only. 