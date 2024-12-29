# Rasklad Geotag

## Overview
Rasklad Geotag is a photo geotagging application built with PyQt6. It allows users to manage and update the EXIF coordinates of image files using an interactive map.

## Differences from others

- Simplificated interface for quick iteractions with many of files
- Already geotagged files if not interactive on map, it speed up of entering

## Features
- **EXIF Coordinates Management**: Add, remove, and save EXIF coordinates to image files.
- **Interactive Map**: Use a map to add and drag markers to update coordinates.
- **Coordinate Filter**: Option to filter and display only files without coordinates.

## Dependencies
- PyQt6
- exif

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/trolleway/rasklad_geotag.git
   ```
2. Navigate to the project directory:
   ```sh
   cd rasklad_geotag
   ```
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```sh
   python main.py
   ```
2. Select a folder containing image files using the "Select Folder" button.
3. View and manage images and their EXIF coordinates.

## Classes and Methods
### `CustomWebEnginePage(QWebEnginePage)`
Handles JavaScript console messages.

### `JavaScriptHandler(QObject)`
Handles communication between JavaScript and Python for coordinate updates.

### `MapWidget(QWebEngineView)`
Displays the interactive map and manages JavaScript interactions.
- `get_initial_map()`: Returns the initial HTML for the Leaflet map.

### `RaskladGeotag(QMainWindow)`
Main application window.
- `initUI()`: Initializes the user interface.
- `toggle_filter()`: Toggles the filter to hide/display files with coordinates.
- `add_marker(lat=None, lon=None)`: Adds a marker to the map.
- `update_coordinates_label(lat, lon)`: Updates the coordinates label with the selected file's coordinates.
- `save2exif()`: Saves the updated coordinates to the EXIF data of the image.
- `open_folder_dialog()`: Opens a dialog to select a folder.
- `read_files_data(folder_path)`: Reads and processes image files in the selected folder.
- `display_files(folder_path)`: Displays the files in the table.
- `display_image()`: Displays the selected image.
- `format_date(timestamp)`: Formats the date from the file's modification time.

## License
[GPL V3 License](LICENSE)

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

For more details, see the source code in `main.py`.