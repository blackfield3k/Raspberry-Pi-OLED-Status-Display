import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C
import psutil
import subprocess
import socket
from gpiozero import Button

# ==========================================
# KONFIGURATION
# ==========================================

# --- Modus ---
USE_BUTTON = True    # True = An auf Knopfdruck | False = Immer an
BUTTON_PIN = 21      # Pin 40
TIMEOUT_SEC = 600    # 10 Minuten

# --- Was soll angezeigt werden? ---
# Das Skript passt die Schriftgröße automatisch an die Anzahl an!
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

# 1. Hardware Init
i2c = busio.I2C(board.SCL, board.SDA)
disp = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDR)

if USE_BUTTON:
    button = Button(BUTTON_PIN)
else:
    button = None

# 2. Automatische Schriftgrößen-Berechnung
# Wir zählen, wie viele Zeilen auf True stehen
active_items = [SHOW_HOSTNAME, SHOW_IP, SHOW_CPU, SHOW_RAM, SHOW_DISK]
line_count = sum(active_items) # Zählt alle 'True' zusammen

# Schriftgröße und Zeilenhöhe basierend auf Anzahl wählen
if line_count == 1:
    FONT_SIZE = 22
    LINE_HEIGHT = 32
    Y_OFFSET = 2  # Etwas korrektur für vertikale Zentrierung
elif line_count == 2:
    FONT_SIZE = 14
    LINE_HEIGHT = 16
    Y_OFFSET = -1
elif line_count == 3:
    FONT_SIZE = 10
    LINE_HEIGHT = 11
    Y_OFFSET = -1
else:
    # 4 oder mehr Zeilen (Fallback)
    FONT_SIZE = 8
    LINE_HEIGHT = 8
    Y_OFFSET = -2

# Schriftart laden mit berechneter Größe
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONT_SIZE)
except IOError:
    # Fallback, falls Schriftart fehlt (sieht dann aber fix aus)
    font = ImageFont.load_default()

# Grafik Puffer
image = Image.new("1", (disp.width, disp.height))
draw = ImageDraw.Draw(image)

# Variablen
last_press_time = time.time()
display_is_active = True 

# Start clean
disp.fill(0)
disp.show()

while True:
    
    # --- Button / Timeout Logik ---
    if USE_BUTTON:
        if button.is_pressed:
            last_press_time = time.time()
            display_is_active = True
        
        if display_is_active and (time.time() - last_press_time > TIMEOUT_SEC):
            display_is_active = False
            disp.fill(0)
            disp.show()
            
        if not display_is_active:
            time.sleep(0.1)
            continue
    else:
        display_is_active = True

    # ================================================
    # ZEICHNEN
    # ================================================
    
    # Schwarz füllen
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    # Startposition setzen (Dynamisch berechnet)
    x = 0
    y = Y_OFFSET 

    # --- HOSTNAME ---
    if SHOW_HOSTNAME:
        try:
            host = socket.gethostname()
            # Falls Hostname zu lang für große Schrift, abschneiden
            if line_count <= 2 and len(host) > 10: 
                host = host[:9] + ".."
            draw.text((x, y), f"{host}", font=font, fill=255)
        except:
            draw.text((x, y), "Host: -", font=font, fill=255)
        y += LINE_HEIGHT

    # --- IP ADRESSE ---
    if SHOW_IP:
        try:
            cmd = "hostname -I | cut -d' ' -f1"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
            # Bei großer Schrift das "IP:" weglassen, Platz sparen
            prefix = "IP: " if line_count > 2 else ""
            draw.text((x, y), f"{prefix}{IP}", font=font, fill=255)
        except:
            draw.text((x, y), "-", font=font, fill=255)
        y += LINE_HEIGHT

    # --- CPU ---
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
                draw.text((x, y), "LOW VOLT!", font=font, fill=255)
            else:
                # Formatierung je nach Platz
                if line_count <= 2:
                    draw.text((x, y), f"CPU:{cpu_load}% {temp}C", font=font, fill=255)
                else:
                    draw.text((x, y), f"CPU: {cpu_load}%  {temp}°C", font=font, fill=255)
        except:
            draw.text((x, y), f"CPU: {cpu_load}%", font=font, fill=255)
        y += LINE_HEIGHT

    # --- RAM ---
    if SHOW_RAM:
        mem = psutil.virtual_memory()
        used_mb = int(mem.used / 1024 / 1024)
        total_mb = int(mem.total / 1024 / 1024)
        
        prefix = "RAM: " if line_count > 2 else "M: "
        draw.text((x, y), f"{prefix}{used_mb}/{total_mb}MB", font=font, fill=255)
        y += LINE_HEIGHT

    # --- DISK ---
    if SHOW_DISK:
        disk = psutil.disk_usage('/')
        used_gb = round(disk.used / 1024 / 1024 / 1024, 1)
        total_gb = round(disk.total / 1024 / 1024 / 1024, 1)
        
        prefix = "SD: " if line_count > 2 else "D: "
        draw.text((x, y), f"{prefix}{used_gb}/{total_gb}GB", font=font, fill=255)
        y += LINE_HEIGHT

    disp.image(image)
    disp.show()
    
    time.sleep(2)