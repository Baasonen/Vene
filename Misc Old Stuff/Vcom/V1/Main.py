import time as t
import pygame



# Setup Threading
import concurrent.futures
pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)


# Setup Communications
import comm
pool.submit(comm.listen)
pool.submit(comm.send)

tickrate = comm.get_tickrate()


# Pygame
pygame.init()
pygame.joystick.init()


if pygame.joystick.get_count() == 0:
    print("No Controller")
    exit()

    

controller = pygame.joystick.Joystick(0)
controller.init()


# Controller mapping
DEADZONE = 0.05


# Mainloop
while True:
    pygame.event.pump()

    lx = controller.get_axis(0)

    thr = round((float(controller.get_axis(5) + 1) / 2), 2)
        
    if abs(lx) < DEADZONE:
        lx = 0

    angle = (lx + 1) * 90
    angle = round(float(angle), 2)

    comm.set_hdg(angle)
    comm.set_thr(thr)
    t.sleep(tickrate)


# Shutdown

#pool.shutdown(wait = False)


