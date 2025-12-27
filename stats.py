import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_ssd1306 import SSD1306_I2C
import psutil
import subprocess

# ==========================================
# KONFIGURATION: Was soll angezeigt werden?
# Setze Werte auf True (An) oder False (Aus)
# ==========================================
SHOW_IP = True
SHOW_CPU = True      # CPU Last + Temperatur
SHOW_RAM = True
SHOW_DISK = True

# Display Einstellungen
WIDTH = 128
HEIGHT = 32          # WICHTIG: 32 für dein schmales Display
I2C_ADDR = 0x3c      # Standard I2C Adresse

# ==========================================

# I2C und Display initialisieren
i2c = busio.I2C(board.SCL, board.SDA)
# Reset-Pin weggelassen, da du GPIO4 anders nutzt
disp = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDR)

# Display leeren
disp.fill(0)
disp.show()

# Bildpuffer erstellen
image = Image.new("1", (disp.width, disp.height))
draw = ImageDraw.Draw(image)

# Schriftart laden
# Wir versuchen eine hübsche Schriftart, sonst Standard
try:
    # Standard bei Raspberry Pi OS Lite
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
except IOError:
    font = ImageFont.load_default()

while True:
    # 1. Bild schwarz übermalen (Reset)
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    # 2. Position zurücksetzen
    x = 0
    y = -2    # Kleiner Offset nach oben, damit es auf 32px passt
    line_height = 8 # Zeilenhöhe für 4 Zeilen auf 32px

    # ---------------------------------------
    # DATEN ABFRAGEN UND ZEICHNEN
    # ---------------------------------------
    
    # --- IP ADRESSE ---
    if SHOW_IP:
        try:
            # Holt die IP (zuverlässiger als Python socket auf dem Pi)
            cmd = "hostname -I | cut -d' ' -f1"
            IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
            draw.text((x, y), f"IP: {IP}", font=font, fill=255)
        except:
            draw.text((x, y), "IP: -", font=font, fill=255)
        y += line_height

    # --- CPU LAST & TEMP ---
    if SHOW_CPU:
        cpu_load = psutil.cpu_percent()
        # Temperatur auslesen
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read()) / 1000, 1)
        except:
            temp = "0"
            
        draw.text((x, y), f"CPU: {cpu_load}%  {temp}°C", font=font, fill=255)
        y += line_height

    # --- RAM ---
    if SHOW_RAM:
        mem = psutil.virtual_memory()
        # Umrechnung in MB
        used_mb = int(mem.used / 1024 / 1024)
        total_mb = int(mem.total / 1024 / 1024)
        draw.text((x, y), f"RAM: {used_mb}/{total_mb}MB", font=font, fill=255)
        y += line_height

    # --- DISK USAGE ---
    if SHOW_DISK:
        disk = psutil.disk_usage('/')
        # Umrechnung in GB
        used_gb = round(disk.used / 1024 / 1024 / 1024, 1)
        total_gb = round(disk.total / 1024 / 1024 / 1024, 1)
        draw.text((x, y), f"SD:  {used_gb}/{total_gb}GB ({disk.percent}%)", font=font, fill=255)
        y += line_height

    # 3. Bild anzeigen
    disp.image(image)
    disp.show()
    
    # 4. Kurz warten (Update Intervall)
    time.sleep(2)