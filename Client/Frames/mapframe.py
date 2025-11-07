'''
Tämä tiedosto määrittää kartan ja piirrettävät karttamerkit. 
Offline-kartan lataaminen tapahtuu config-tiedoston parametrien perusteella.
'''

import tkinter as tk
from tkinter import ttk
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkintermapview

class MapFrame(ttk.Frame):
    def __init__(self, container, boat, config_map, wp_list):
        super().__init__(container, style="Custom.TFrame")

        self.wp_list = wp_list
        self.boat = boat
        self.container = container

        # Offline-kartan latauskonfiguraatio
        self.top_left_position = config_map.get("top_left", (60.19711, 24.81159))   
        self.bottom_right_position = config_map.get("bottom_right", (60.18064, 24.85399))  
        self.zoom_min = config_map.get("zoom_min", 0)
        self.zoom_max = config_map.get("zoom_max", 15)
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(self.script_directory, config_map.get("offline_db", "offline_tiles.db"))

        self.loader = tkintermapview.OfflineLoader(
            path=self.database_path,
            tile_server=config_map.get("tile_server", "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        )
        
        # Lataa offline-kartan
        if config_map.get("loader_enabled", False):
            self.loader.save_offline_tiles(self.top_left_position, self.bottom_right_position, self.zoom_min, self.zoom_max)
        
        self.offline_map = tkintermapview.TkinterMapView(
            self,
            width=600,
            height=600,
            use_database_only=True,
            max_zoom=19, #Realistisesti maksimi on 19
            database_path=self.database_path
        )

        # Lisää wp -nappi karttaan
        self.offline_map.add_right_click_menu_command(
            label="Add waypoint",
            command=self.add_waypoint,
            pass_coords=True
        )   

        #Asettaa kartan aloitusnäkymän
        default_pos = config_map.get("default_position", (60.185921, 24.825963))
        self.offline_map.set_position(default_pos[0], default_pos[1]) # Otaniemi, kartan voi asettaa seuraamaan venettä: self.boat.t_current_coords[0], self.boat.t_current_coords[1]
        default_zoom = config_map.get("default_zoom",15)
        self.offline_map.set_zoom(default_zoom)
        self.offline_map.pack(fill=tk.BOTH, expand=True)

        #Error handling jos kuvia ei löydy (erikseen, jotta yhden puuttuminen ei vaikuta muihin)
        try:
            home_icon_path = os.path.join(self.script_directory, "home_icon.png")
            self.home_icon = tk.PhotoImage(file=home_icon_path)
        except:
            self.home_icon = None
        try:
            vene_icon_path = os.path.join(self.script_directory, "vene_icon.png")  
            self.vene_icon = tk.PhotoImage(file=vene_icon_path) 
        except:
            self.vene_icon = None
        try:
            wp_icon_path = os.path.join(self.script_directory, "wp_icon.png")
            self.wp_icon = tk.PhotoImage(file=wp_icon_path)
        except:
            self.wp_icon = None
        # Vene kartalla
        self.vene_marker = self.offline_map.set_marker(self.boat.t_current_coords[0], self.boat.t_current_coords[1], text=f"Vene: {self.boat.t_current_coords}", icon=self.vene_icon)
        self.move_vene()
        self.periodic_update()

    
    # Piirtää veneen kartalle
    def move_vene(self):
        new_lat = self.boat.t_current_coords[0]
        new_lon = self.boat.t_current_coords[1]
        
        #Jos koordinaatit nolla, ei piirretä venettä
        if new_lat == 0 and new_lon == 0:
            if self.vene_marker:
                self.offline_map.delete_all_marker()
                self.vene_marker = None
        else:
            if self.vene_marker is None:
                self.vene_marker = self.offline_map.set_marker(new_lat, new_lon, text=f"Vene: {self.boat.t_current_coords}", icon=self.vene_icon)
            else:
                self.vene_marker.set_position(new_lat, new_lon)
                self.vene_marker.set_text(f"Vene: {self.boat.t_current_coords}")

        self.after(100, self.move_vene)

    def add_waypoint(self, coords):
        print("Add waypoint:", coords)
        if len(self.wp_list) < 255:
            self.wp_list.append(coords)
        else:
            print("Max waypoints reached")
        self.container.waypointframe.update_wp_gui(self.wp_list, self)
        self.draw_path()

    def draw_path(self):  #Käytä aina tätä, älä luo erillisiä viivoja
        if (self.boat.t_mode in (0, 1) ) and (len(self.wp_list) > 1):
            self.offline_map.set_path(self.wp_list, width=5, color="#FF0000")
        elif self.boat.t_mode == 2 and (self.boat.t_current_coords[0] + self.boat.t_current_coords[1] != 0) and (len(self.wp_list) > 1):
            path_coords: list[tuple] = [self.boat.t_current_coords] + self.wp_list[self.boat.t_target_wp - 1:]
            self.offline_map.set_path(path_coords, width=5, color="#FF0000")
        elif (self.boat.t_mode == 3) and (self.boat.t_current_coords[0] + self.boat.t_current_coords[1] != 0) and (self.boat.t_home_coords[0] + self.boat.t_home_coords[1] > 10) and (self.boat.t_current_coords != self.boat.t_home_coords):
            path_coords = [self.boat.t_current_coords, self.boat.t_home_coords]
            self.offline_map.set_path(path_coords, width=5, color="#FF0000")
    
    def redraw_map(self):
        self.offline_map.delete_all_marker()
        self.offline_map.delete_all_path()
        self.vene_marker = None
        self.move_vene()
        if self.boat.t_home_coords[0] > 5 and self.boat.t_home_coords[1] > 5:
            self.offline_map.set_marker(self.boat.t_home_coords[0], self.boat.t_home_coords[1], text=f"Home wp: {self.boat.t_home_coords}", icon=self.mapframe.offline_map.home_icon)
    
    def periodic_update(self):
        self.offline_map.delete_all_path()
        self.draw_path()
        self.after(1000, self.periodic_update)


    def wp_on_map(self, index, wp):
        self.offline_map.set_marker(wp[0], wp[1], text=f"{index}", icon=self.wp_icon)
