# VU1 Dials GUI

## Overview

VU1 Dials GUI is a PyQt6-based graphical user interface (GUI) designed for managing and controlling dial displays, specifically tailored for integration with AIDA64 sensor data. The application enables real-time monitoring and control of dial settings, backlights, sensor assignments, and value ranges, providing an intuitive platform for system monitoring and display customization.

Note: This application is specifically built for the Streacom VU1 DIALs and requires the corresponding hardware along with the VU1 Server to function. For more information, visit vudials.com.

The GUI works exclusively with AIDA64 from FinalWire. For more details, visit AIDA64. Make sure to enable the Shared Memory feature in AIDA64 and select a set of sensors to share via the application settings. Without this configuration, the GUI will not function properly.

An extensive documentation of the VU1 API Server can be found at docs.vudials.com. The server and its source code, developed by Saša Karanović, are available on GitHub.

## Features

Dial Management: Create, update, and manage multiple dials.

AIDA64 Integration: Fetch and assign AIDA64 sensor data to dials.

### Customizable Settings:

Backlight control with RGB sliders and color picker.

Easing parameters for smooth updates.

Adjustable value ranges for dial mapping.

Image Uploads: Upload custom images for dials.

Settings Persistence: Save and load user settings and assignments via JSON files.

System Tray Support: Minimize the application to the system tray with options for autostart and minimized start.

Platform Compatibility: Windows-focused with features like Windows Registry integration for autostart.

## Requirements

None. A precompiled version is provided for Windows systems.

## Installation

Download the precompiled executable from the Releases section and run it directly. No installation or dependencies are required.

## Usage

Start the application by running the downloaded executable.

If required, configure the server address and API key via the Settings dialog.

Ensure the Shared Memory feature is enabled in AIDA64, and a set of sensors is selected for sharing.

### Use the interface to:

Create and configure dials.

Assign AIDA64 sensors.

Customize dial backlights and ranges.

Minimize the application to the system tray for background operation.

## File Structure

settings.json: Stores user preferences and configurations.

assignments.json: Stores dial assignments, value ranges, and backlight settings.

## Customization

### Dials:

Add custom images by selecting the "Set Image" option.

Configure RGB backlights using sliders or the color picker.

Define value ranges and easing parameters for dial behavior.

### Settings:

Enable or disable autostart through the Settings dialog.

Adjust AIDA64 sensor integration as needed.

## Releases

A precompiled, standalone version for Windows systems is available under the "Releases" section. This version requires no installation and can be run directly.

## Known Issues

Ensure the server address and API key are correctly configured; otherwise, sensor data and dial updates may fail.

AIDA64 must be running and configured to expose sensor data for integration.

### Legal Disclaimer

No Warranty: This software is provided "as-is," without any express or implied warranties. The developer is not responsible for any damages or data loss resulting from the use of this software.

Third-Party Dependencies: The application depends on AIDA64, Streacom VU1 hardware, and the VU1 Server. The developer is not liable for any issues caused by changes or outages in these third-party services or products.

Use at Your Own Risk: Users assume all responsibility for using this software. Proper configuration of hardware and dependencies is required for correct operation.

Data Privacy: Users must ensure compliance with local data privacy laws when processing sensor data.

Trademarks: All trademarks and logos, including AIDA64 and Streacom, are property of their respective owners. The developer is not affiliated with FinalWire or Streacom.

### Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests.

### License

This project is licensed under the MIT License. See the LICENSE file for details.

### Support

For issues or questions, please open an issue in the GitHub repository or contact the project maintainer.

# Happy Monitoring!

