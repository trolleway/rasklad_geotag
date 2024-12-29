import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout,QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QDir,QObject, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPixmap
import folium
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import pyqtSlot, QUrl
from PyQt6.QtWebChannel import QWebChannel
from folium.plugins import MarkerCluster
import exif

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f"JavaScript console message: {message} (line: {line_number})")

class JavaScriptHandler(QObject):
    coordinatesUpdated = pyqtSignal(str, str)

    @pyqtSlot(str, str)
    def coordinatesUpdatedSlot(self, lat, lng):
        self.coordinatesUpdated.emit(lat, lng)

class MapWidget(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.setPage(CustomWebEnginePage(self))
        self.channel = QWebChannel()
        self.jsHandler = JavaScriptHandler()

        self.channel.registerObject('jsHandler', self.jsHandler)
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
            <div id="map" style="height: 600px;"></div>
            <div id="coordinates">Coordinates: </div>
            <script>
                var map = L.map('map').setView([55.666, 37.666], 11);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

                var marker;

                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.jsHandler = channel.objects.jsHandler;
                    console.log("Channel initialized");
                });

                function removeMarkers() {
                    
                    if (marker) {
                        map.removeLayer(marker);
                    }
                }
                function addMarker(position) {
                   removeMarkers();
                

                    // Custom circular icon
                    var circularIcon = L.icon({
                        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDEwQzEwIDguMzI0NSAxMS4zMjQ1IDcgMTMgN0MxNC42NzU1IDcgMTYgOC4zMjQ1IDE2IDEwQzE2IDExLjY3NTUgMTQuNjc1NSAxMyAxMyAxM0MxMS4zMjQ1IDEzIDEwIDExLjY3NTUgMTAgMTBaIiBmaWxsPSIjMDAwMDAwIi8+CjxwYXRoIGQ9Ik0xMCAwQzQuNDcxNiAwIDAgNC40NzE2IDAgMTBDMCAxNS41Mjg0IDQuNDcxNiAyMCAxMCAyMEMxNS41Mjg0IDIwIDIwIDE1LjUyODQgMjAgMTBDMjAgNC40NzE2IDE1LjUyODQgMCAxMCAwWk0xMCAxOUM0Ljc4MjQgMTkgMSAxNS4yMTc2IDEgMTBDMSA0Ljc4MjQgNC43ODI0IDEgMTAgMUMxNS4yMTc2IDEgMTkgNC43ODI0IDE5IDEwQzE5IDE1LjIxNzYgMTUuMjE3NiAxOSAxMCAxOVoiIGZpbGw9IiMwMDAwMDAiLz4KPC9zdmc+Cg==', // Base64 encoded SVG
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    });

                    // Create a circle marker at the the map
                    marker = L.marker(position, {
                    draggable: true,
                    autoPan: true,
                    icon: circularIcon

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
                }
            </script>
        </body>
        </html>
        """
        return leaflet_html


class FileViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.initial_coords = (55.666, 37.666)

        self.mainfiles=[]
        self.mainfile_selected=''
        self.filter_has_coords_enabled = False  # Initial state of the filter

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
        self.label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        

        self.select_button = QPushButton("Select Folder", self)
        self.select_button.clicked.connect(self.open_folder_dialog)

        self.save_button = QPushButton("Save coordinates to EXIF", self)
        self.save_button.clicked.connect(self.save2exif)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Filename", "Modification Date","lat","lon",'State'])
        self.table.setColumnWidth(0, 400)
        self.table.itemSelectionChanged.connect(self.display_image)

        self.file_path_label = QLabel(self)
        self.file_path_label.setText("Selected File Path: ")



        layout.addWidget(self.label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.table)
        layout.addWidget(self.file_path_label)
        
        layout_horizontal.addLayout(layout)

        self.map_widget = MapWidget()
        layout_vertical_right = QVBoxLayout()
        layout_vertical_right.addWidget(self.map_widget)

        layout_horizontal.addLayout(layout_vertical_right)
        self.coordinates_label = QLabel("Coordinates: ")
        self.map_widget.jsHandler.coordinatesUpdated.connect(self.update_coordinates_label)

        self.add_marker_button = QPushButton("Add Marker to Center")
        self.add_marker_button.clicked.connect(self.add_marker)
        layout_vertical_right.addWidget(self.add_marker_button)
        self.toggle_button = QPushButton("Hide files with coordinates", self)
        self.toggle_button.clicked.connect(self.toggle_filter)
        layout.addWidget(self.toggle_button)

        layout.addWidget(self.coordinates_label)
        layout.addWidget(self.save_button)


        widget.setLayout(layout_horizontal)
        self.marker_coordinates = None

    def toggle_filter(self):
        self.filter_has_coords_enabled = not self.filter_has_coords_enabled
        if self.filter_has_coords_enabled:
            self.toggle_button.setText("Display all files")
            # Add your filter logic here
            self.display_files(self.folder_path)
            print("Filter enabled")
        else:
            self.toggle_button.setText("Hide files with coordinates")
            # Remove your filter logic here
            self.display_files(self.folder_path)
            print("Filter disabled")

    def add_marker(self, lat=None, lon=None):
        if not lat or not lon:
            js_code = "addMarker(map.getCenter());"
        else:
            js_code = f"addMarker([{lat}, {lon}]);"
    
        self.map_widget.page().runJavaScript(js_code)

    @pyqtSlot(str, str)
    def update_coordinates_label(self, lat, lon):
        if self.mainfile_selected:
            self.coordinates_label.setText(f"Coordinates: {lat} {lon} for file {self.mainfile_selected}")
            for i, f in enumerate(self.mainfiles):
                if f['file_path']==self.mainfile_selected:
                    f['modified']['lat']=lat
                    f['modified']['lon']=lon
                    f['is_modified']=True

                    row_count = self.table.rowCount()
                    for row in range(row_count):
                        item = self.table.item(row, 0)  # Get the item in column 0
                        if item and item.text() == f['file_name']:
                            self.table.setItem(row, 2, QTableWidgetItem(f'{lat} modified'))  
                            self.table.setItem(row, 3, QTableWidgetItem(f'{lon} modified'))  

                    break
   

    def save2exif(self):
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

        for i, f in enumerate(self.mainfiles):
            if f.get('is_modified'):
                assert f['modified']['lat'] and f['modified']['lon']
                lat=f['modified']['lat']
                lon=f['modified']['lon']
                if lat and lon:
                    lat_deg = to_deg(lat, ('S', 'N'))
                    lon_deg = to_deg(lon, ('W', 'E'))
                    with open(f['file_path'] , 'rb') as image_file:
                        img = exif.Image(image_file)
                    img.gps_latitude = lat_deg[:3]
                    img.gps_latitude_ref = lat_deg[3]
                    img.gps_longitude = lon_deg[:3]
                    img.gps_longitude_ref = lon_deg[3]
                    with open(f['file_path'], 'wb') as new_image_file:
                        new_image_file.write(img.get_file())
                        
                    self.coordinates_label.setText(f"Coordinates: {lat} {lon} for file {f['file_name']} saved to EXIF")
                else:
                    self.coordinates_label.setText(f"Coordinates not found for file {f['file_name']}")

        self.display_files(self.folder_path)


    def open_folder_dialog(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.display_files(self.folder_path)

    def read_files_data(self,folder_path):
        self.mainfiles=[]
        print('mainfiles cleared')
        files = os.listdir(folder_path)
        for i, file_name in enumerate(files):
            if not file_name.lower().endswith('.jpg'): continue
            f=dict()
            f['modified']=dict()
            f['file_path'] = os.path.join(folder_path, file_name)
            f['file_name'] = file_name
            f['file_info'] = os.stat(f['file_path'])
            f['modification_date'] = self.format_date(f['file_info'].st_mtime)
            try:
                with open(f['file_path'], 'rb') as image_file:
                    img = exif.Image(image_file)
                    f['model'] = img.get('model')
                    f['datetime_original'] = img.get('datetime_original')

                    if img.has_exif and img.get('gps_latitude') and img.get('gps_longitude'):
                        lat = img.gps_latitude[0] + img.gps_latitude[1] / 60 + img.gps_latitude[2] / 3600
                        lon = img.gps_longitude[0] + img.gps_longitude[1] / 60 + img.gps_longitude[2] / 3600
                        if img.gps_latitude_ref == 'S': lat = -lat
                        if img.gps_longitude_ref == 'W': lon = -lon

                        f['lat'] = lat
                        f['lon'] = lon
            except:
                print('exif read error '+f['file_path'])

                
            
            self.mainfiles.append(f)

    def display_files(self, folder_path):
        self.read_files_data(folder_path)
        self.folder_path = folder_path  # Save the selected folder path
        
        self.table.setSortingEnabled(False)  # Disable sorting while updating
        self.table.setRowCount(0)
        
        files=self.mainfiles
        if self.filter_has_coords_enabled:
            files = [f for f in self.mainfiles if f.get('lat') is None and f.get('lon') is None]
        
        self.table.setRowCount(len(files))
    
        for i, f in enumerate(files):
            
            self.table.setItem(i, 0, QTableWidgetItem(f['file_name']))
            self.table.setItem(i, 1, QTableWidgetItem(f.get('datetime_original')))
            self.table.setItem(i, 2, QTableWidgetItem(str(f.get('lat',''))))
            self.table.setItem(i, 3, QTableWidgetItem(str(f.get('lon',''))))
        
        self.table.setSortingEnabled(True)  # Enable sorting after updating
        self.table.viewport().update()  # Explicitly trigger a redraw of the table



    def display_image(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            file_name = selected_items[0].text()
            full_path = os.path.join(self.folder_path, file_name)
            self.mainfile_selected = full_path
            self.file_path_label.setText(f"Selected File Path: {full_path}")
            pixmap = QPixmap(full_path)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.AspectRatioMode.KeepAspectRatio))
            self.label.setScaledContents(True)
            
            for i, f in enumerate(self.mainfiles):
                if f['file_path']==full_path:
                    if f['modified'].get('lat') and f['modified'].get('lon'):
                        self.add_marker(f['modified']['lat'],f['modified']['lon'])
                    elif f.get('lat') and f.get('lon'):
                        self.add_marker(f['lat'],f['lon'])
                    else:
                        self.add_marker()
            

    def format_date(self, timestamp):
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')



def main():
    app = QApplication(sys.argv)
    viewer = FileViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
