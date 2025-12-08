import tkinter as tk
from tkinter import ttk
import Utils.config as config
from .controllerframe import ControllerFrame

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
            self.connection_label.config(text="vcom disabled: 0 pps", style="Custom.TLabel")
        else:
            match self.boat.t_packets_rcv:                
                case x if 0 <= x < 4:
                    self.connection_label.config(text=f"vcom enabled: {self.boat.t_packets_rcv} pps", style="Red.TButton")
                case _:
                    self.connection_label.config(text=f"vcom enabled: {self.boat.t_packets_rcv} pps", style="Green.TButton")
            
        self.after(1000, self.check_connection) 
            
    def update_gui(self):
        for var, lbl in self.telemetry_labels.items():
            display_name = self.telemetry_vars.get(var, var)  #dict.get()
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        for var, lbl in self.control_labels.items():
            display_name = self.control_vars.get(var, var)
            lbl.config(text=f"{display_name}: {getattr(self.boat, var)}")

        self.after(200, self.update_gui) 
