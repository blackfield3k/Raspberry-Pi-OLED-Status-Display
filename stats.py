import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C
import psutil
import subprocess
from gpiozero import Button
import socket  # <--- NEU: Für den Hostnamen

# ==========================================
# KONFIGURATION
# ==========================================
# Button Einstellungen
BUTTON_PIN = 21      # Pin 40 (GND ist Pin 39 daneben)
TIMEOUT_SEC = 600    # 10 Minuten an bleiben

# Was soll angezeigt werden? 
# ACHTUNG: Auf 128x32 passen maximal 4 Zeilen gleichzeitig!
SHOW_HOSTNAME = True # <--- NEU
SHOW_IP = True
SHOW_CPU = True      # CPU Last + Temp + LowVolt Warnung
SHOW_RAM = True
SHOW_DISK = False    # Habe ich mal auf False gesetzt, damit Platz für Hostname ist

# Display Einstellungen
WIDTH = 128
HEIGHT = 32
I2C_ADDR = 0x3c

# ==========================================

# Hardware init
i2c = busio.I2C(board.SCL, board.SDA)
disp = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDR)
button = Button(BUTTON_PIN)

# Grafik Vorbereitung
image = Image.new("1", (disp.width, disp.height))
draw = ImageDraw.Draw(image)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
except IOError:
    font = ImageFont.load_default()

# Variablen für Timer
last_press_time = 0
display_is_active = False

# Init Screen clear
disp.fill(0)
disp.show()

while True:
    # Button Logic
    if button.is_pressed:
        last_press_time = time.time()
        display_is_active = True
    
    # Timeout Logic
    if display_is_active and (time.time() - last_press_time > TIMEOUT_SEC):
        display_is_active = False
        disp.fill(0)
        disp.show()

    # Schlafen wenn inaktiv
    if not display_is_active:
        time.sleep(0.1)
        continue

    # ================================================
    # ZEICHNEN
    # ================================================
    
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    x = 0
    y = -2
    line_height = 8

    # --- HOSTNAME (NEU) ---
    if SHOW_HOSTNAME:
        try:
            host = socket.gethostname()
            draw.text((x, y), f"Host: {host}", font=font, fill=255)
        except:
            draw.text((x, y), "Host: -", font=font, fill=255)
        y += line_height

    # --- IP ADRESSE ---
    if SHOW_IP:
        try:
            cmd = "hostname -I | cut -d' ' -f1"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
            draw.text((x, y), f"IP: {IP}", font=font, fill=255)
        except:
            draw.text((x, y), "IP: -", font=font, fill=255)
        y += line_height

    # --- CPU LAST & TEMP & POWER CHECK ---
    if SHOW_CPU:
        cpu_load = psutil.cpu_percent()
        # Temp lesen
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read()) / 1000, 1)
        except:
            temp = "0"

        # Undervoltage Check
        try:
            cmd = "vcgencmd get_throttled | cut -d'=' -f2"
            throttled_hex = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
            if int(throttled_hex, 16) != 0:
                draw.text((x, y), "WARN: LOW VOLT!", font=font, fill=255)
            else:
                draw.text((x, y), f"CPU: {cpu_load}%  {temp}°C", font=font, fill=255)
        except:
            draw.text((x, y), f"CPU: {cpu_load}%  {temp}°C", font=font, fill=255)
            
        y += line_height

    # --- RAM ---
    if SHOW_RAM:
        mem = psutil.virtual_memory()
        used_mb = int(mem.used / 1024 / 1024)
        total_mb = int(mem.total / 1024 / 1024)
        draw.text((x, y), f"RAM: {used_mb}/{total_mb}MB", font=font, fill=255)
        y += line_height

    # --- DISK USAGE ---
    if SHOW_DISK:
        disk = psutil.disk_usage('/')
        used_gb = round(disk.used / 1024 / 1024 / 1024, 1)
        total_gb = round(disk.total / 1024 / 1024 / 1024, 1)
        draw.text((x, y), f"SD:  {used_gb}/{total_gb}GB", font=font, fill=255)
        y += line_height

    disp.image(image)
    disp.show()
    time.sleep(2)