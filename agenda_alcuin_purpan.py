import os
import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime

# --- Identifiants depuis les secrets GitHub ---
USERNAME = os.getenv("ALCUIN_USERNAME")
PASSWORD = os.getenv("ALCUIN_PASSWORD")

LOGIN_URL = "https://purpan.alcuin.com/OpDotNet/Noyau/Login.aspx"
PLANNING_URL = "https://purpan.alcuin.com/OpDotNet/Noyau/Default.aspx"

# --- Session HTTP ---
session = requests.Session()
payload = {
    "login": USERNAME,
    "password": PASSWORD
}
session.post(LOGIN_URL, data=payload)

# --- Charger la page de planning ---
resp = session.get(PLANNING_URL)
soup = BeautifulSoup(resp.text, "html.parser")

cal = Calendar()

# --- Trouver tous les blocs de détails de cours ---
details = soup.find_all("div", id="DivDet")

for det in details:
    # Titre
    titre_tag = det.find("td", class_="AuthentificationMenu")
    titre = titre_tag.get_text(strip=True) if titre_tag else "Cours"

    # Date
    date_tag = det.find("td", string=lambda x: x and "Date" in x)
    if not date_tag:
        continue
    date_val = date_tag.find_next("td").get_text(strip=True)
    try:
        date = datetime.strptime(date_val, "%d/%m/%Y").date()
    except:
        continue

    # Heures
    heures = det.find_all("td", class_="GEDcellsouscategorie", align="center")
    start_time, end_time = None, None
    for h in heures:
        txt = h.get_text(strip=True)
        if txt.startswith("Début"):
            start_time = txt.split(":")[-1].strip()
        if txt.startswith("Fin"):
            end_time = txt.split(":")[-1].strip()

    if not start_time or not end_time:
        continue

    try:
        start = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    except:
        continue

    # Salle
    salle_tag = det.find("a", onclick=lambda x: x and "VisRes" in x)
    salle = salle_tag.get_text(strip=True) if salle_tag else None

    # Créer l’événement
    event = Event()
    event.name = titre
    event.begin = start
    event.end = end
    if salle:
        event.location = salle

    cal.events.add(event)

# --- Sauvegarde du fichier ICS ---
with open("alcuin_planning.ics", "w", encoding="utf-8") as f:
    f.writelines(cal)

print("✅ Fichier alcuin_planning.ics généré")
