import socket
import struct
import time as t

ESP32_IP = "192.168.4.1"
ESP32_PORT_RX = 4210
ESP32_PORT_TX = 4211
TX_RATE = 10

MODE = 0
HDG = 90
TARGET_HDG = 0
THROTTLE = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", ESP32_PORT_TX))

def recieve():
    while True:
        data, addr = sock.recvfrom(1024)
        if len(data) == 20:
            telemetry = struct.unpack("<5f", data)
            print(telemetry)

def send():
    while True:
        global MODE, HDG, TARGET_HDG, THROTTLE
        if MODE == 0:
            a = HDG
        else:
            a = TARGET_HDG

        packet = struct.pack("<4if", MODE, a, THROTTLE, THROTTLE, t.time())
        sock.sendto(packet, (ESP32_IP, ESP32_PORT_TX))
        t.sleep(1 / TX_RATE)

