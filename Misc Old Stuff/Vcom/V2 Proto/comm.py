import socket
import struct
import time as t
import os

def clear():
    os.system("cls")

t_start = int(t.time())

ESP32_IP = "192.168.4.1"
ESP32_PORT_RX = 4210
ESP32_PORT_TX = 4211
TX_RATE = 100

MODE = 0
HDG = 0
TARGET_HDG = 0
THROTTLE = 0
LIGHT_MODE = 0

VENE_MODE = 0
VENE_HDG = 0
VENE_NOPEUS = 0
VENE_KALLISTUS = 0
VENE_LAT = 0
VENE_LON = 0
VENE_BATT = 0
VENE_ERR = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", ESP32_PORT_TX))

def recieve():
    while True:
        data, addr = sock.recvfrom(1024)
        if len(data) == 20:
            a = socket.unpack("<BhhhBBB", data)

def send():
    while True:
        global MODE, HDG, TARGET_HDG, THROTTLE
        if MODE == 0:
            a = HDG
        else:
            a = TARGET_HDG

        packet = struct.pack("<BhBBBh", MODE, a, THROTTLE, THROTTLE, LIGHT_MODE, int(t.time() - t_start))
        #print(packet)
       # print(struct.calcsize("<BhBBh"))
        clear()
        print(struct.unpack("<BhBBBh", packet), packet)
        #print(int(t.time() - t_start))
        sock.sendto(packet, (ESP32_IP, ESP32_PORT_TX))
        #print("Sent", MODE, HDG, THROTTLE)
        t.sleep(1 / TX_RATE)

