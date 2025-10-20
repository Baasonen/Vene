import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont # Voisi ehkä toteuttaa ilmankin
import tkintermapview
from time import strftime #Ruudun alakulman kelloa varten
import os #lukee oikean tiedostopolun offline-kartalle
import pygame #Ohjainta varten
from vcom import Vene

'''
TODO:
- Controller reconnect
'''

class VeneGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Vene Gui V3')

        self.boat = Vene()
        #Testausta varten
        self.boat.debugmode(0)
        print(f"Debug mode set to {self.boat._Vene__debugmode}")

        #Alustaa ikkunan
        self.width = int(self.winfo_screenwidth() / 1.5)
        self.height = int(self.winfo_screenheight() / 1.4)
        self.geometry(f'{self.width}x{self.height}')

        self.bg_color = '#FFFFFF'
        self.configure(bg=self.bg_color)
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font.configure(family="Inter", size=10, weight="normal")

        self.style = ttk.Style(self)
        self.style.configure("Custom.TFrame", background=self.bg_color)
        self.style.configure("Custom.TLabel", background=self.bg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=8)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create frames
        self.statusframe = StatusFrame(self, self.boat)
        self.statusframe.grid(row=0, column=0, sticky="nsew")

        self.mapframe = MapFrame(self, self.boat)
        self.mapframe.grid(row=0, column=1, sticky="nsew")
        

        self.waypointframe = WaypointFrame(self, self.boat)
        self.waypointframe.grid(row=0, column=2, sticky="nsew")

        # Waypointit
        self.wp_list = []

        self.mapframe.offline_map.add_right_click_menu_command(
            label="Add waypoint",
            command=self.add_waypoint,
            pass_coords=True
            
        )

        self.waypointframe.update_wp_gui(self.wp_list, self.mapframe)
        self.waypointframe.update_time()
        self.after(1000, self.periodic_update)

        #Näppäimistöohjauksen konfiguraatio
        self.bind("<Up>", lambda e: self.change_throttle(10))
        self.bind("<Down>", lambda e: self.change_throttle(-10))
        self.bind("<Left>", lambda e: self.change_rudder(-10))
        self.bind("<Right>", lambda e: self.change_rudder(10))
        self.bind("<Prior>", lambda e: self.change_rudder(180))        #PageUp
        self.bind("<Next>", lambda e: self.change_rudder(-180))        #PageDown
        self.bind("1", lambda e: self.boat.setModeManual())
        self.bind("2", lambda e: self.boat.setModeAP())
        self.bind("3", lambda e: self.boat.returnHome())
        self.bind("4", lambda e: self.boat.modeOverride())
        #self.bind("l", lambda e: self.boat.change_light(10))
        #self.bind("k", lambda e: self.boat.change_light(-10))

    def change_rudder(self, delta):
        new_val = self.boat.rudder + delta
        self.boat.set_control(rudder=new_val)

    def change_throttle(self, delta):
        thr1, thr2 = self.boat.throttle
        thr1 += delta
        thr2 += delta
        self.boat.set_control(throttle=(thr1, thr2))

    def add_waypoint(self, coords):
        print("Add waypoint:", coords)
        if len(self.wp_list) < 64:
            self.wp_list.append(coords)
        else:
            print("Max waypoints reached")
        self.waypointframe.update_wp_gui(self.wp_list, self.mapframe)
        self.draw_path()

    def redraw_map(self):
        self.mapframe.offline_map.delete_all_marker()
        self.mapframe.offline_map.delete_all_path()
        self.mapframe.vene_marker = None
        self.mapframe.move_vene()
        #Asettaa veneen sijainnin
        #if self.boat.t_current_coords[0] != 0 and self.boat.t_current_coords[1] != 0:
        #    self.mapframe.offline_map.set_marker(self.boat.t_current_coords[0], self.boat.t_current_coords[1], text=f"Vene: {self.boat.t_current_coords}")


    def draw_path(self):  #Käytä aina tätä, älä luo erillisiä viivoja
        if (self.boat.t_target_wp < len(self.wp_list)) and (len(self.wp_list) > 1):
            if self.boat.t_current_coords[0] != 0 and self.boat.t_current_coords[1] != 0:
                path_coords = [self.boat.t_current_coords] + self.wp_list[(self.boat.t_target_wp - 1):]
            else:
                path_coords = self.wp_list[self.boat.t_target_wp:]
            self.mapframe.offline_map.set_path(path_coords)

    def periodic_update(self):
        self.waypointframe.update_time()
        self.mapframe.offline_map.delete_all_path()
        self.draw_path()

        self.after(1000, self.periodic_update)

class StatusFrame(ttk.Frame):  # Kartan vasen puoli
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.bg_color = container.bg_color

        #Otsikko
        self.label_wp = tk.Label(self, text="Vene Status:", font=("Inter", 17, "bold"), bg=container.bg_color)
        self.label_wp.pack(side="top", anchor="w", padx=20, pady=10)

        self.boat = boat

        #Yhteysindikaattori
        self.connection_label  = tk.Label(self, text=f"Connected to Vene: False", font=("Inter", 13), bg=container.bg_color)
        self.connection_label.pack(side="top", anchor="w", padx=20, pady=10)

        #Luetaan Veneen output
        self.receive_label = tk.Label(self, text="Received from Vene:", font=("Inter", 10, "bold"), bg=container.bg_color)
        self.receive_label.pack(side="top", anchor="w", padx=30, pady=(30,0))
        
        self.telemetry_frame = tk.Frame(self,  bg=container.bg_color)
        self.telemetry_labels = {}
        self.telemetry_vars = {
            "t_mode": "Mode",
            "t_heading": "Heading",
            "t_speed": "Speed",
            "t_current_coords": "Coordinates",
            "t_battery": "Battery",
            "t_target_wp": "Target waypoint",
            "t_gps_status": "GPS status",
            "t_gen_error": "Gen error",
            "t_packets_per_second": "Packets per second",
            "t_home_coords": "Home waypoint"
        }


        for i, var in enumerate(self.telemetry_vars):
            lbl = tk.Label(self.telemetry_frame, text=f"{var}: ---", bg=container.bg_color)
            lbl.grid(row=i, column=0, sticky="w")
            self.telemetry_labels[var] = lbl
        self.telemetry_frame.pack(side="top", anchor="w", padx=60, pady=10)

        #Luetaan Veneen input
        self.send_label = tk.Label(self, text="Sending to Vene:", font=("Inter", 10, "bold"), bg=container.bg_color)
        self.send_label.pack(side="top", anchor="w", padx=30, pady=(30,0))

        self.controls_frame = tk.Frame(self, bg=container.bg_color)
        self.control_labels = {}

        self.control_vars = {
            "rudder": "Rudder",
            "throttle": "Throttle",
            "light_mode": "Lights",
            "_Vene__debugmode": "Debug mode"
        }

        for i, var in enumerate(self.control_vars):
            lbl = tk.Label(self.controls_frame, text=f"{self.control_vars[var]}: ---", bg=container.bg_color            )
            lbl.grid(row=i, column=0, sticky="w")
            self.control_labels[var] = lbl
        
        self.controls_frame.pack(side="top", anchor="w", padx=60, pady=10)


        ''' Tarkistaa SSID:n käynnistyessä, hidastaa käynnistymistä, eikä toimi Windowsilla vielä
        def ssid():
            try:
                ssid_output = os.popen("nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2").read().strip()
                if len(ssid_output) < 15:
                    print(ssid_output)
                    return ssid_output
                else:
                    return "None"
            except Exception:
                return "None"
            
    
        self.send_label = tk.Label(self, text=f"Connected to {ssid()}", font=("Inter", 10, "bold"), bg=container.bg_color)
        self.send_label.pack(side="top", anchor="w", padx=30, pady=(30,0))
        '''

        #Ohjainruutu
        self.controller_frame = ControllerFrame(self, self.boat)
        self.controller_frame.pack(side="top", anchor="w", padx=40, pady=(60,40))

        # Start vcom
        tk.Button(
            self,
            text="Start vcom",
            command=lambda: self.boat.start(),
            bg="#9af97a"
            ).pack(anchor="w", padx=40)
        # Stop vcom
        tk.Button(
            self,
            text="Stop vcom",
            command=lambda: self.boat.shutdown(),
            bg="#ffcdcc"
            ).pack(anchor="w", padx=40, pady=10)
    
        self.update_gui()
        
        self.sum = 0

        self.check_connection()

        

    def check_connection(self): #Tässä on logiikkaa
        if self.boat.t_packets_rcv > 1:
            True
            self.connection_label.config(text="Connected to Vene", bg="#00b16a")
        else:
            False
            self.connection_label.config(text="No connection", bg="#ffcdcc")
            
        self.after(1000, self.check_connection) 
            
    def update_gui(self):
        for var, lbl in self.telemetry_labels.items():
            display_name = self.telemetry_vars.get(var, var)
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        for var, lbl in self.control_labels.items():
            display_name = self.control_vars.get(var, var)
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        self.after(200, self.update_gui) 

class WaypointFrame(ttk.Frame):  # Kartan oikea puoli
    def __init__(self, container, boat):
        super().__init__(container, style='Custom.TFrame')
        self.container = container

        #Waypoint-lista
        #Lisää yksittäisten poistaminen, tai jopa uudelleenjärjestäminen?
        self.wp_label = ttk.Label(self, text="Waypoints: (max 64) ", style='Custom.TLabel')
        self.wp_label.pack(pady=(10,5))

        self.wp_gui = tk.Listbox(self, height=15, font=("Inter", 10))
        self.wp_gui.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def remove_index(event): 
            index = self.wp_gui.nearest(event.y)
            if index != None:
                self.wp_gui.delete(index)
                container.wp_list.pop(index)
            self.update_wp_gui(container.wp_list, container.mapframe)
        
        self.wp_gui.bind("<Button 3>", remove_index)

        tk.Button(
            self,
            text="Clear all waypoints",
            command=lambda: self.empty_wp(),
            bg="#ffcdcc"
            ).pack()


        #Modevalitsin
        self.mode_label = ttk.Label(self, text="Choose Mode: ", style='Custom.TLabel')
        self.mode_label.pack(anchor="w", padx=70, pady=(30, 5))

        self.boat = boat
        self.mode = tk.IntVar(value=0)

        
        self.color_active = "#00b16a"
        self.color_inactive = "#FFFFFF"
        self.color1 = self.color_inactive
        self.color2 = self.color_inactive
        self.color3 = self.color_inactive
        self.color4 = self.color_inactive

        #Lista napeille
        self.buttons = []

        self.buttons.append(tk.Button(self, text="Manual", anchor="w", command=lambda: self.boat.setModeManual(), bg=self.color1, width=17))
        self.buttons.append(tk.Button(self, text="Automatic", anchor="w", command=lambda: self.boat.setModeAP(container.wp_list), bg=self.color2, width=17))
        self.buttons.append(tk.Button(self, text="Return home", anchor="w", command=lambda: self.boat.returnHome(), bg=self.color3, width=17))
        self.buttons.append(tk.Button(self, text="Reset", anchor="w", command=lambda: self.boat.modeOverride(), bg=self.color4, width=17))


        for button in self.buttons:
            button.pack(anchor="w", padx=80, pady=5)

        
        #Kello
        self.clock_label = ttk.Label(self, text="00:00:00", font=("Inter", 12, "normal"), style='Custom.TLabel')
        self.clock_label.pack(anchor="e", padx=15, pady=(10, 15))

    def update_time(self):
        current_time = strftime('%H:%M:%S')
        self.clock_label.config(text=current_time)
        # Värinvaihto mode-valintaan
        for index, button in enumerate(self.buttons, start=1):
            if index == self.boat.t_mode:
                button.config(bg=self.color_active)
            else:
                button.config(bg=self.color_inactive)


    def empty_wp(self):
        self.wp_gui.delete(0, tk.END)
        self.container.wp_list.clear()
        self.container.redraw_map()


    def update_wp_gui(self, wp_list, mapframe):
        self.wp_gui.delete(0, tk.END)
        self.container.redraw_map()

        self.container.draw_path()

        for index, wp in enumerate(wp_list, start=1): #Indeksi visuaaliseen listaan, oikeassa wp-listassa ei ole indeksejä
            self.wp_gui.insert(tk.END, f"{index}: ({wp[0]:.4f}, {wp[1]:.4f})")
            mapframe.wp_on_map(wp)

        

class MapFrame(tk.Frame):
    def __init__(self, container, boat):
        super().__init__(container)

        # Offline-kartan latauskonfiguraatio
        self.top_left_position = (60.1884794, 24.8313517)   #(60.19711, 24.81159)
        self.bottom_right_position = (60.1880447, 24.8328618)  #(60.18064, 24.85399)
        self.zoom_min = 0
        self.zoom_max = 15 #Tämän kanssa varovasti, zoom_level 20 mittakaava on jo 1:500.
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(self.script_directory, "offline_tiles.db")

        self.loader = tkintermapview.OfflineLoader(
            path=self.database_path,
            tile_server="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        )
        
        # Lataa offline-kartan, käytä vain jos tarvii ladata lisää karttaa
        self.loader.save_offline_tiles(self.top_left_position, self.bottom_right_position, self.zoom_min, self.zoom_max)

        self.offline_map = tkintermapview.TkinterMapView(
            self,
            width=600,
            height=600,
            use_database_only=True,
            max_zoom=19, #Realistisesti maksimi on 19
            database_path=self.database_path
        )

        self.boat = boat

        #Asettaa kartan aloitusnäkymän
        self.offline_map.set_position(60.185921, 24.825963) # Otaniemi, kartan voi asettaa seuraamaan venettä: self.boat.t_current_coords[0], self.boat.t_current_coords[1]
        self.offline_map.set_zoom(15)
        self.offline_map.pack(fill=tk.BOTH, expand=True)

        
        # Vene kartalla, muuta kuva
        self.vene_marker = self.offline_map.set_marker(self.boat.t_current_coords[0], self.boat.t_current_coords[1], text=f"Vene: {self.boat.t_current_coords}")
        self.move_vene()
    
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
                self.vene_marker = self.offline_map.set_marker(new_lat, new_lon, text=f"Vene: {self.boat.t_current_coords}")
            else:
                self.vene_marker.set_position(new_lat, new_lon)
                self.vene_marker.set_text(f"Vene: {self.boat.t_current_coords}")

        self.after(100, self.move_vene)

    def wp_on_map(self, wp):
        self.offline_map.set_marker(wp[0], wp[1], text=f"({wp[0]:.5f}, {wp[1]:.5f})")


class ControllerFrame(ttk.Frame):
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.bg_color = container.bg_color

        self.controller = Controller(boat)

        self.controller_status = tk.StringVar(value="no_value")

        self.controller_status_label = tk.Label(self, textvariable=self.controller_status, bg=self.bg_color)
        self.controller_status_label.pack(anchor="w")


        # Piirtää viivat
        self.canvas = tk.Canvas(self, width=300, height=200, bg="white")
        self.canvas.pack(anchor="w")

        self.lx_line = self.canvas.create_line(0, 50, 150, 50, width=4, fill="blue")
        self.thr_line = self.canvas.create_line(0, 150, 150, 150, width=4, fill="green")

        self.steer_center = 150
        self.steer_length = 100


        self.update_controller()
        self.update_lines()
        self.controller.poll_joystick(container)


    def update_controller(self): # ei toimi
        if self.controller.joystick is None:
            self.controller_status.set("No controller detected")
        else:
            self.controller_status.set("Controller connected")
    
        self.after(200, self.update_controller)

    def update_lines(self):
        lx_offset = self.controller.axis0 * self.steer_length
        
        if lx_offset >= 0:
            self.canvas.coords(self.lx_line, self.steer_center, 50, self.steer_center + lx_offset, 50)
        else:
            self.canvas.coords(self.lx_line, self.steer_center + lx_offset, 50, self.steer_center, 50)


        thr_norm = (self.controller.axis5 + 1) / 2 
        thr_x = 50 + thr_norm * 200
        self.canvas.coords(self.thr_line, 50, 150, thr_x, 150)

        self.after(50, self.update_lines)

class Controller:
    def __init__(self, boat):
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No controller detected")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller connected: {self.joystick.get_name()}")

        self.boat = boat
        self.axis0 = 0
        self.axis5 = 0
        

    def poll_joystick(self, root):
        if self.joystick:
            self.deadzone = 2 #Eliminoi yhden kokonaisluvun hypyt, onko tästä hyötyä?
            pygame.event.pump()
            self.axis0 = ( 0 if (abs(self.joystick.get_axis(0)) < self.deadzone) else self.joystick.get_axis(0))
            self.boat.set_control(rudder=int((self.axis0 + 1) * 90))
            self.axis5 = ( 0 if (abs(self.joystick.get_axis(5)) < self.deadzone) else self.joystick.get_axis(5))
            self.boat.set_control(throttle=int((self.axis5 + 1) * 50))
        else:
            self.axis0 = 0
            self.axis5 = 0

        root.after(50, self.poll_joystick, root)
 
if __name__ == "__main__":
    app = VeneGui()
    app.mainloop()
