import socket
import time as t

tickrate = 0.05

def get_tickrate():
    return tickrate

ESP32_IP = "192.168.4.1"
ESP32_RX_PORT = 4210
ESP32_TX_PORT = 4211

# Globals
HDG = 90
THR = 0

sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock_rx.bind(("", ESP32_TX_PORT))

def listen():
    while True:
        data, addr = sock_rx.recvfrom(1024)
        print(f"Recieved: {data.decode()}")

def send():
    while True:
        msg = str((HDG, THR))

        sock_tx.sendto(msg.encode(), (ESP32_IP, ESP32_RX_PORT))
        print(f"Sent: {msg}")
        t.sleep(0.05)


def set_hdg(a):
    global HDG
    HDG = a

def set_thr(a):
    global THR
    THR = a