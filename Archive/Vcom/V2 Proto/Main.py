import concurrent.futures
import pygame
import comm
import tkinter as tk

pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)

pool.submit(comm.recieve)
pool.submit(comm.send)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No Controller")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()

DEADZONE = 0.05

root = tk.Tk()
root.title("VeneV2")

canvas = tk.Canvas(root, width = 300, height = 200, bg = "white")
canvas.pack()

lx_line = canvas.create_line(0, 50, 150, 50, width=4, fill="blue")   # initial
thr_line = canvas.create_line(0, 150, 150, 150, width=4, fill="green")


def update():
    pygame.event.pump()
    lx = controller.get_axis(0)
    if abs(lx) < DEADZONE:
        lx = 0
    lx = int(90 + (lx * 90))
    thr = int((controller.get_axis(5) + 1) * 50)
    #if controller.get_button(0) == True:
    #    if Comm.MODE == 0:
    #        Comm.MODE = 1
    #    else:
    #        Comm.MODE = 0
    comm.THROTTLE = thr
    comm.HDG = lx
    lx_x = 50 + (lx / 180) * 200
    thr_x = 50 + (thr / 100) * 200
    canvas.coords(lx_line, 50, 50, lx_x, 50)
    canvas.coords(thr_line, 50, 150, thr_x, 150)
    root.after(50, update)


update()
root.mainloop()