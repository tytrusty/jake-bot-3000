# JAKE BOT 2000

A Python-based RuneScape bot with human-like mouse movement based on my dear friend Jake

## Features

- Human-like mouse movement using machine learning
- Automatic target detection and combat
- Loot pickup with clustering algorithms
- Health monitoring and auto-eating
- Configurable speed ranges for movement variability
- Interactive setup tools for game areas

## Dependencies

- Python 3.9+
- NumPy, SciPy, scikit-learn (machine learning)
- OpenCV, Pillow (image processing)
- PyAutoGUI, PyDirectInput (automation)
- pywin32 (Windows integration)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tytrusty/rs-bot.git
cd runescape-pro
```

2. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate jake
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

Run the interactive bot:
```bash
python examples/runescape_bot_example.py
```

Or use the simple example:
```bash
python examples/simple_example.py
```

## License

MIT License 