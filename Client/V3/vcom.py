import concurrent.futures
import struct
import socket
from var.py import *


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", __RX_PORT))

def recieve():
    while True:
        data = sock.recvfrom(1024)
        print(struct.calcsize("<3B2Hll"))
        if len(data[0]) == 15:
            temp = struct.unpack("<3B2H2l", data[0])

def send():
    while True:
        packet = struct.pack("<8BH", 