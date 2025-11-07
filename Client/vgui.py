import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont # Voisi ehkä toteuttaa ilmankin

#Paikalliset tiedostot
from vcom import Vene
import config
#Framet
from Frames.statusframe import StatusFrame
from Frames.waypointframe import WaypointFrame
from Frames.cameraframe import CameraFrame
from Frames.mapframe import MapFrame
from Frames.buttonframe import ButtonFrame

class VeneGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Vene Gui V3')

        self.boat = Vene()

        #Debugmode
        self.boat.debugmode(config.DEBUG_MODE)

        # Waypointit
        self.wp_list = []

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

        # Create frames
        self.statusframe = StatusFrame(self, self.boat)
        self.statusframe.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=15)

        self.mapframe = MapFrame(self, self.boat, config.MAP_CONFIG, self.wp_list)
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
        self.mapframe.draw_path()



if __name__ == "__main__":
    app = VeneGui()
    app.protocol("WM_DELETE_WINDOW", app.destroy) #Sulkee ohjelman, mikäli ikkuna sulkeutuu
    app.mainloop()
