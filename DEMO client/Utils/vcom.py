# Copyright (C) 2025 Henri Paasonen - GPLv3
# See LICENSE for details

import socket
import struct 
import concurrent.futures
import time
from threading import Lock
import random  
import requests
from PIL import Image
import io
from pathlib import Path
from operator import xor

class Vene:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock: 
            if cls._instance is None:
                cls._instance = super().__new__(cls)  
        return cls._instance

    def __init__(self,):
        if getattr(self, "_initialized", False): 
            return

        self.version = 4.0 
        
        # TODO: Nimeä muuttujat paremmin (en usko että tulee tapahtumaan)
        self.__ESP_IP = "192.168.4.1"
        self.__RX_PORT = 4210
        self.__TX_PORT = 4211
        self.__tx_rate = 30
        self.__ap_tx_rate = 5
        self.__last_pps_calc_time = 0
        self.__packets_this_second = 0
        self.__camera_enabled = True
        self.__max_timestamp = 500
        self.__current_timestamp = 0

        self.__ESP_CAM_IP = "192.168.4.5"

        self.__mode = 1
        self.rudder = 0
        self.throttle = 100   #thr1, thr2
        self.light_mode = 0
        self.__debugmode = 0
        self.__last_wp_id = 0

        self.__latest_frame = None

        BASE_DIR = Path(__file__).parent

        # Jos ei saada live kuvaa niin palauttaa tän
        try:
            no_cam_image_path = str(BASE_DIR) + "\\Vcomicons\\noCamera.jpeg" #Icon made by: Ivan Abirawa from https://www.flaticon.com
            print(no_cam_image_path)

            #self.__no_connection_image = Image.open(no_cam_image_path).convert("RGB")
            
            img = Image.open(no_cam_image_path).resize((150, 150))
            padded = Image.new("RGB", (1000, 1000), (35, 35, 39))
            padded.paste(img, (425, 425), mask = img.split()[3]) 
            self.__no_connection_image = padded
        except Exception:
            self.__no_connection_image = Image.new("RGB", (320, 240), color = (120, 120, 120))

        # Telemetriamuuttujat
        self.t_mode = 0
        self.t_heading = 0
        self.t_speed = 0        
        self.t_current_coords = (0, 0)  #lat, lon
        self.t_battery = 0
        self.t_target_wp = 0
        self.t_gps_status = 0
        self.t_gen_error = 0
        self.t_packets_per_second = 0
        self.t_home_coords = (0, 0)
        self.t_packets_rcv = 0
        
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.__sock.bind(("", self.__RX_PORT))
        self.__sock.settimeout(0.8)

        self.__pool = None
        self.__shutdown_flag = True
        self.__t_start = int(time.time())

        print(f"VCom {self.version} loaded")

        self._initialized = True 

    # Kamera
    def enableCamera(self):
        self.__camera_enabled = True
        
    def disableCamera(self):
        self.__camera_enabled = False

    def __camera_loop(self):
        enabled = True
        l_fps = 0.5
        h_fps = 2
        target_fps = h_fps

        while not self.__shutdown_flag:
            if self.__camera_enabled:
                if self.t_packets_rcv < 5:
                    enabled = False
                else:
                    enabled = True
                    if self.t_packets_rcv > 7:
                        target_fps = h_fps
                    else:
                        target_fps = l_fps

                try:
                    if enabled:
                        url = f"http://{self.__ESP_CAM_IP}/capture"
                        img_data = requests.get(url, timeout = 1)
                        if img_data.status_code == 200:
                            self.__latest_frame = img_data.content
                        else:
                            self.__latest_frame = None
                    else:
                        self.__latest_frame = None
                except requests.RequestException:
                    self.__latest_frame = None

            time.sleep(1 / target_fps)

    def get_frame(self):
        if self.__latest_frame is not None:
            return self.__latest_frame
        else:
            img_buf = io.BytesIO()
            self.__no_connection_image.save(img_buf, format = "JPEG")
            return img_buf.getvalue()

    # Tekee mitä nimi sanoo
    def clamp(self, val, min_val, max_val):
        return max(min_val, min(val, max_val))

    #Esim. set_control(rudder = 80)
    def set_control(self, *, rudder = None, throttle = None, light_mode = None):
        
        if rudder is not None:
            self.rudder = self.clamp(rudder, 0, 180)
        
        if throttle is not None:
            if isinstance(throttle, tuple):
                thr1 = throttle[0] + 100
            else:
                thr1 = throttle + 100
            
            self.throttle = (self.clamp(thr1, 0, 200))

        #Ei vielä mitään käyttöä
        if light_mode is not None: 
            #self.light_mode = self.clamp(light_mode, 0, 255)
            print("light_mode not available")

    # Nimi selittää hyvin
    def setModeManual(self):
        self.__mode = 1
    # Sama juttu
    def setModeAP(self, wp_list):
        if len(wp_list) > 254:
            print("wp list too long")
        else:
            self.__send_wp(wp_list)
            self.__mode = 2

    def __send_wp(self, wp_list):
        wp_ammount = len(wp_list)
        wp_id = random.randint(0, 200)
        if wp_id == self.__last_wp_id:
            wp_id += 1 # Varmistetaan että ei sama id peräkkäin (aika huono tapa toteuttaa tää)
            self.__last_wp_id = wp_id
        self.__last_wp_id = wp_id 

        for index in range(wp_ammount):
            for x in range(3): # Varmuuden vuoksi lähetetään jokainen 3 kertaa
                packet = struct.pack("<B2i2B", index + 1, int(wp_list[index][0]*100000), int(wp_list[index][1] * 100000), wp_ammount, wp_id) # Indeksi 0 varatuu home WP
                self.__sock.sendto(packet, (self.__ESP_IP, self.__TX_PORT))
                time.sleep(0.01)
            time.sleep(0.03)

    def returnHome(self):
        self.__mode = 3

    def setHome(self):
        if self.t_mode == 1:
            self.__mode = 8
            time.sleep(0.2)
            self.__mode = 1
            self.t_home_coords = (60.18694888403153, 24.81968689516132)
        

    def modeOverride(self):
        self.__mode = 4
                
    def start(self):
        if self.__pool is not None:
            self.shutdown()  #Ei sammunut kunnolla
        
        self.__shutdown_flag = False
        self.__pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)
        self.__pool.submit(self.__recieve_loop)
        self.__pool.submit(self.__send_loop)
        self.__pool.submit(self.__camera_loop)

    def shutdown(self):
        self.__shutdown_flag = True

        # Yritä sulkee socket
        try:
            self.__sock.close()
        except Exception:
            pass
        
        # Sulje threadit jos on 
        if self.__pool:
            self.__pool.shutdown(wait = False)
            self.__pool = None

        self.t_packets_rcv = 0 # Näyttää kivalta (gui varmaa tarvii emt en puuhaile gui:n kanssa)

        # Uusi socket, sillä vanha suljettiin
        time.sleep(1)
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(("", self.__RX_PORT))
        self.__sock.settimeout(0.8)

    # Suht turha
    def set_rate(self, rate_hz):
        self.__tx_rate = rate_hz

    # Tämäkin
    def get_rate(self):
        return self.__tx_rate
    
    # 0: Ei debug, 1: Kyllä debug, 2: Next WP (toimii TOSI huonosti)
    def debugmode(self, a):
        self.__debugmode = a

    def calculate_checsum(self, data):
        c = 0
        for x in data:
            c ^= x #xor
        return c
    
    def __recieve_loop(self):
        while not self.__shutdown_flag:
            if (time.time() - self.__last_pps_calc_time >= 1):
                self.t_packets_rcv = self.__packets_this_second
                self.__packets_this_second = 0
                self.__last_pps_calc_time = time.time()
            
            # Yritä, muuten jää jumiin
            try:
                data, _ = self.__sock.recvfrom(1024)
            except socket.timeout:
                continue

            if len(data) == 16:
                unpacked = struct.unpack("<4B2H2i", data)
                (
                    self.t_mode,
                    self.t_battery,
                    self.t_packets_per_second,
                    self.t_speed,
                    self.t_heading,
                    error,
                    lat,   
                    lon,
                ) = unpacked
                self.t_battery = round((float(self.t_battery) / 100) + 2.5, 2)
                
                latFloat = float(lat / 100000)
                lonFloat = float(lon / 100000)

                # Päivitä home WP jos mode 9, muuten tämänhetkinen sijainti
                if self.t_mode != 9:
                    self.t_current_coords = (60.18694888403153, 24.81968689516132)
                else:
                    self.t_home_coords = (60.18694888403153, 24.81968689516132)

                # Muuta error (hieman) järkevämpään muotoon
                target = error & 0x3FF
                self.t_gps_status = 0
                self.t_gen_error = 1

                # Target WP on 0 jos manuaalinen ohjaus (näyttää kivalta)
                if self.t_mode == 1:
                    self.t_target_wp = 0
                else:
                    self.t_target_wp = target

                self.__packets_this_second += 1

            else:
                print(f"Unexpected packet size: {len(data)}") # Uh oh :(
    
    def __send_loop(self):
        while not self.__shutdown_flag:

            self.light_mode = 100 #AP kaasu nykyään

            thr1 = self.throttle
            
            # Tarviiko home WP päivittää (jos gui käynnistetty veneen jälkeen)
            #if self.t_gen_error == 1 and self.t_home_coords[0] == 0:
            #    a = 9
            #else:
            #    a = self.__mode

            if self.__current_timestamp < self.__max_timestamp:
                self.__current_timestamp += 1
            else:
                self.__current_timestamp = 0

            checksum_data = struct.pack("<3B", self.__mode, self.rudder, thr1)
            checksum = self.calculate_checsum(checksum_data)

            packet = struct.pack("<6BH", 
                        self.__mode, # MODE
                        self.rudder,
                        thr1,
                        checksum,
                        self.light_mode,
                        self.__debugmode,
                        int(self.__current_timestamp),
                        )
            
            self.__sock.sendto(packet, (self.__ESP_IP, self.__TX_PORT))

            # Adaptiivinen TX Rate
            if self.t_mode == 2:
                time.sleep(1 / self.__ap_tx_rate)
            else:
                time.sleep(1 / self.__tx_rate)

if __name__ == "__main__":
    print("vcom cannot run standalone!")
    quit()
