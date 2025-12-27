import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C
import psutil
import subprocess
import socket
# Wir importieren Button, nutzen ihn aber nur, wenn konfiguriert
from gpiozero import Button

# ==========================================
# KONFIGURATION
# ==========================================

# --- Modus wählen ---
USE_BUTTON = True    # True = Display geht nur auf Knopfdruck an
                     # False = Display ist IMMER an (Dauerbetrieb)

# Button Einstellungen (nur relevant, wenn USE_BUTTON = True)
BUTTON_PIN = 21      # Pin 40 (GND ist Pin 39)
TIMEOUT_SEC = 600    # Wie lange bleibt es an? (Sekunden)

# Was soll angezeigt werden?
# (Achte darauf, maximal 4 Zeilen auf True zu setzen bei 128x32)
SHOW_HOSTNAME = True
SHOW_IP = True
SHOW_CPU = True
SHOW_RAM = True
SHOW_DISK = False

# Display Einstellungen
WIDTH = 128
HEIGHT = 32
I2C_ADDR = 0x3c

# ==========================================

# I2C und Display initialisieren
i2c = busio.I2C(board.SCL, board.SDA)
disp = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDR)

# Button nur initialisieren, wenn wir ihn brauchen
if USE_BUTTON:
    button = Button(BUTTON_PIN)
else:
    button = None

# Grafik Vorbereitung
image = Image.new("1", (disp.width, disp.height))
draw = ImageDraw.Draw(image)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
except IOError:
    font = ImageFont.load_default()

# Variablen
last_press_time = time.time()
display_is_active = True # Standardwert beim Start

# Init Screen clear
disp.fill(0)
disp.show()

while True:
    
    # ------------------------------------------------
    # LOGIK: AN ODER AUS?
    # ------------------------------------------------
    
    if USE_BUTTON:
        # Modus: Nur auf Knopfdruck
        
        # Wurde gedrückt?
        if button.is_pressed:
            last_press_time = time.time()
            display_is_active = True
        
        # Ist Zeit abgelaufen?
        if display_is_active and (time.time() - last_press_time > TIMEOUT_SEC):
            display_is_active = False
            disp.fill(0)
            disp.show()
            
        # Wenn inaktiv -> Schlafen legen und Loop neu starten
        if not display_is_active:
            time.sleep(0.1)
            continue
            
    else:
        # Modus: Immer an
        display_is_active = True

    # ================================================
    # ZEICHNEN (Nur wenn aktiv)
    # ================================================
    
    # Schwarz füllen
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    x = 0
    y = -2
    line_height = 8

    # --- HOSTNAME ---
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

    # --- CPU & POWER ---
    if SHOW_CPU:
        cpu_load = psutil.cpu_percent()
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read()) / 1000, 1)
        except:
            temp = 0

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

    # --- DISK ---
    if SHOW_DISK:
        disk = psutil.disk_usage('/')
        used_gb = round(disk.used / 1024 / 1024 / 1024, 1)
        total_gb = round(disk.total / 1024 / 1024 / 1024, 1)
        draw.text((x, y), f"SD:  {used_gb}/{total_gb}GB", font=font, fill=255)
        y += line_height

    disp.image(image)
    disp.show()
    
    time.sleep(2)