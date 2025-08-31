# Virtual Cursor - Circular Mouse Movement Automation

A Python-based automation tool that moves your mouse cursor in a perfect circle for a specified duration. Built with PyAutoGUI and designed with safety features and interrupt capabilities.

## ✨ Features

- **Circular Movement**: Smooth, mathematically precise circular mouse movement
- **Duration Control**: Configurable animation duration (default: 5 seconds)
- **Center Positioning**: Automatically centers the circle on current cursor position
- **Interrupt Safety**: Press ESC to immediately stop movement, or use Ctrl+C
- **Position Restoration**: Automatically returns cursor to starting position
- **Progress Tracking**: Real-time progress indicators during animation
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the program:**
   ```bash
   python main.py
   ```

### Usage

1. Position your mouse cursor where you want the center of the circle to be
2. Run the script: `python circular_mouse.py`
3. Press ENTER when prompted to start the animation
4. Watch your cursor move in a perfect circle for 5 seconds
5. Press ESC at any time to interrupt the movement

## 📋 Technical Details

### Configuration

Key parameters can be modified in `circular_mouse.py`:

```python
RADIUS = 100        # Circle radius in pixels
DURATION = 5.0      # Animation duration in seconds
FPS = 30           # Frames per second (smoothness)
```

### Mathematical Implementation

The circular movement uses parametric circle equations:
- `x = center_x + radius * cos(angle)`
- `y = center_y + radius * sin(angle)`

Where the angle increments smoothly over time to create fluid motion.

### Safety Features

- **Fail-safe Protection**: PyAutoGUI's built-in corner fail-safe
- **Keyboard Interrupts**: ESC key and Ctrl+C support
- **Position Restoration**: Returns cursor to original position
- **Error Handling**: Graceful error recovery and cleanup
- **User Confirmation**: Requires explicit confirmation before starting

## 🛠️ Dependencies

- **PyAutoGUI** (≥0.9.54): Cross-platform GUI automation
- **keyboard** (≥0.13.5): Keyboard event detection for ESC interrupt

### System Requirements

| Platform | Additional Notes |
|----------|------------------|
| **macOS** | No additional setup required |
| **Windows** | No additional setup required |
| **Linux** | May require: `python3-tk`, `python3-dev`, `scrot`, `python3-xlib` |

## 🎮 Controls

| Key/Action | Function |
|------------|----------|
| **ENTER** | Start circular movement |
| **ESC** | Interrupt movement immediately |
| **Ctrl+C** | Force stop program |
| **Mouse to corner** | PyAutoGUI fail-safe activation |

## 📊 Program Output

```
==================================================
Circular Mouse Movement Automation
==================================================

SAFETY NOTE: This script will control your mouse cursor.
Make sure you're ready before proceeding.
The cursor will move in a circle for 5 seconds.

Press ENTER to start the circular movement (or Ctrl+C to cancel)...

Starting circular movement centered at (640, 360)
Circle radius: 100 pixels
Duration: 5.0 seconds
Press ESC to interrupt the movement at any time...

Starting circular movement...
Time elapsed: 1.0s
Time elapsed: 2.0s
Time elapsed: 3.0s
Time elapsed: 4.0s
Time elapsed: 5.0s

Completed 5.0-second circular movement!
Restoring cursor to original position (640, 360)
Circular movement complete!

Program completed successfully!
```

## 🔧 Troubleshooting

### Common Issues

**Import Errors:**
```bash
pip install --upgrade pyautogui keyboard
```

**Permission Errors on Linux:**
```bash
sudo pip install -r requirements.txt
```

**macOS Security Permissions:**
- Grant accessibility permissions in System Preferences → Security & Privacy → Privacy → Accessibility

**Movement Too Fast/Slow:**
- Modify the `FPS` constant in `circular_mouse.py`
- Higher FPS = smoother but more CPU intensive
- Lower FPS = less smooth but more efficient

## 🎯 Use Cases

- **Screen Recording Demos**: Create smooth circular mouse movements for tutorials
- **Mouse Testing**: Test mouse hardware and software responsiveness
- **Automation Testing**: Verify cursor tracking in applications
- **Screensaver Prevention**: Keep system active during presentations
- **Accessibility Tools**: Automated mouse movement for accessibility needs

## 🔄 Customization Examples

### Change Circle Size
```python
RADIUS = 200  # Larger circle
```

### Longer Duration
```python
DURATION = 10.0  # 10-second animation
```

### Higher Smoothness
```python
FPS = 60  # Ultra-smooth 60 FPS movement
```

### Multiple Rotations
Modify the angle increment calculation:
```python
# For 3 complete rotations over duration
angle_increment = (6 * math.pi) / (DURATION * FPS)
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional movement patterns (figure-8, spiral, etc.)
- GUI interface for parameter adjustment
- Multiple monitor support
- Movement recording and playback
- Speed ramping (slow start/stop)

## 📄 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

This tool is designed for legitimate automation and testing purposes. Users are responsible for complying with their organization's policies and local laws regarding automated mouse control. Always ensure you have proper authorization before running automation scripts on shared or managed systems.

---

**Created with Python 3 • PyAutoGUI • Mathematical Precision**
