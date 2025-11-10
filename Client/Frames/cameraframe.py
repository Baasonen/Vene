import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk #Videokäsittelyyn
import cv2  #Videokäsittelyyn
import concurrent.futures
import os
import io

class CameraFrame(ttk.Frame):
    def __init__(self, container, boat):
        super().__init__(container, style="Custom.TFrame")
        self.container = container
        self.boat = boat

        no_connection_image_path = os.path.join(self.container.mapframe.script_directory, "sus.png")
        self.no_connection_image = tk.PhotoImage(file=no_connection_image_path).subsample(2)
        self.img_label =ttk.Label(self, style="Custom.TLabel", image=self.no_connection_image)
        self.img_label.pack()
        

        self.camera_url = "http://192.168.4.2/capture"

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.update_scheduled = False
        self.schedule_update()
    
    def schedule_update(self):
        if not self.update_scheduled:
            self.update_scheduled = True    
            self.got_frame
        self.after(50, self.schedule_update)

    def got_frame(self):
        self.update_scheduled = False
        frame = self.boat.get_frame()   #kuva update_framesta
        if frame is not None:
            width = self.winfo_width()
            height = self.winfo_height()
            a = Image.open(io.BytesIO(frame))
            img = ImageTk.PhotoImage(a.resize((width, height), Image.LANCZOS))
            self.img_label.config(image=img)
            self.img_label.image = img
        else:
            self.img_label.config(image=self.no_connection_image)
            self.img_label.image = self.no_connection_image
