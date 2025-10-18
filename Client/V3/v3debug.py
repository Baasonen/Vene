import tkinter as tk
from tkinter import ttk
import random
from vcom import Vene
import time


class DebugGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vene Debugger")

        self.boat = Vene()
        self.boat.start()
        self.boat.debugmode(1)

        # Updated telemetry vars
        telemetry_frame = ttk.LabelFrame(root, text="Telemetry")
        telemetry_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.telemetry_labels = {}
        telemetry_vars = [
            "t_mode", "t_heading", "t_speed",
            "t_current_coords", "t_home_coords", "t_battery", "t_target_wp",
            "t_gps_status", "t_gen_error", "t_packets_per_second", "t_packets_rcv"
        ]
        for i, var in enumerate(telemetry_vars):
            lbl = ttk.Label(telemetry_frame, text=f"{var}: ---")
            lbl.grid(row=i, column=0, sticky="w")
            self.telemetry_labels[var] = lbl

        # Control labels
        controls_frame = ttk.LabelFrame(root, text="Controls")
        controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.control_labels = {}
        control_vars = ["t_mode", "rudder", "throttle", "light_mode"]
        for i, var in enumerate(control_vars):
            lbl = ttk.Label(controls_frame, text=f"{var}: ---")
            lbl.grid(row=i, column=0, sticky="w")
            self.control_labels[var] = lbl

        # Keybindings
        root.bind("<Up>", lambda e: self.change_throttle(10))
        root.bind("<Down>", lambda e: self.change_throttle(-10))
        root.bind("<Left>", lambda e: self.change_rudder(-10))
        root.bind("<Right>", lambda e: self.change_rudder(10))
        root.bind("1", lambda e: self.set_mode_manual())
        root.bind("2", lambda e: self.set_mode_ap())
        root.bind("3", lambda e: self.set_return_home())
        root.bind("4", lambda e: self.set_mode_override())
        root.bind("l", lambda e: self.change_light(10))
        root.bind("k", lambda e: self.change_light(-10))
        root.bind("9", lambda e: self.next_wp())

        self.update_gui()

    def update_gui(self):
        for var, lbl in self.telemetry_labels.items():
            lbl.config(text=f"{var}: {getattr(self.boat, var)}")

        for var, lbl in self.control_labels.items():
            lbl.config(text=f"{var}: {getattr(self.boat, var)}")

        self.root.after(200, self.update_gui)

    def next_wp(self):
        self.boat.debugmode(2)
        time.sleep(1.5)
        self.boat.debugmode(1)

    def change_rudder(self, delta):
        new_val = self.boat.rudder + delta
        self.boat.set_control(rudder=new_val)

    def change_throttle(self, delta):
        thr1, thr2 = self.boat.throttle
        thr1 += delta
        thr2 += delta
        self.boat.set_control(throttle=(thr1, thr2))

    def change_light(self, delta):
        new_val = self.boat.light_mode + delta
        self.boat.set_control(light_mode=new_val)

    def set_mode_manual(self):
        self.boat.setModeManual()

    def set_mode_ap(self):
        dummy_wp_list = []
        for x in range(64):
            a = (random.randint(0, 60), random.randint(0, 60))
            dummy_wp_list.append(a)
        self.boat.setModeAP(dummy_wp_list)

    def set_return_home(self):
        self.boat.returnHome()

    def set_mode_override(self):
        self.boat.modeOverride()


def run():
    root = tk.Tk()
    app = DebugGUI(root)
    try:
        root.mainloop()
    finally:
        app.boat.shutdown()


if __name__ == "__main__":
    run()
