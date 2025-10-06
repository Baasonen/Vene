import socket
import struct 
import concurrent.futures
import time
from threading import Lock  

class Vene:
    _instance = None
    _lock = Lock() #En tiiä

    def __new__(cls, *args, **kwargs):
        with cls._lock: 
            if cls._instance is None:
                cls._instance = super().__new__(cls)  #Joo o
        return cls._instance

    def __init__(self, ip = "192.168.4.1", rx = 4210, tx = 4211):
        if getattr(self, "_initialized", False):  #Aika hieno ja selkee funktio
            return

        self.version = 3.0
        
        self.__ESP_IP = ip
        self.__RX_PORT = rx
        self.__TX_PORT = tx
        self.__tx_rate = 100

        #Pls älä laita näille arvoja, käytä set_control
        self.mode = 0
        self.rudder = 0
        self.throttle = (0, 0)   #thr1, thr2
        self.light_mode = 0

        # Telemetry data, can be accessed as variables
        self.t_mode = 0
        self.t_heading = 0
        self.t_speed = 0        
        self.t_coords = (0, 0)  #lat, lon
        self.t_battery = 0
        self.t_target_wp = 0
        self.t_gps_status = 0
        self.t_gen_errror = 0
        self.t_packets_per_second = 0

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(("", self.__RX_PORT))

        self.__pool = None
        self.__shutdown_flag = True
        self.__t_start = int(time.time())

        print(f"VCom {self.version}")

        self._initialized = True 
    
    def clamp(val, min_val, max_val):
        return max(min_val, min(val, max_val))

    #Esim. set_control(rudder = 80)
    def set_control(self, *, rudder = None, throttle = None, light_mode = None):
        
        if rudder is not None:
            self.rudder = self.clamp(rudder, 0, 180)
        
        if throttle is not None:
            if isinstance(throttle, tuple):
                thr1, thr2 = throttle
            else:
                thr1 = thr2 = throttle
            
            self.throttle = (clamp(thr1, 0, 100), clamp(thr2, 0, 100))

        if light_mode is not None:
            self.light_mode = clamp(light_mode, 0, 255)

    def setModeManual(self):
        self.mode = 1

    def setModeAP(self, wp_list):
        print(wp_list)
        self.mode = 2

    def returnHome(self):
        self.mode = 3

    def modeOverride(self):
        self.mode = 4
                
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

    def set_rate(self, rate_hz: int):
        self.__tx_rate = rate_hz

    def get_rate(self) -> int:
        return self.__tx_rate
    
    def __recieve_loop(self):
        while not self.__shutdown_flag:
            data, _ = self.__sock.recvfrom(1024)
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
                self.t_coords = (latFloat, lonFloat)
                self.t_target_wp = error & 0x7F
                self.t_gps_status = (error >> 7) & 0x03
                self.t_gen_error = error >> 9

            else:
                print(f"Unexpected packet size: {len(data)}")
    
    def __send_loop(self):
        while not self.__shutdown_flag:
            thr1, thr2 = self.throttle
            packet = struct.pack("<6BH", 
                        self.mode,
                        self.rudder,
                        thr1,
                        thr2,
                        self.light_mode,
                        self.__tx_rate,
                        int(time.time() - self.__t_start),
                        )
            
            self.__sock.sendto(packet, (self.__ESP_IP, self.__TX_PORT))
            if self.t_mode == 2:
                time.sleep(1)
            else:
                time.sleep(1 / self.__tx_rate)

