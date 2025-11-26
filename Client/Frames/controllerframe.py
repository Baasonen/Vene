import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" #Täysin varastettua koodia, estää pygame printtaamasta tervehdyksen

import tkinter as tk
from tkinter import ttk
import pygame
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.config as config



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
            self.axis2 = ( 0 if (abs(self.joystick.get_axis(4)) < self.deadzone) else self.joystick.get_axis(4))
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

        self.total_thr = (self.axis5 + 1) #((self.axis5 + 1) - (self.axis2 + 1)) / 2
        print(self.total_thr)

        root.after(self.poll_interval, self.poll_joystick, root)

    def controller_connected(self):
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        return pygame.joystick.get_count() > 0