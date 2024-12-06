# Lily58 OLED Configurator

A GUI application for configuring both OLED displays on Lily58 keyboards. This tool provides an intuitive interface for uploading text and images to your keyboard's OLED displays with support for rotation and independent display control.

## Features

- Dual OLED Support:
  - Independent control of left and right OLED displays
  - Separate tabs for each display configuration
  - Real-time preview for both displays

- Text Mode:
  - Custom text input with precise positioning
  - Rotation support in 45° increments (0° to 315°)
  - Real-time preview of text appearance
  - Pixel-perfect positioning using X/Y coordinates

- Image Mode:
  - Support for common image formats (PNG, JPG, BMP, GIF)
  - Image rotation in 45° increments
  - Automatic image conversion to monochrome
  - Automatic resizing to fit OLED dimensions
  - Live preview before applying

## Prerequisites

### Firmware Requirements

Before using this tool, ensure your Lily58's firmware meets these requirements:

1. QMK Firmware with OLED Support:
   ```c
   // In rules.mk
   OLED_ENABLE = yes
   ```

2. Proper OLED Driver Initialization:
   ```c
   // In config.h
   #define OLED_DISPLAY_128X32
   #define I2C_DRIVER I2CD1
   #define I2C1_SCL_PIN B6
   #define I2C1_SDA_PIN B7
   ```

3. VIA Support:
   ```c
   // In rules.mk
   VIA_ENABLE = yes
   ```

### Hardware Setup

1. ProMicro Configuration:
   - Verify I2C pins are correctly connected to OLED displays
   - Check OLED power connections
   - Ensure proper ground connections

2. OLED Display Connections:
   - SDA and SCL lines properly connected
   - VCC and GND properly connected
   - No shorts or loose connections

## Installation

1. Ensure Python 3.7+ is installed on your system
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Linux users may need to add udev rules for HID access:
   ```bash
   echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="eb2d", MODE="0666"' | sudo tee /etc/udev/rules.d/50-lily58.rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

## Usage

1. Launch the application:
   ```bash
   python oled_configurator.py
   ```

2. Connect to Your Lily58:
   - Click "Connect to Lily58" to establish connection
   - The application will automatically detect your keyboard
   - Connection status is shown in the top bar

3. Configure Left/Right OLED:
   - Select the tab for the OLED you want to configure
   - Choose between Text or Image mode

4. Text Mode:
   - Enter your desired text
   - Set X and Y coordinates for text position (0,0 is top-left)
   - Select rotation angle (0° to 315° in 45° increments)
   - Click "Preview" to see how it will look
   - Click "Apply to OLED" when satisfied

5. Image Mode:
   - Click "Select Image" to choose an image file
   - Select desired rotation angle
   - Preview will show how it will appear on the OLED
   - Click "Apply to OLED" when satisfied

## Troubleshooting

1. OLED Not Displaying:
   - Verify QMK firmware has OLED support enabled
   - Check I2C pin configurations in firmware
   - Verify OLED power and data connections
   - Reflash ProMicro with updated firmware if needed

2. Connection Issues:
   - Ensure your Lily58 is properly connected
   - Check that udev rules are properly set up (Linux)
   - Try unplugging and reconnecting the keyboard
   - Verify the keyboard is in VIA-compatible mode

3. Display Issues:
   - Make sure the preview looks correct before applying
   - Text positioning uses pixel coordinates (0,0 is top-left)
   - Large rotated text might be clipped
   - If display is garbled, check I2C communication

## Technical Details

### Lily58 Keyboard Specifications
- Vendor ID: 0x04D8
- Product ID: 0xEB2D
- VIA Protocol Version: 0x0C
- OLED Display: 128x32 pixels (each side)

### Communication Protocol

The application uses VIA HID protocol for OLED communication:

```
Report Structure:
[Report ID (0x00)] [OLED Command (0x40)] [OLED Select] [Chunk Index] [Data...]

- Report ID: 0x00
- OLED Command: 0x40
- OLED Select: 0x01 (Left) or 0x02 (Right)
- Chunk Index: Sequential chunk number (0xFF for completion)
- Data: Image data, 1 bit per pixel, packed into bytes
```

Data is sent in chunks to comply with HID report size limitations (32 bytes per report).

### Image Processing
- Images are automatically converted to monochrome
- Rotation is applied before resizing
- Images are resized to fit the OLED dimensions
- Dithering is applied for better representation of grayscale images

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use and modify as needed.
