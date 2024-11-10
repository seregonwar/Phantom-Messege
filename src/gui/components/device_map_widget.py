from PyQt6.QtWidgets import QWidget, QVBoxLayout
import folium
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import os
import json

class DeviceMapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create QWebEngineView to display the map
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Initialize empty map centered on world
        self.map = folium.Map(
            location=[0, 0],
            zoom_start=2,
            tiles='OpenStreetMap'
        )
        
        # Save and load initial map
        self._save_and_load_map()
        
    def _save_and_load_map(self):
        """Save map to temporary file and load it in web view"""
        map_file = "temp_map.html"
        self.map.save(map_file)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(map_file)))
        
    def update_devices(self, devices: list):
        """Update map with device locations"""
        # Clear existing markers
        self.map = folium.Map(
            location=[0, 0],
            zoom_start=2,
            tiles='OpenStreetMap'
        )
        
        # Add markers for each device
        for device in devices:
            try:
                # Get location data
                location = json.loads(device['location']) if device['location'] else None
                if not location or 'city' not in location:
                    continue
                    
                # Get coordinates for the city
                coords = self._get_city_coordinates(location['city'], location['country'])
                if not coords:
                    continue
                
                # Create popup content
                popup_content = f"""
                    <b>Device Info:</b><br>
                    Hardware ID: {device['hardware_id']}<br>
                    Status: {device['status']}<br>
                    Location: {location['city']}, {location['country']}<br>
                    Last Active: {device['last_check']}<br>
                """
                
                # Add marker with custom icon based on status
                icon_color = 'green' if device['status'] == 'active' else 'red'
                folium.Marker(
                    coords,
                    popup=popup_content,
                    icon=folium.Icon(color=icon_color, icon='info-sign')
                ).add_to(self.map)
                
            except Exception as e:
                print(f"Error adding device marker: {e}")
                continue
        
        # Save and reload map
        self._save_and_load_map()
        
    def _get_city_coordinates(self, city: str, country: str) -> tuple:
        """Get coordinates for a city using geocoding service"""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="phantom_messenger")
            location = geolocator.geocode(f"{city}, {country}")
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            print(f"Error geocoding location: {e}")
        return None 