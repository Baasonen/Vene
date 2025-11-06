import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont # Voisi ehkä toteuttaa ilmankin
import tkintermapview
from time import strftime #Ruudun alakulman kelloa varten
import os #lukee oikean tiedostopolun offline-kartalle
import pygame #Ohjainta varten
from PIL import Image, ImageTk #Videokäsittelyyn
import cv2  #Videokäsittelyyn
import concurrent.futures
import io

#Paikalliset tiedostot
from vcom import Vene
import config

class VeneGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Vene Gui V3')

        self.boat = Vene()

        #Debugmode
        self.boat.debugmode(config.DEBUG_MODE)
        print(f"Debug mode set to {self.boat._Vene__debugmode}")

        #Alustaa ikkunan
        self.width = int(self.winfo_screenwidth() / 1.5)
        self.height = int(self.winfo_screenheight() / 1.4)
        if config.FULLSCREEN:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        else:
            self.geometry(f"{self.width}x{self.height}")

        self.bg_color = "#FFFFFF"
        self.configure(bg=self.bg_color)
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font.configure(family="Inter", size=10, weight="normal")

        
        self.style = ttk.Style(self)
        self.style.configure("Custom.TFrame", background=self.bg_color)
        self.style.configure("Custom.TLabel", font=("Inter", 10), background=self.bg_color)
        self.style.configure("Custom.TButton", font=("Inter", 10), background=self.bg_color, anchor="w", padding=(10,5,5,5))
        self.style.configure("Red.TButton", font=("Inter", 10), background="#ff9d9d", anchor="w", padding=(10,5,5,5))
        self.style.configure("Green.TButton", font=("Inter", 10), background="#6ED06E", anchor="w", padding=(10,5,5,5))

        self.LIGHT_THEME = config.LIGHT_THEME
        self.DARK_THEME = config.DARK_THEME

        self.grid_columnconfigure(1, weight=8)
        self.grid_rowconfigure(0, weight=1)


        # Waypointit
        self.wp_list = []

        # Create frames
        self.statusframe = StatusFrame(self, self.boat)
        self.statusframe.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=15)

        self.mapframe = MapFrame(self, self.boat, config.MAP_CONFIG)
        self.mapframe.grid(row=0, column=1, rowspan=2, sticky="nsew")

        # Lisää wp -nappi karttaan
        self.mapframe.offline_map.add_right_click_menu_command(
            label="Add waypoint",
            command=self.add_waypoint,
            pass_coords=True
            
        )        

        self.waypointframe = WaypointFrame(self, self.boat)
        self.waypointframe.grid(row=0, column=2, sticky="nsew")

        self.waypointframe.update_wp_gui(self.wp_list, self.mapframe)

        self.buttonframe = ButtonFrame(self, self.boat)
        self.buttonframe.grid(row=1, column=2, sticky="nsew")

        self.active_frames_shown = 0

        self.cameraframe = CameraFrame(self, self.boat)
        #Älä aseta mihinkään vieäl
        
        self.theme = self.LIGHT_THEME #Vaikka vaihtaa tähän niin ei käynnisty oletuksena tummaan?
        self.toggle_theme() # Vaihda tummaan teemaan heti käynnistyessä

        self.configure_keybindings()
        self.after(1000, self.periodic_update)

    
        #Näppäimistöohjauksen konfiguraatio
    def configure_keybindings(self):
        self.bind("<Up>", lambda e: self.change_throttle(10))
        self.bind("<Down>", lambda e: self.change_throttle(-10))
        self.bind("<Left>", lambda e: self.change_rudder(-10))
        self.bind("<Right>", lambda e: self.change_rudder(10))       
        self.bind("<Next>", lambda e: self.boat.set_control(rudder=180 if self.boat.rudder >= 90 else 90)) #PageDown 
        self.bind("<Prior>", lambda e: self.boat.set_control(rudder=0 if self.boat.rudder <= 90 else 90))  #PageUp  
        self.bind("1", lambda e: self.boat.setModeManual())
        self.bind("2", lambda e: self.boat.setModeAP())
        self.bind("3", lambda e: self.boat.returnHome())
        self.bind("4", lambda e: self.boat.modeOverride())
        self.bind("M", lambda e: self.change_frame())
        #self.bind("l", lambda e: self.boat.change_light(10))
        #self.bind("k", lambda e: self.boat.change_light(-10))

        
    
    def toggle_theme(self):
        self.theme = self.DARK_THEME if self.theme == self.LIGHT_THEME else self.LIGHT_THEME
        self.apply_theme()
    
    def apply_theme(self):
        theme = self.theme
        self.configure(bg=theme["bg"])
        self.style.configure("Custom.TFrame", background=theme["bg"])
        self.style.configure("Custom.TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("Custom.TButton", background=theme["button_bg"], foreground=theme["fg"])
        if theme == self.LIGHT_THEME:
            self.waypointframe.wp_gui.configure(bg="#FFFFFF", fg="#000000")
            self.statusframe.controller_frame.canvas.config(bg="#FFFFFF")
        else:
            self.waypointframe.wp_gui.configure(bg="#333237", fg="#FFFFFF")
            self.statusframe.controller_frame.canvas.config(bg="#333237")

    def change_frame(self):  #Vaihtaa FPV:n ja kameran välillä
        if self.active_frames_shown == 0:
            self.mapframe.grid_remove()
            self.waypointframe.grid_remove()          
            self.cameraframe.grid(row=0, column=1, columnspan=2, sticky="nsew")
            self.mapframe.grid(row=1, column=1, columnspan=2, pady=20, padx=20)
            self.statusframe.grid(row=0, column=0, rowspan=2)
            self.active_frames_shown = 1
        else:
            self.cameraframe.grid_remove()     
            self.mapframe.grid_remove()       
            self.statusframe.grid_remove()
            self.mapframe.grid(row=0, column=1, sticky="nsew")
            self.waypointframe.grid(row=0, column=2, sticky="nsew") 
            self.statusframe.grid(row=0, column=0)
            self.active_frames_shown = 0

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
        if len(self.wp_list) < 255:
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
        if self.boat.t_home_coords[0] > 5 and self.boat.t_home_coords[1] > 5:
            self.mapframe.offline_map.set_marker(self.boat.t_home_coords[0], self.boat.t_home_coords[1], text=f"Home wp: {self.boat.t_home_coords}") #icon=self.mapframe.offline_map.home_icon)

    def draw_path(self):  #Käytä aina tätä, älä luo erillisiä viivoja
        if (self.boat.t_mode in (0, 1) ) and (len(self.wp_list) > 1):
            self.mapframe.offline_map.set_path(self.wp_list)
        elif self.boat.t_mode == 2 and (self.boat.t_current_coords[0] + self.boat.t_current_coords[1] != 0) and (len(self.wp_list) > 1):
            path_coords: list[tuple] = [self.boat.t_current_coords] + self.wp_list[self.boat.t_target_wp - 1:]
            self.mapframe.offline_map.set_path(path_coords)
        elif (self.boat.t_mode == 3) and (self.boat.t_current_coords[0] + self.boat.t_current_coords[1] != 0) and (self.boat.t_home_coords[0] + self.boat.t_home_coords[1] > 10) and (self.boat.t_current_coords != self.boat.t_home_coords):
            path_coords = [self.boat.t_current_coords, self.boat.t_home_coords]
            self.mapframe.offline_map.set_path(path_coords)

    def periodic_update(self):
        self.mapframe.offline_map.delete_all_path()
        self.draw_path()
        self.after(1000, self.periodic_update)

class StatusFrame(ttk.Frame):  # Kartan vasen puoli
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.bg_color = container.bg_color

        #Otsikko
        self.label_wp =ttk.Label(self, text="Vene Status:", font=("Inter", 17, "bold"), style="Custom.TLabel")
        self.label_wp.pack(side="top", anchor="w", padx=20, pady=10)

        self.boat = boat

        #Yhteysindikaattori
        self.connection_label = ttk.Label(self, text=f"Connected to Vene: False", font=("Inter", 13), style="Custom.TLabel")
        self.connection_label.pack(side="top", anchor="w", padx=20, pady=10)

        #Luetaan Veneen output
        self.receive_label =ttk.Label(self, text="Received from Vene:", font=("Inter", 10, "bold"), style="Custom.TLabel")
        self.receive_label.pack(side="top", anchor="w", padx=30, pady=(30,0))
        
        self.telemetry_frame = ttk.Frame(self,  style="Custom.TFrame")
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
            lbl =ttk.Label(self.telemetry_frame, text=f"{var}: ---", style="Custom.TLabel")
            lbl.grid(row=i, column=0, sticky="w")
            self.telemetry_labels[var] = lbl
        self.telemetry_frame.pack(side="top", anchor="w", padx=60, pady=10)

        #Luetaan Veneen input
        self.send_label =ttk.Label(self, text="Sending to Vene:", font=("Inter", 10, "bold"), style="Custom.TLabel")
        self.send_label.pack(side="top", anchor="w", padx=30, pady=(30,0))

        self.controls_frame = ttk.Frame(self, style="Custom.TFrame")
        self.control_labels = {}

        self.control_vars = {
            "rudder": "Rudder",
            "throttle": "Throttle",
            "light_mode": "Lights",
            "_Vene__debugmode": "Debug mode"
        }

        for i, var in enumerate(self.control_vars):
            lbl =ttk.Label(self.controls_frame, text=f"{self.control_vars[var]}: ---", style="Custom.TLabel")
            lbl.grid(row=i, column=0, sticky="w")
            self.control_labels[var] = lbl
        
        self.controls_frame.pack(side="top", anchor="w", padx=60, pady=10)

        #Ohjainruutu
        self.controller_frame = ControllerFrame(self, self.boat)
        self.controller_frame.pack(side="bottom", anchor="w", padx=40, pady=(60,40))

        
        self.update_gui()
        
        self.sum = 0

        self.check_connection()

        

    def check_connection(self):
        if self.boat._Vene__shutdown_flag:
            self.connection_label.config(text="No connection: 0 pps", style="Custom.TLabel")
        else:
            match self.boat.t_packets_rcv:                
                case x if 0 <= x < 4:
                    self.connection_label.config(text=f"Connected to Vene: {self.boat.t_packets_rcv} pps", style="Red.TButton")
                case _:
                    self.connection_label.config(text=f"Connected to Vene: {self.boat.t_packets_rcv} pps", style="Green.TButton")
            
        self.after(1000, self.check_connection) 
            
    def update_gui(self):
        for var, lbl in self.telemetry_labels.items():
            display_name = self.telemetry_vars.get(var, var)  #dict.get()
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        for var, lbl in self.control_labels.items():
            display_name = self.control_vars.get(var, var)
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        self.after(200, self.update_gui) 

class WaypointFrame(ttk.Frame):  # Kartan oikea puoli
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.container = container
        self.boat = boat

        #Waypoint-lista
        self.wp_amount = tk.StringVar(value=f"Waypoints: ({len(container.wp_list)}/255)")
        self.wp_label = ttk.Label(self, textvariable=self.wp_amount, style="Custom.TLabel")
        self.wp_label.pack(anchor="w", padx=80, pady=(10,5))

        self.wp_gui = tk.Listbox(self, width=25, font=("Inter", 10))
        self.wp_gui.pack(fill=tk.BOTH, expand="y", padx=(55,50), pady=5)

        def remove_index(event): 
            index = self.wp_gui.nearest(event.y)
            if index != None and len(container.wp_list) > 0:
                self.wp_gui.delete(index)
                container.wp_list.pop(index)
            self.update_wp_gui(container.wp_list, container.mapframe)
        
        self.wp_gui.bind("<Button 3>", remove_index)

        ttk.Button(
            self,
            text="Clear all waypoints",
            command=lambda: self.empty_wp(),
            style="Red.TButton"
            ).pack(anchor="w", padx=80, pady= 10)

    def empty_wp(self):
        self.wp_gui.delete(0, tk.END)
        self.container.wp_list.clear()
        self.container.redraw_map()
        self.wp_amount.set(f"Waypoints: (0/255)")
        

    def update_wp_gui(self, wp_list, mapframe):
        self.wp_gui.delete(0, tk.END)
        self.container.redraw_map()
        self.container.draw_path()
        self.wp_amount.set(f"Waypoints: ({len(wp_list)}/255)")

        for index, wp in enumerate(wp_list, start=1): #Indeksi visuaaliseen listaan, oikeassa wp-listassa ei ole indeksejä
            if 0 < (index) == self.boat.t_target_wp: #Korostaa target wp:n
                self.wp_gui.insert(tk.END, f"{index}: ({wp[0]:.4f}, {wp[1]:.4f})")
                self.wp_gui.itemconfig("end",bg="#00b16a")
            else:     
                self.wp_gui.insert(tk.END, f"{index}: ({wp[0]:.4f}, {wp[1]:.4f})")
            mapframe.wp_on_map(index, wp)

class ButtonFrame(ttk.Frame):
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.container = container

        #Modevalitsin
        self.mode_label = ttk.Label(self, text="Choose Mode: ", style='Custom.TLabel')
        self.mode_label.pack(anchor="w", padx=70, pady=(30, 5))

        self.boat = boat
        self.mode = tk.IntVar(value=0)

        
        self.style_active = "Green.TButton"
        self.style_inactive = "Custom.TButton"
        self.color1 = self.style_inactive
        self.color2 = self.style_inactive
        self.color3 = self.style_inactive
        self.color4 = self.style_inactive

        #Lista napeille
        self.buttons = []

        self.buttons.append(ttk.Button(self, text="Manual", command=lambda: self.boat.setModeManual(), style=self.color1, width=17))
        self.buttons.append(ttk.Button(self, text="Automatic", command=lambda: self.boat.setModeAP(container.wp_list), style=self.color2, width=17))
        self.buttons.append(ttk.Button(self, text="Return home", command=lambda: self.boat.returnHome(), style=self.color3, width=17))
        self.buttons.append(ttk.Button(self, text="Reset", command=lambda: self.boat.modeOverride(), style=self.color4, width=17))


        for button in self.buttons:
            button.pack(anchor="w", padx=80, pady=5)

        #Switch to FPV
        ttk.Button(
            self,
            text="Switch view",
            command=container.change_frame,
            width=17,
            style="Custom.TButton"
        ).pack(anchor="w", padx=80, pady=(40,5))

        #Dark mode toggle
        self.toggle_btn = ttk.Button(self, text="Toggle dark mode", style="Custom.TButton", command=container.toggle_theme, width=17)
        self.toggle_btn.pack(anchor="w", padx=80, pady=(5,0))

        # Start vcom
        ttk.Button(
            self,
            text="Start vcom",
            command=lambda: self.boat.start(),
            style="Custom.TButton",
            width=17
            ).pack(anchor="w", padx=80,pady=(40,5))
        # Stop vcom
        ttk.Button(
            self,
            text="Stop vcom",
            command=lambda: self.boat.shutdown(),
            style="Red.TButton",
            width=17
            ).pack(anchor="w", padx=80, pady=5)
        
        
        #Kello
        self.clock_label = ttk.Label(self, text="00:00:00", font=("Inter", 12, "normal"), style='Custom.TLabel')
        self.clock_label.pack(anchor="e", padx=15, pady=(10, 15))

        self.update_time()

    def update_time(self):
        current_time = strftime('%H:%M:%S')
        self.clock_label.config(text=current_time)
        # Värinvaihto mode-valintaan
        for index, button in enumerate(self.buttons, start=1):
            if index == self.boat.t_mode:
                button.config(style=self.style_active)
            else:
                button.config(style=self.style_inactive)
        self.after(1000, self.update_time)

class MapFrame(ttk.Frame):
    def __init__(self, container, boat, config_map):
        super().__init__(container, style="Custom.TFrame")

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

        self.boat = boat

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
        # Vene kartalla
        self.vene_marker = self.offline_map.set_marker(self.boat.t_current_coords[0], self.boat.t_current_coords[1], text=f"Vene: {self.boat.t_current_coords}", icon=self.vene_icon)
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
                self.vene_marker = self.offline_map.set_marker(new_lat, new_lon, text=f"Vene: {self.boat.t_current_coords}", icon=self.vene_icon)
            else:
                self.vene_marker.set_position(new_lat, new_lon)
                self.vene_marker.set_text(f"Vene: {self.boat.t_current_coords}")

        self.after(100, self.move_vene)

    def wp_on_map(self, index, wp):
        self.offline_map.set_marker(wp[0], wp[1], text=f"{index}")

class CameraFrame(ttk.Frame):
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.container = container
        self.boat = boat

        no_connection_image_path = os.path.join(self.container.mapframe.script_directory, "sus.png")
        self.no_connection_image = tk.PhotoImage(file=no_connection_image_path).subsample(2)
        self.img_label =ttk.Label(self, style="Custom.TLabel", image=self.no_connection_image)
        self.img_label.pack()
        

        self.camera_url = "http://192.168.4.2/capture"

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.schedule_update()
    
    def schedule_update(self):
        self.got_frame()
        self.after(2, self.schedule_update)

    def got_frame(self):
        frame = self.boat.get_frame()   #kuva update_framesta
        if frame is not None:
            width = self.winfo_width()
            height = self.winfo_height()
            a = Image.open(io.BytesIO(frame))
            img = ImageTk.PhotoImage(a.resize((width, height), Image.LANCZOS))
            self.img_label.config(image=img)
            self.img_label.image = img
        else:
            self.img_label.config(image=self.no_connection_image)
            self.img_label.image = self.no_connection_image
    
class ControllerFrame(ttk.Frame):
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.bg_color = container.bg_color

        self.controller_status = tk.StringVar(value="no_value")

        self.controller_status_label =ttk.Label(self, textvariable=self.controller_status, style="Custom.TLabel")
        self.controller_status_label.pack(anchor="w")

        self.controller = Controller(self, boat, config.CONTROLLER_CONFIG)

        # Piirtää viivat
        self.canvas = tk.Canvas(self, width=300, height=150, bg="#FFFFFF")
        self.canvas.pack(anchor="w")

        self.lx_line = self.canvas.create_line(0, 50, 150, 50, width=8, fill="#0073FF")
        self.thr_line = self.canvas.create_line(0, 100, 150, 100, width=8, fill="#6ED06E")

        self.line_center = 150
        self.line_length = 100

        self.update_lines()
        self.controller.poll_joystick(container)


    def update_lines(self):
        lx_offset = self.controller.axis0 * self.line_length
        
        if lx_offset >= 0:
            self.canvas.coords(self.lx_line, self.line_center, 50, self.line_center + lx_offset, 50)
        else:
            self.canvas.coords(self.lx_line, self.line_center + lx_offset, 50, self.line_center, 50)

        thr_offset = self.controller.total_thr * self.line_length
        
        if thr_offset >= 0:
            self.canvas.coords(self.thr_line, self.line_center, 100, self.line_center + thr_offset, 100)
        else:
            self.canvas.coords(self.thr_line, self.line_center + thr_offset, 100, self.line_center, 100)

        self.after(50, self.update_lines)

class Controller:
    def __init__(self, container, boat, config_controller):
        
        self.deadzone = config_controller.get("deadzone", 0.07) #config-tiedoston arvo, tai muuten 0.07
        self.poll_interval = config_controller.get("poll_interval", 50)

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No controller detected")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller connected: {self.joystick.get_name()}")

        self.controller_status = container.controller_status

        self.boat = boat
        self.axis0 = 0
        self.axis2 = 0
        self.axis5 = 0
        self.total_thr = (self.axis5 + 1) - (self.axis2 + 1)
        

    def poll_joystick(self, root):
        #Täällä on tuplakäynnistys: controller connected + status.set if-haarassa ja uudestaan else-haarassa
        #Tälle oli syynsä, mutta voisi ehkä yksinkertaistaa

        #Tarkistetaan, onko ohjain yhdistetty ja joystick-moduuli päällä.
        if self.controller_connected() and self.joystick is not None and self.joystick.get_init():
            self.controller_status.set("Controller connected")
            pygame.event.pump()
            self.axis0 = ( 0 if (abs(self.joystick.get_axis(0)) < self.deadzone) else self.joystick.get_axis(0))
            self.axis2 = ( 0 if (abs(self.joystick.get_axis(2)) < self.deadzone) else self.joystick.get_axis(2))
            self.axis5 = ( 0 if (abs(self.joystick.get_axis(5)) < self.deadzone) else self.joystick.get_axis(5))
            self.boat.set_control(throttle=int((((self.axis5 + 1)*0.7071)**2 * 50)-(((self.axis2 + 1)*0.7071)**2 * 50)), rudder=int((self.axis0 + 1) * 90)) #Input veneelle, logaritminen skaalaus vcomissa
        # Mikäli ohjainta ei ole/katoaa, nollataan joystick-moduuli. Jos ohjain on yhdistetty, mutta moduuli ei ole päällä, käynnistetään se.
        else:         
            self.axis0 = 0
            self.axis2 = 0
            self.axis5 = 0
            self.controller_status.set("No controller detected")
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print(f"Controller connected: {self.joystick.get_name()}")
            else:
                pygame.joystick.quit()

        self.total_thr = ((self.axis5 + 1) - (self.axis2 + 1)) / 2

        root.after(self.poll_interval, self.poll_joystick, root)

    def controller_connected(self):
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        return pygame.joystick.get_count() > 0

if __name__ == "__main__":
    app = VeneGui()
    app.protocol("WM_DELETE_WINDOW", app.destroy) #Sulkee ohjelman, mikäli ikkuna sulkeutuu
    app.mainloop()
