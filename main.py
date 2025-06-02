import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QLabel,
    QSizePolicy,
    QListWidget,
    QMenuBar,
    QDialog,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QInputDialog,
    QProgressBar,
    QStyle,
    QFrame,
     QTabWidget,
    QGroupBox,
)
from PyQt6.QtCore import (
    Qt,
    QDir,
    QObject,
    pyqtSlot,
    pyqtSignal,
    QEvent,
    QSettings,
    QRectF,
)
from PyQt6.QtGui import QPixmap, QKeyEvent, QAction, QPainter, QPen, QBrush, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
import exif
from exiftool import ExifToolHelper  # when python library failed
import shapely.wkt
import shapely.geometry
import math


class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f"JavaScript console message: {message} (line: {line_number})")


class JavaScriptHandler(QObject):
    coordinatesUpdated = pyqtSignal(str, str)

    @pyqtSlot(str, str)
    def coordinatesUpdatedSlot(self, lat, lng):
        self.coordinatesUpdated.emit(lat, lng)


class CustomProgressBar(QProgressBar):
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = QRectF(
            10, 8, self.width() - 20, self.height() - 15
        )  # Define the rectangle for the progress bar

        # Draw background rectangle
        painter.setBrush(QBrush(QColor(254, 232, 200)))
        painter.drawRect(rect)

        # Draw scale 80%
        progress_width = (self.width() - 20) * (80 / 100.0)
        progress_rect = QRectF(
            progress_width, self.height() - 8, self.width() - progress_width - 10, 4
        )
        painter.setBrush(QBrush(QColor(253, 187, 132)))
        painter.drawRect(progress_rect)

        # Draw progress rectangle
        progress_width = (self.width() - 20) * (self.value() / 100.0)
        progress_rect = QRectF(10, 8, progress_width, self.height() - 15)
        painter.setBrush(QBrush(QColor(166, 216, 84)))
        painter.drawRect(progress_rect)

        # Draw text
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value()}%")


class MapWidget(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.setPage(CustomWebEnginePage(self))
        self.channel = QWebChannel()
        self.jsHandler = JavaScriptHandler()

        self.channel.registerObject("jsHandler", self.jsHandler)
        self.page().setWebChannel(self.channel)

        self.setHtml(self.get_initial_map())

    def get_initial_map(self):
        leaflet_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Leaflet Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style> #map { width: 100%; height: 100%; } </style>
        </head>
        <body>
            <div id="map" style="height: 500px;"></div>
            <div id="coordinates">Coordinates: </div>
            <script>
                var map = L.map('map',{
            wheelPxPerZoomLevel: 10 // Add this option
        }).setView([55.666, 37.666], 11);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

                
                var markers = [];

                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.jsHandler = channel.objects.jsHandler;
                    console.log("Channel initialized");
                });

                function removeMarkers() {
                    //console.log("current count of markers "+markers.length+", start delete);
                    for (var i = 0; i < markers.length; i++) {
                        map.removeLayer(markers[i]);
                        
                    }
                    // Clear the markers array
                    markers = [];
                    //console.log("after delete markers is  "+markers.length);
                }
                function addMarker(position, markerclass, draggable=true) {
                   console.log("adding marker draggable = "+draggable);
                    // Custom  icon
                    var destIcon = L.icon({
                        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHg9IjMiIHk9IjMiIHdpZHRoPSI5NCIgaGVpZ2h0PSI5NCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSI2IiBzdHJva2UtbWl0ZXJsaW1pdD0iMi42MTMxMyIvPgo8cGF0aCBkPSJNNTAgMFYxMDAiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMyIvPgo8cGF0aCBkPSJNMCA1MEMyLjgxNDA3IDUwIDY3LjgzOTIgNTAgMTAwIDUwIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjMiLz4KPC9zdmc+Cg==', // Base64 encoded SVG
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    });
                    var imageIcon = L.icon({
                        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAzMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjQjU2RDJEIi8+Cjwvc3ZnPgo=', // Base64 encoded SVG
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    });

                    // Create a marker at the the map
                    if (markerclass==='dest'){var icon=destIcon};
                    if (markerclass==='image'){var icon=imageIcon};
                    var marker = L.marker(position, {
                    draggable: draggable,
                    autoPan: true,
                    icon: icon
                    }).addTo(map);
                    

                    marker.on('dragend', function(e) {
                        var coords = e.target.getLatLng();
                        document.getElementById('coordinates').innerText = "Coordinates: " + coords.lat.toFixed(7) + ", " + coords.lng.toFixed(7);
                        if (window.jsHandler) {
                            //console.log("Sending coordinates to channel: " + coords.lat.toFixed(4) + ", " + coords.lng.toFixed(4));
                            window.jsHandler.coordinatesUpdatedSlot(coords.lat.toFixed(7), coords.lng.toFixed(7));
                        } else {
                            console.log("jsHandler is not defined");
                        }
                    });
                    
                    
                    // Move marker to click location
                    if (draggable) {
                        map.on('click', function(e) {
                            var clickCoords = e.latlng;
                            marker.setLatLng(clickCoords);
                            marker.fire('dragend', { target: marker });
                            document.getElementById('coordinates').innerText = "Coordinates: " + clickCoords.lat.toFixed(7) + ", " + clickCoords.lng.toFixed(7);
                        });
                        }
                    markers.push(marker); // array of markers to remove all markers
                    }
                    function move_to_favorite_place(position, zoom) {
                        map.setView(position, zoom);
                        removeMarkers();
                        addMarker(position,'image');
                    }
                    
            </script>
        </body>
        </html>
        """
        return leaflet_html


class EditFavoritesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Favorites")
        self.setGeometry(150, 150, 400, 300)
        self.layout = QVBoxLayout()
        self.fav_list = QListWidget()
        self.layout.addWidget(self.fav_list)

        self.add_button = QPushButton("Add Favorite")
        self.edit_button = QPushButton("Edit Favorite")
        self.remove_button = QPushButton("Remove Favorite")

        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.edit_button)
        self.layout.addWidget(self.remove_button)

        self.setLayout(self.layout)

        self.add_button.clicked.connect(self.add_favorite)
        self.edit_button.clicked.connect(self.edit_favorite)
        self.remove_button.clicked.connect(self.remove_favorite)

        self.parent = parent
        self.load_favorites()

    def load_favorites(self):
        self.fav_list.clear()
        for fav in self.parent.locationFavs:
            self.fav_list.addItem(f"{fav['key']} {fav['name']}")

    def add_favorite(self):
        key, ok = QInputDialog.getText(
            self, "Add Favorite", "Enter key: One didgit or letter, case insensitive"
        )
        if ok and key:
            name, ok = QInputDialog.getText(self, "Add Favorite", "Enter name:")
            if ok and name:
                wkt_geom = (
                    f"POINT({self.parent.mapMarkerLon} {self.parent.mapMarkerLat})"
                )
                self.parent.locationFavs.append(
                    {"key": key.upper(), "name": name, "wkt_geom": wkt_geom}
                )
                self.save_favorites()
                self.load_favorites()
                self.parent.display_sorted_location_favorites(
                    self.parent.map_fav_widget
                )

    def edit_favorite(self):
        current_item = self.fav_list.currentItem()
        if current_item:
            key, name = current_item.text().split(" ", 1)
            new_key, ok = QInputDialog.getText(
                self,
                "Edit Favorite",
                "Enter new key: One didgit or letter, case insensitive",
                text=key,
            )
            if ok and new_key:
                new_name, ok = QInputDialog.getText(
                    self, "Edit Favorite", "Enter new name:", text=name
                )
                if ok and new_name:
                    for fav in self.parent.locationFavs:
                        if fav["key"] == key and fav["name"] == name:
                            fav["key"] = new_key.upper()
                            fav["name"] = new_name
                            fav["wkt_geom"] = (
                                f"POINT({self.parent.map_widget.center().lng} {self.parent.map_widget.center().lat})"
                            )
                            break
                    self.save_favorites()
                    self.load_favorites()
                    self.parent.display_sorted_location_favorites(
                        self.parent.map_fav_widget
                    )

    def remove_favorite(self):
        current_item = self.fav_list.currentItem()
        if current_item:
            key, name = current_item.text().split(" ", 1)
            self.parent.locationFavs = [
                fav
                for fav in self.parent.locationFavs
                if not (fav["key"] == key and fav["name"] == name)
            ]
            self.save_favorites()
            self.load_favorites()
            self.parent.display_sorted_location_favorites(self.parent.map_fav_widget)

    def save_favorites(self):
        settings = QSettings("Trolleway", "RaskladGeotag")
        settings.setValue("locationFavs", self.parent.locationFavs)


class RaskladGeotag(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rasklad Geotag")
        self.setGeometry(100, 100, 800, 600)
        self.initial_coords = (55.666, 37.666)

        self.mainfiles = []
        self.mainfile_selected = ""
        self.filter_has_coords_enabled = False  # Initial state of the filter

        self.locationFavs = self.load_favorites()
        self.mapMarkerLat = None
        self.mapMarkerLon = None

        self.mode_enter_coordinates = 1
        self.mode_enter_destinations = 2

        self.mode_interface = self.mode_enter_coordinates

        self.initUI()

    def initUI(self):
        widget = QWidget()
        self.setCentralWidget(widget)

        layout_horizontal = QHBoxLayout()
        layout = QVBoxLayout()

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label.setMinimumHeight(400)
        self.label.setScaledContents(True)
        self.label.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )

        self.select_button = QPushButton("Select Folder", self)

        self.select_button.setIcon(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_DirIcon"))
        )
        self.select_button.clicked.connect(self.open_folder_dialog)

        self.save_button = QPushButton("Save coordinates to EXIF", self)
        self.save_button.setIcon(
            self.style().standardIcon(
                getattr(QStyle.StandardPixmap, "SP_DialogSaveButton")
            )
        )
        self.save_button.clicked.connect(self.save2exif)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels(
            ["Filename", "Create Date", "lat", "lon", "dest lat", "dest lon"]
        )
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 180)
        self.table.itemSelectionChanged.connect(self.display_image)
        self.table.installEventFilter(self)
        self.table.setMinimumHeight(300)
        self.table_last_event_timestamp = None

        self.file_path_label = QLabel(self)
        self.file_path_label.setText("Selected File Path: ")

        layout.addWidget(self.select_button)
        layout.addWidget(self.table)
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.label)

        layout_horizontal.addLayout(layout)

        self.map_widget = MapWidget()
        layout_vertical_right = QVBoxLayout()
        layout_vertical_right.addWidget(self.map_widget)

        layout_horizontal.addLayout(layout_vertical_right)
        self.coordinates_label = QLabel("Coordinates: ")
        self.map_widget.jsHandler.coordinatesUpdated.connect(
            self.update_coordinate_in_mainfiles
        )

        self.add_marker_button = QPushButton("Add Marker to Center")
        self.add_marker_button.clicked.connect(self.add_marker)
        layout_vertical_right.addWidget(self.add_marker_button)
        self.map_fav_widget = QListWidget()
        self.map_fav_widget.setFixedHeight(150)
        layout_vertical_right.addWidget(self.map_fav_widget)
        self.coordinate_set_progressBar = CustomProgressBar()
        self.coordinate_set_progressBar.setValue(0)  # Set the percentage value here
        layout_vertical_right.addWidget(self.coordinate_set_progressBar)

        # tab1
        tab_enter_coordinates_mode = QWidget()
        layout_enter_coordinates_mode = QVBoxLayout()
        self.toggle_button = QPushButton("Hide files with coordinates", self)
        self.toggle_button.clicked.connect(self.toggle_filter)
        layout_enter_coordinates_mode.addWidget(self.toggle_button)
        tab_enter_coordinates_mode.setLayout(layout_enter_coordinates_mode)

        # tab2
        tab_enter_dest_coordinates_mode = QWidget()
        layout_enter_dest_coordinates_mode = QVBoxLayout()
        self.dest_coordinates_info = QLabel("Entering destination coordinates")
        layout_enter_dest_coordinates_mode.addWidget(self.dest_coordinates_info)
        tab_enter_dest_coordinates_mode.setLayout(layout_enter_dest_coordinates_mode)

        # tab group
        self.label_mode = QLabel("Mode:")
        layout.addWidget(self.label_mode)
        self.tab_mode = QTabWidget()
        self.tab_mode.addTab(tab_enter_coordinates_mode, "Enter image coordinates")
        self.tab_mode.addTab(tab_enter_dest_coordinates_mode, "Enter dest coordinates")
        self.tab_mode.setCurrentIndex(0)
        self.tab_mode.currentChanged.connect(self.on_tab_change)

        self.tab_mode.setStyleSheet(
            """
            QTabWidget::pane { /* The tab widget frame */
                border: 2px solid black;
                position: absolute;
                top: -0.5em;
            }
            QTabBar::tab {
                background: lightgray;
                border: 1px solid black;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: white;
            }
        """
        )
        layout.addWidget(self.tab_mode)

        layout.addWidget(self.coordinates_label)
        layout.addWidget(self.save_button)

        widget.setLayout(layout_horizontal)
        self.marker_coordinates = None
        self.statusBar().showMessage("Select a directory with images to start")
        self.create_main_menu()
        self.display_sorted_location_favorites(self.map_fav_widget)

    def on_tab_change(self, index):
        js_code = f"removeMarkers();"
        self.map_widget.page().runJavaScript(js_code)
        if index == 0:
            self.switch_mode_enter_coordinates()
        elif index == 1:
            self.switch_mode_enter_destinations()

    def display_sorted_location_favorites(self, map_fav_widget):
        sorted_locationFavs = sorted(
            self.locationFavs, key=lambda x: (x["key"], x["name"])
        )
        map_fav_widget.clear()
        for el in sorted_locationFavs:
            map_fav_widget.addItem(f"{el['key']} {el['name']}")

        if len(self.locationFavs) < 1:
            return
        item_height = self.map_fav_widget.sizeHintForRow(0)

        # Set the fixed height of the QListWidget to match the height of 6 items
        self.map_fav_widget.setFixedHeight(
            item_height * 6 + 2 * self.map_fav_widget.frameWidth()
        )

    def create_main_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Settings")

        edit_favorites_action = QAction("Edit Favorites", self)
        edit_favorites_action.triggered.connect(self.open_edit_favorites_dialog)
        file_menu.addAction(edit_favorites_action)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_edit_favorites_dialog(self):
        dialog = EditFavoritesDialog(self)
        dialog.exec()

    def load_favorites(self):
        settings = QSettings("Trolleway", "RaskladGeotag")
        return settings.value("locationFavs", [])

    def toggle_filter(self):
        self.filter_has_coords_enabled = not self.filter_has_coords_enabled
        if self.filter_has_coords_enabled:
            self.toggle_button.setText("Display all files")
            # Add your filter logic here
            self.display_files(self.folder_path)
            print("Filter enabled")
            self.statusBar().showMessage("Showing only files without coordinates")
        else:
            self.toggle_button.setText("Hide files with coordinates")
            # Remove your filter logic here
            self.display_files(self.folder_path)
            print("Filter disabled")
            self.statusBar().showMessage("Showing all files")

    def switch_mode_enter_destinations(self):
        self.mode_interface = self.mode_enter_destinations
        self.label.setPixmap(QPixmap())  # unload image
        # switch off filter
        self.filter_has_coords_enabled = False
        self.display_files(self.folder_path)

        self.statusBar().showMessage(
            "Switched to destination coordinates entering mode. Set coordinates of image destination"
        )

    def switch_mode_enter_coordinates(self):
        self.label.setPixmap(QPixmap())  # unload image
        self.mode_interface = self.mode_enter_coordinates
        self.display_files(self.folder_path)
        self.statusBar().showMessage("Switched to image coordinates edit mode.")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.table:
            self.keyPressEvent(event)
            return True
        return super().eventFilter(source, event)

    def select_next_file(self, event):
        if event.timestamp() != self.table_last_event_timestamp:
            current_row = self.table.currentRow()
            next_row = current_row + 1
            if next_row < self.table.rowCount():
                self.table.selectRow(next_row)
                self.table.setCurrentCell(next_row, 0)
                self.table_last_event_timestamp = event.timestamp()
                
    def select_prev_file(self, event):
        if event.timestamp() != self.table_last_event_timestamp:
            current_row = self.table.currentRow()
            prev_row = current_row - 1
            if prev_row > 0:
                self.table.selectRow(prev_row)
                self.table.setCurrentCell(prev_row, 0)
                self.table_last_event_timestamp = event.timestamp()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_PageDown, Qt.Key.Key_Down, Qt.Key.Key_Space):
            """somehow the event triggered twice,
            do only if event with this timestamp
            not performed yet
            """
            self.select_next_file(event)
        if event.key() in (Qt.Key.Key_PageUp, Qt.Key.Key_Up):
            """somehow the event triggered twice,
            do only if event with this timestamp
            not performed yet
            """
            self.select_prev_file(event)
            
        key_pressed = event.text()
        for fav in self.locationFavs:
            if fav["key"].upper() == key_pressed.upper():
                event.accept()
                self.statusBar().showMessage(f'You pressed the key for {fav["name"]}')
                # wkt_point = "POINT(37.620393 55.734036)"
                wkt_point = fav.get("wkt_geom")
                if not wkt_point:
                    continue
                retrieved_point = shapely.wkt.loads(wkt_point)
                retrieved_latitude = retrieved_point.y
                retrieved_longitude = retrieved_point.x
                zoom = 16
                js_code = f"move_to_favorite_place([{retrieved_latitude}, {retrieved_longitude}],{zoom});"
                self.map_widget.page().runJavaScript(js_code)
                continue
        super().keyPressEvent(event)

    def add_marker(self, lat=None, lon=None, markerclass="image", nonmoveable=False):
        assert markerclass in ("image", "dest")
        if self.table.currentRow() is None:
            return

        if not lat or not lon:
            self.map_widget.page().runJavaScript("removeMarkers();")
            js_code = f"addMarker(map.getCenter(),'{markerclass}');"
        else:
            if nonmoveable == False:
                self.map_widget.page().runJavaScript("removeMarkers();")
                js_code = f"addMarker([{lat}, {lon}],'{markerclass}');"
            elif nonmoveable == True:
                js_code = f"addMarker([{lat}, {lon}],'{markerclass}',false);"

        self.map_widget.page().runJavaScript(js_code)

    @pyqtSlot(str, str)
    def update_coordinate_in_mainfiles(self, lat, lon):

        if self.mode_interface == self.mode_enter_coordinates:
            attr_lat = "lat"
            attr_lon = "lon"
            table_column_lat = 2
            table_column_lon = 3
        elif self.mode_interface == self.mode_enter_destinations:
            attr_lat = "dest_lat"
            attr_lon = "dest_lon"
            table_column_lat = 4
            table_column_lon = 5

        self.mapMarkerLat = lat
        self.mapMarkerLon = lon
        selected = set([])
        for it in self.table.selectedItems():
            selected.add(it.text())
        for i, f in enumerate(self.mainfiles):
            if f["file_name"] in selected:
                f["modified"][attr_lat] = lat
                f["modified"][attr_lon] = lon
                f["is_modified"] = True

                row_count = self.table.rowCount()
                for row in range(row_count):
                    item = self.table.item(row, 0)  # Get the item in column 0
                    if item and item.text() == f["file_name"]:
                        new_table_item = QTableWidgetItem(f"{lat}")
                        new_table_item.setBackground(QColor("#a6d96a"))

                        self.table.setItem(row, table_column_lat, new_table_item)
                        del new_table_item
                        new_table_item = QTableWidgetItem(f"{lon}")
                        new_table_item.setBackground(QColor("#a6d96a"))
                        self.table.setItem(row, table_column_lon, new_table_item)
                        del new_table_item

                        self.statusBar().showMessage(
                            f"Coordinates: {lat} {lon} for file {f['file_name']} updated. Press Space, Pagedown, or ⇩ to select next file"
                        )
                        break
                # no break here, may be multiple files selected

    def save2exif(self):
        def calculate_heading(lat1, lon1, lat2, lon2):
            lat1 = math.radians(lat1)
            lon1 = math.radians(lon1)
            lat2 = math.radians(lat2)
            lon2 = math.radians(lon2)

            d_lon = lon2 - lon1

            x = math.sin(d_lon) * math.cos(lat2)
            y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)

            initial_bearing = math.atan2(x, y)
            initial_bearing = math.degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360

            return compass_bearing

        def to_deg(value, loc):
            value = float(value)
            if value < 0:
                loc_value = loc[0]
            else:
                loc_value = loc[1]

            abs_value = abs(value)
            deg = int(abs_value)
            temp_min = (abs_value - deg) * 60
            min = int(temp_min)
            sec = round((temp_min - min) * 60, 6)

            return deg, min, sec, loc_value

        result_msg = ""
        for i, f in enumerate(self.mainfiles):
            was_saved_by_exiftool = False
            dest_lat = None
            dest_lon = None
            lat = None
            lon = None
            if f.get("is_modified"):
                lat = f["modified"].get("lat")
                lon = f["modified"].get("lon")
                dest_lat = f["modified"].get("dest_lat")
                dest_lon = f["modified"].get("dest_lon")

                if lat and lon:
                    lat_deg = to_deg(lat, ("S", "N"))
                    lon_deg = to_deg(lon, ("W", "E"))
                    creation_time = os.path.getctime(f["file_path"])
                    mod_time = os.path.getmtime(f["file_path"])
                    """
                    with open(f["file_path"], "rb") as image_file:
                        img = exif.Image(image_file)
                    try:
                        img.gps_latitude = lat_deg[:3]
                        img.gps_latitude_ref = lat_deg[3]
                        img.gps_longitude = lon_deg[:3]
                        img.gps_longitude_ref = lon_deg[3]
                    except:
                        self.coordinates_label.setText(f"EXIF library error")
                        continue
                    """

                if dest_lat and dest_lon:
                    dest_lat_deg = to_deg(dest_lat, ("S", "N"))
                    dest_lon_deg = to_deg(dest_lon, ("W", "E"))
                    creation_time = os.path.getctime(f["file_path"])
                    mod_time = os.path.getmtime(f["file_path"])

                # append to object
                was_saved_by_exiftool = False

                try:
                    tags = dict()
                    if lat and lon:
                        tags["GPSLatitude"] = lat
                        tags["GPSLatitudeRef"] = lat_deg[3]
                        tags["GPSLongitude"] = lon
                        tags["GPSLongitudeRef"] = lon_deg[3]
                    if dest_lat and dest_lon:
                        tags["GPSDestLatitude"] = dest_lat
                        tags["GPSDestLatitudeRef"] = dest_lat_deg[3]
                        tags["GPSDestLongitude"] = dest_lon
                        tags["GPSDestLongitudeRef"] = dest_lon_deg[3]
                        # for heading if main coordinates is changing, use new coordinate, if not changing use old image coords, if not defined - skip tag
                        if lat and lon:
                            tags["GPSImgDirection"] = calculate_heading(float(lat), float(lon), float(dest_lat), float(dest_lon))
                        elif f['lat'] and f['lon']:
                            tags["GPSImgDirection"] = calculate_heading(float(f['lat']), float(f['lon']), float(dest_lat), float(dest_lon))
                        else:
                            pass #not calculate gps direction
                    with ExifToolHelper() as et:
                        et.set_tags(
                            [f["file_path"]],
                            tags=tags,
                            params=["-P", "-overwrite_original"],
                        )
                    self.coordinates_label.setText(f"Saved using exiftool")
                    was_saved_by_exiftool = True
                    continue
                except Exception as e:

                    self.coordinates_label.setText(f"EXIF library error " + str(e))
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    msg_box.setText("Failed to save EXIF data.")
                    msg_box.setInformativeText(f"File: {f['file_name']}")
                    msg_box.setStandardButtons(
                        QMessageBox.StandardButton.Retry
                        | QMessageBox.StandardButton.Ignore
                        | QMessageBox.StandardButton.Cancel
                    )
                    msg_box.setDefaultButton(QMessageBox.StandardButton.Retry)
                    ret = msg_box.exec()

                    if ret == QMessageBox.StandardButton.Retry:
                        continue
                    elif ret == QMessageBox.StandardButton.Ignore:
                        pass
                    elif ret == QMessageBox.StandardButton.Cancel:
                        break
                if was_saved_by_exiftool:
                    f[i]['is_modified']=False

        self.statusBar().showMessage(f"Coordinates saved to EXIF")
        self.updateProgressBar()
        self.display_files(self.folder_path, supress_statusbar=True)

    def updateProgressBar(self):
        has_coords1 = len([f for f in self.mainfiles if f.get("lat")])
        has_coords2 = len(
            [
                f
                for f in self.mainfiles
                if f.get("modified") and f["modified"].get("lat")
            ]
        )
        has_coords = has_coords1 + has_coords2
        total = len(self.mainfiles)
        if total == 0 or has_coords == 0:
            self.coordinate_set_progressBar.setValue(0)
        else:
            self.coordinate_set_progressBar.setValue(round(100 / (total / has_coords)))

    def open_folder_dialog(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if self.folder_path:
            self.mainfiles_init(self.folder_path)
            self.display_files(self.folder_path)

    def mainfiles_init(self, folder_path):
        # initialize mainfiles, read exif from disk
        self.mainfiles = []
        print("mainfiles cleared")
        files = os.listdir(folder_path)
        for i, file_name in enumerate(files):
            if not file_name.lower().endswith(".jpg"):
                continue
            f = dict()
            f["modified"] = dict()
            f["file_path"] = os.path.join(folder_path, file_name)
            f["file_name"] = file_name
            f["file_info"] = os.stat(f["file_path"])
            f["modification_date"] = self.format_date(f["file_info"].st_mtime)
            try:
                with open(f["file_path"], "rb") as image_file:
                    img = exif.Image(image_file)
                    f["model"] = img.get("model")
                    f["datetime_original"] = img.get("datetime_original")

                    # load coord

                    if (
                        img.has_exif
                        and img.get("gps_latitude")
                        and img.get("gps_longitude")
                    ):
                        lat = (
                            img.gps_latitude[0]
                            + img.gps_latitude[1] / 60
                            + img.gps_latitude[2] / 3600
                        )
                        lon = (
                            img.gps_longitude[0]
                            + img.gps_longitude[1] / 60
                            + img.gps_longitude[2] / 3600
                        )
                        if img.gps_latitude_ref == "S":
                            lat = -lat
                        if img.gps_longitude_ref == "W":
                            lon = -lon

                        f["lat"] = lat
                        f["lon"] = lon
                        del lat
                        del lon
                        # dest
                        if (
                            img.has_exif
                            and img.get("gps_dest_latitude")
                            and img.get("gps_dest_longitude")
                        ):
                            lat = (
                                img.gps_dest_latitude[0]
                                + img.gps_dest_latitude[1] / 60
                                + img.gps_dest_latitude[2] / 3600
                            )
                            lon = (
                                img.gps_dest_longitude[0]
                                + img.gps_dest_longitude[1] / 60
                                + img.gps_dest_longitude[2] / 3600
                            )
                            if img.gps_dest_latitude_ref == "S":
                                lat = -lat
                            if img.gps_dest_longitude_ref == "W":
                                lon = -lon

                            f["dest_lat"] = lat
                            f["dest_lon"] = lon

            except:
                print("exif read error " + f["file_path"])

            self.mainfiles.append(f)

    def display_files(self, folder_path, supress_statusbar=False):
        """
        append files to file list
        """

        self.folder_path = folder_path  # Save the selected folder path

        self.table.setSortingEnabled(False)  # Disable sorting while updating
        self.table.setRowCount(0)

        files = self.mainfiles
        # if filter
        if self.filter_has_coords_enabled:
            files = [
                f
                for f in self.mainfiles
                if f.get("lat") is None and f.get("lon") is None
            ]

        self.table.setRowCount(len(files))

        for i, f in enumerate(files):

            item_file_name = QTableWidgetItem(f["file_name"])
            item_datetime = QTableWidgetItem(f.get("datetime_original"))
            item_lat = QTableWidgetItem(str(f.get("lat", "")))
            item_lon = QTableWidgetItem(str(f.get("lon", "")))
            item_destlat = QTableWidgetItem(str(f.get("dest_lat", "")))
            item_destlon = QTableWidgetItem(str(f.get("dest_lon", "")))
            if f.get("is_modified") is not None and f.get("modified") is not None:
                if f["modified"].get("lat"):
                    item_lat = QTableWidgetItem(f"Pending {f["modified"]['lat']}")
                    item_lat.setBackground(QColor("#a6d96a"))
                if f["modified"].get("lon"):
                    item_lon = QTableWidgetItem(f"Pending {f["modified"]['lon']}")
                    item_lon.setBackground(QColor("#a6d96a"))
                if f["modified"].get("dest_lat"):
                    item_destlat = QTableWidgetItem(
                        f"Pending {f["modified"]['dest_lat']}"
                    )
                    item_destlat.setBackground(QColor("#a6d96a"))
                if f["modified"].get("dest_lon"):
                    item_destlon = QTableWidgetItem(
                        f"Pending {f["modified"]['dest_lon']}"
                    )
                    item_destlon.setBackground(QColor("#a6d96a"))
            # Disable editing for each item
            item_file_name.setFlags(
                item_file_name.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            item_datetime.setFlags(item_datetime.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_lat.setFlags(item_lat.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_lon.setFlags(item_lon.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_lat.setFlags(item_destlat.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_lon.setFlags(item_destlon.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(i, 0, item_file_name)
            self.table.setItem(i, 1, item_datetime)
            self.table.setItem(i, 2, item_lat)
            self.table.setItem(i, 3, item_lon)
            self.table.setItem(i, 4, item_destlat)
            self.table.setItem(i, 5, item_destlon)

        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.setSortingEnabled(True)  # Enable sorting after updating
        self.table.viewport().update()  # Explicitly trigger a redraw of the table
        if not supress_statusbar:
            self.statusBar().showMessage(f"Select image in table to edit coordinates")
        self.updateProgressBar()

    def display_image(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            file_name = selected_items[0].text()
            full_path = os.path.join(self.folder_path, file_name)
            self.mainfile_selected = full_path
            self.file_path_label.setText(f"Selected File Path: {full_path}")
            pixmap = QPixmap(full_path)
            self.label.setPixmap(
                pixmap.scaled(
                    self.label.width(),
                    self.label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            )
            self.label.setScaledContents(True)

            self.map_widget.page().runJavaScript("removeMarkers();")

            if self.mode_interface == self.mode_enter_coordinates:
                # display only photo coord
                attr_lat = "lat"
                attr_lon = "lon"
                for i, f in enumerate(self.mainfiles):
                    if f["file_path"] == full_path:
                        if f["modified"].get(attr_lat) and f["modified"].get(attr_lon):
                            self.add_marker(
                                f["modified"][attr_lat],
                                f["modified"][attr_lon],
                                markerclass="image",
                            )
                        elif f.get(attr_lat) and f.get(attr_lon):
                            self.add_marker(
                                f[attr_lat], f[attr_lon], markerclass="image"
                            )
                        else:
                            self.add_marker(lat=None, lon=None, markerclass="image")
                        self.statusBar().showMessage(
                            f"Move the marker to set coordinates for {file_name}"
                        )
                        break

            elif self.mode_interface == self.mode_enter_destinations:
                # display both photo coord and dest point
                attr_lat = "dest_lat"
                attr_lon = "dest_lon"

                for i, f in enumerate(self.mainfiles):
                    if f["file_path"] == full_path:
                        if f["modified"].get(attr_lat) and f["modified"].get(attr_lon):
                            self.add_marker(
                                f["modified"][attr_lat],
                                f["modified"][attr_lon],
                                markerclass="dest",
                            )
                        elif f.get(attr_lat) and f.get(attr_lon):
                            self.add_marker(
                                f[attr_lat], f[attr_lon], markerclass="dest"
                            )
                        else:
                            self.add_marker(lat=None, lon=None, markerclass="dest")
                        self.statusBar().showMessage(
                            f"Move the marker to set dest coordinates for {file_name}"
                        )

                        # non moveable marker for photo coord
                        attr_lat = "lat"
                        attr_lon = "lon"
                        for i, f in enumerate(self.mainfiles):
                            if f["file_path"] == full_path:
                                if f["modified"].get(attr_lat) and f["modified"].get(
                                    attr_lon
                                ):
                                    self.add_marker(
                                        f["modified"][attr_lat],
                                        f["modified"][attr_lon],
                                        markerclass="image",
                                        nonmoveable=True,
                                    )
                                elif f.get(attr_lat) and f.get(attr_lon):
                                    self.add_marker(
                                        f[attr_lat],
                                        f[attr_lon],
                                        markerclass="image",
                                        nonmoveable=True,
                                    )
                        break

    def format_date(self, timestamp):
        from datetime import datetime

        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def main():
    app = QApplication(sys.argv)
    viewer = RaskladGeotag()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
