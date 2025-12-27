#!/bin/bash

# Farben für schöne Ausgabe
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Start OLED Stats Installation ===${NC}"

# 1. System-Updates & Abhängigkeiten
echo -e "${GREEN}[1/5] Installiere System-Pakete...${NC}"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-pil libopenjp2-7

# 2. Virtuelle Umgebung erstellen
echo -e "${GREEN}[2/5] Erstelle virtuelle Umgebung (venv)...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Python Module installieren
echo -e "${GREEN}[3/5] Installiere Python-Bibliotheken...${NC}"
./venv/bin/pip3 install --upgrade pip
./venv/bin/pip3 install -r requirements.txt

# 4. Service konfigurieren
echo -e "${GREEN}[4/5] Richte Autostart Service ein...${NC}"

# Aktuellen Pfad und User ermitteln
CURRENT_DIR=$(pwd)
CURRENT_USER=$USER

# Service-Datei anpassen (Platzhalter ersetzen) und kopieren
sudo cp oled_stats.service /etc/systemd/system/oled_stats.service
sudo sed -i "s|%USER%|$CURRENT_USER|g" /etc/systemd/system/oled_stats.service
sudo sed -i "s|%WORKDIR%|$CURRENT_DIR|g" /etc/systemd/system/oled_stats.service

# 5. Service aktivieren
echo -e "${GREEN}[5/5] Starte Service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable oled_stats.service
sudo systemctl restart oled_stats.service

echo -e "${GREEN}=== Installation FERTIG! ===${NC}"
echo "Das Display sollte jetzt laufen."