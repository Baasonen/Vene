import tkinter as tk
from tkinter import ttk


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
        self.container.mapframe.redraw_map()
        self.wp_amount.set(f"Waypoints: (0/255)")
        

    def update_wp_gui(self, wp_list, mapframe):
        self.wp_gui.delete(0, tk.END)
        self.container.mapframe.redraw_map()
        self.container.mapframe.draw_path()
        self.wp_amount.set(f"Waypoints: ({len(wp_list)}/255)")

        for index, wp in enumerate(wp_list, start=1): #Indeksi visuaaliseen listaan, oikeassa wp-listassa ei ole indeksejä
            if 0 < (index) == self.boat.t_target_wp: #Korostaa target wp:n
                self.wp_gui.insert(tk.END, f"{index}: ({wp[0]:.4f}, {wp[1]:.4f})")
                self.wp_gui.itemconfig("end",bg="#00b16a")
            else:     
                self.wp_gui.insert(tk.END, f"{index}: ({wp[0]:.4f}, {wp[1]:.4f})")
            mapframe.wp_on_map(index, wp)