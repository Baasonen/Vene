import tkinter as tk
from tkinter import ttk
from time import strftime #Ruudun alakulman kelloa varten

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

        #Set home
        ttk.Button(
            self,
            text="Set home waypoint",
            command=lambda:self.boat.setHome(),
            width=17,
            style="Custom.TButton"
        ).pack(anchor="w", padx=80, pady=(5))

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
