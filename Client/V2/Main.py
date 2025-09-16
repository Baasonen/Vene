import concurrent.futures
import pygame
import vcom
import tkinter as tk
import math


pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No Controller")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()

DEADZONE = 0.05

# Tk setup

root = tk.Tk()
root.title("VeneV2")

canvas = tk.Canvas(root, width = 300, height = 200, bg = "white")
canvas.pack()

lx_line = canvas.create_line(0, 50, 150, 50, width=4, fill="blue")

thr_line = canvas.create_line(0, 150, 150, 150, width=4, fill="green")

battery_label = tk.Label(root, text="Battery: 0%")
battery_label.pack()

gps_label = tk.Label(root, text="GPS: 0, 0")
gps_label.pack()

heading_label = tk.Label(root, text="Heading: 0°")
heading_label.pack()

speed_label = tk.Label(root, text="Speed: 0")
speed_label.pack()

roll_label = tk.Label(root, text="Roll: 0°")
roll_label.pack()

mode_label = tk.Label(root, text="Mode: ERROR", bg="red", fg="white", width=20)
mode_label.pack(pady=5)

vcom.start()


def update():
    pygame.event.pump()
    lx = controller.get_axis(0)
    if abs(lx) < DEADZONE:
        lx = 0
    lx = int(90 + (lx * 90))

    thr = int((controller.get_axis(5) + 1) * 50)

    if controller.get_button(0) == True:
        vcom.MODE = 1

    if controller.get_button(1) == True:
        vcom.MODE = 2
        vcom.shutdown()

    vcom.THROTTLE = thr
    vcom.HDG = lx


    # Steering / Throttle bars
    steer_center = 150
    steer_length = 100
    lx_offset = (lx - 90) / 90 * steer_length  # -100 .. +100
    
    if lx_offset >= 0:
        canvas.coords(lx_line, steer_center, 50, steer_center + lx_offset, 50)
    else:
        canvas.coords(lx_line, steer_center + lx_offset, 50, steer_center, 50)


    thr_x = 50 + (thr / 100) * 200
    canvas.coords(thr_line, 50, 150, thr_x, 150)

    # Telemetry labels
    battery_label.config(text=f"Battery: {vcom.VENE_BATT}%")
    gps_label.config(text=f"GPS: {vcom.VENE_LAT}, {vcom.VENE_LON}")
    heading_label.config(text=f"Heading: {vcom.VENE_HDG}°")
    speed_label.config(text=f"Speed: {vcom.VENE_SPEED}")
    roll_label.config(text=f"Roll: {vcom.VENE_TILT}°")

    # Mode indicator
    mode = vcom.VENE_MODE
    if mode == 0:
        mode_label.config(text="Mode: ERROR", bg="red")
    elif mode == 1:
        mode_label.config(text="Mode: MANUAL", bg="yellow")
    elif mode == 2:
        mode_label.config(text="Mode: AUTOPILOT", bg="green")
    else:
        mode_label.config(text=f"Mode: {mode}", bg="gray")


    root.after(50, update)


update()
root.mainloop()