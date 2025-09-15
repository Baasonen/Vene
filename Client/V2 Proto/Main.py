import concurrent.futures
import pygame
import Comm


pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)

pool.submit(Comm.recieve)
pool.submit(Comm.send)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No Controller")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()

DEADZONE = 0.05

while True:
    pygame.event.pump()

    lx = controller.get_axis(0)
    if abs(lx) < DEADZONE:
        lx = 0
    
    thr = int((controller.get_axis(5) + 1) * 50)

    if controller.get_button(0):
        if Comm.MODE == 0:
            Comm.MODE = 1
        else:
            Comm.MODE = 0

    Comm.THROTTLE = thr
    Comm.HDG = lx

