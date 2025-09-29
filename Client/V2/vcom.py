import socket
import struct
import time as t
import concurrent.futures
import os

v = 2.0

os.system("cls")
print("################################################################")
print(f"Vene Communication Module v{v}, vcom.help() for instructions")
print("################################################################")

pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)

t_start = int(t.time())

SHUTDOWN_FLAG = True

def shutdown():
    global SHUTDOWN_FLAG
    pool.shutdown(wait = False)
    SHUTDOWN_FLAG = True

def start():
    global SHUTDOWN_FLAG
    SHUTDOWN_FLAG = False
    pool.submit(recieve)
    pool.submit(send)

ESP32_IP = "192.168.4.1"
ESP32_PORT_RX = 4210
ESP32_PORT_TX = 4211
TX_RATE = 100

# Outgoing variables
MODE = 0
HDG = 0
TARGET_HDG = 0
THROTTLE = 0
LIGHT_MODE = 0

# Incomming variables
VENE_MODE = 0
VENE_HDG = 0
VENE_SPEED = 0
VENE_TILT = 0
VENE_LAT = 0
VENE_LON = 0
VENE_BATT = 0
VENE_ERR = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", ESP32_PORT_RX))

def set_rate(rate):
    global TX_RATE
    TX_RATE = int(rate)

def get_rate():
    global TX_RATE
    return TX_RATE

def recieve():
    global VENE_MODE, VENE_HDG, VENE_SPEED, VENE_TILT
    global VENE_LAT, VENE_LON, VENE_BATT, VENE_ERR, SHUTDOWN_FLAG
    while True:
        if SHUTDOWN_FLAG == True:
            break
        data, addr = sock.recvfrom(1024)
        if len(data) == 11:
            a = struct.unpack("<BHBBllBB", data)
            VENE_MODE, VENE_HDG, VENE_SPEED, VENE_TILT, VENE_LAT, VENE_LON, VENE_BATT, VENE_ERR = a
        else:
            print(len(data))

def send():
    global MODE, HDG, TARGET_HDG, THROTTLE
    while True:
        if SHUTDOWN_FLAG == True:
            break
        
        a = HDG

        packet = struct.pack("<BhBBBh", MODE, a, THROTTLE, THROTTLE, LIGHT_MODE, int(t.time() - t_start))
 
        sock.sendto(packet, (ESP32_IP, ESP32_PORT_TX))

        t.sleep(1 / TX_RATE)

def help():
    os.system("cls")
    print("##########################################################")
    print(f"Vene Communication Module v{v}   Henri Paasonen 2025")
    print("##########################################################")
    print("")
    print("Functions: ")
    print("shutdown (No Args), shuts down recieve and transmith threads")
    print("set_rate (Int), sets the frequency of controll packets sent (Hz)")
    print("get_rate(No Args), returns the current frequency of transmission (Hz)")
    print("")
    print("Variables (Write):")
    print("MODE (Mode select to be sent to esp)")
    print("HDG and TARGET_HDG (sent to esp depending on selected mode)")
    print("THROTTLE (0 - 100)")
    print("LIGHT_MODE (0 - 255)")
    print("")
    print("Variables (Read):")
    print("VENE_MODE, VENE_HDG, VENE_SPEED, VENE_TILT")
    print("VENE_LAT, VENE_LON, VENE_BATT, VENE_ERR")

if __name__ == "__main__":
    print("Unable to be started standalone!")
    os._exit(1)
