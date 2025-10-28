
import socket
import struct 
import concurrent.futures
import time
from threading import Lock
import math  
import requests

class Vene:
    _instance = None
    _lock = Lock() #En tiiä

    def __new__(cls, *args, **kwargs):
        with cls._lock: 
            if cls._instance is None:
                cls._instance = super().__new__(cls)  #Joo o
        return cls._instance

    def __init__(self,):
        if getattr(self, "_initialized", False):  #Aika hieno ja selkee funktio
            return

        self.version = 3.5
        
        self.__ESP_IP = "192.168.4.1"
        self.__RX_PORT = 4210
        self.__TX_PORT = 4211
        self.__tx_rate = 100
        self.__last_pps_calc_time = 0
        self.__packets_this_second = 0

        self.__esp_cam_ip = "192.168.4.2"

        #Pls älä laita näille arvoja, käytä set_control
        self.__mode = 1
        self.rudder = 0
        self.throttle = (0, 0)   #thr1, thr2
        self.light_mode = 0
        self.__debugmode = 0
        self.__last_wp_id = 0

        # Telemetry data, can be accessed as variables
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
        
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(("", self.__RX_PORT))
        self.__sock.timeout(0.8)

        self.__pool = None
        self.__shutdown_flag = True
        self.__t_start = int(time.time())

        print(f"VCom {self.version}")

        self._initialized = True 

    def set_camera(self, enabled, fps):
        try:
            control_url = f"http://{self.__esp_cam_ip}/control?enabled={int(enabled)}&fps={fps}"
            requests.get(control_url, timeout = 0.2)
        except requests.RequestException:
            pass
    
    def clamp(self, val, min_val, max_val):
        return max(min_val, min(val, max_val))
    
    def thr_map(self, input):
        input = (input * 0.7071) ** 2

        return input + 100

    #Esim. set_control(rudder = 80)
    def set_control(self, *, rudder = None, throttle = None, light_mode = None):
        
        if rudder is not None:
            self.rudder = self.clamp(rudder, 0, 180)
        
        if throttle is not None:
            if isinstance(throttle, tuple):
                thr1 = self.thr_map(throttle[0])
                thr2 = self.thr_map(throttle[1])
            else:
                thr1 = thr2 = self.thr_map(throttle)
            
            self.throttle = (self.clamp(thr1, 0, 200), self.clamp(thr2, 0, 200))

        if light_mode is not None:
            self.light_mode = self.clamp(light_mode, 0, 255)

    def setModeManual(self):
        self.__mode = 1

    def setModeAP(self, wp_list):
        if len(wp_list) > 64:
            print("wp list too long")
        else:
            self.__send_wp(wp_list)
            self.__mode = 2

    def __send_wp(self, wp_list):
        wp_ammount = len(wp_list)
        wp_id = int((math.sin(time.time()) * 100) + 100)
        if wp_id == self.__last_wp_id:
            wp_id += 1
            self.__last_wp_id = wp_id
        self.__last_wp_id = wp_id

        for index in range(wp_ammount):
            for x in range(3):
                packet = struct.pack("<B2i2B", index + 1, int(wp_list[index][0]*100000), int(wp_list[index][1] * 100000), wp_ammount, wp_id)
                self.__sock.sendto(packet, (self.__ESP_IP, self.__TX_PORT))
                time.sleep(0.01)
            time.sleep(0.04)

    def returnHome(self):
        self.__mode = 3

    def modeOverride(self):
        self.__mode = 4
                
    def start(self):
        if self.__pool is not None:
            self.shutdown()  #En keksi parempaakaa ratkasuu

        self.__shutdown_flag = False
        self.__pool = concurrent.futures.ThreadPoolExecutor(max_workers = 2)
        self.__pool.submit(self.__recieve_loop)
        self.__pool.submit(self.__send_loop)

    def shutdown(self):
        self.__shutdown_flag = True
        
        if self.__pool:
            self.__pool.shutdown(wait = False)
            self.__pool = None

    def set_rate(self, rate_hz):
        self.__tx_rate = rate_hz

    def get_rate(self):
        return self.__tx_rate
    
    def debugmode(self, a):
        self.__debugmode = a
    
    def __recieve_loop(self):
        while not self.__shutdown_flag:
            if (time.time() - self.__last_pps_calc_time >= 1):
                self.t_packets_rcv = self.__packets_this_second
                self.__packets_this_second = 0
                self.__last_pps_calc_time = time.time()

                # Fps control
                if self.t_packets_rcv < 2:
                    self.set_camera(enabled = False)
                elif self.t_packets_rcv < 4:
                    self.set_camera(enabled = True, fps = 5)
                else:
                    self.set_camera(enabled = True, fps = 10)
            
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
                
                latFloat = float(lat / 100000)
                lonFloat = float(lon / 100000)
                if self.t_mode != 9:
                    self.t_current_coords = (latFloat, lonFloat)
                else:
                    self.t_home_coords = (latFloat, lonFloat)

                target = error & 0x7F
                self.t_gps_status = (error >> 7) & 0x03
                self.t_gen_error = error >> 9
                if self.t_mode == 1:
                    self.t_target_wp = 0
                else:
                    self.t_target_wp = target

                self.__packets_this_second += 1

            else:
                print(f"Unexpected packet size: {len(data)}")
    
    def __send_loop(self):
        while not self.__shutdown_flag:
            thr1, thr2 = self.throttle
            if self.t_mode == 1 and self.t_home_coords[0] == 0:
                a = 9
            else:
                a = self.__mode

            packet = struct.pack("<6BH", 
                        a,
                        self.rudder,
                        thr1,
                        thr2,
                        self.light_mode,
                        self.__debugmode,
                        int(time.time() - self.__t_start),
                        )
            
            self.__sock.sendto(packet, (self.__ESP_IP, self.__TX_PORT))
            if self.t_mode == 2:
                time.sleep(0.2)
            else:
                time.sleep(1 / self.__tx_rate)
