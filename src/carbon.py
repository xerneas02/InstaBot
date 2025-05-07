from io import BytesIO
import urllib.request
import matplotlib.pyplot as plt
from PIL import Image, ImageFont, ImageDraw
import os
from options import PUBLISH
from instagrapi import Client

login    = os.getenv("LOGIN_INSTAGRAM")
password = os.getenv("PASSWORD_INSTAGRAM")


# --- 1) Récupère les données CO₂ ---
print("Récupération des données CO₂...")
url = "https://www.esrl.noaa.gov/gmd/webdata/ccgg/trends/co2/co2_weekly_mlo.txt"
urllib.request.urlretrieve(url, "co2.txt")
print("Données récupérées !")

with open("co2.txt") as f:
    lines = f.read().splitlines()

last = lines[-1].split()
prev = lines[-2].split()
v_now, v_prev = float(last[4]), float(prev[4])
v_1yr, v_10yr   = float(last[6]), float(last[7])

# Construire le texte descriptif
texte = (
    "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    "Le taux de CO2 dans l'atmosphère :\n\n\n\n\n\n\n\n\n"
    f"La semaine dernière  : {v_now:.2f} ppm\n\n\n\n\n\n"
    f"Il y a deux semaines  : {v_prev:.2f} ppm\n\n\n\n\n\n"
    f"Il y a 1 an                   : {v_1yr:.2f} ppm\n\n\n\n\n\n"
    f"Il y a 10 ans               : {v_10yr:.2f} ppm\n\n\n\n\n\n\n\n\n"
    "ppm = partie par million\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
)
print(texte)
# --- 2) Génère un bar chart dans un buffer (toutes légendes en blanc) ---
labels = ["1 sem.", "2 sem.", "1 an", "10 ans"]
values = [v_now, v_prev, v_1yr, v_10yr]
fig, ax = plt.subplots(figsize=(4,3), dpi=100, facecolor='none')
bars = ax.bar(labels, values, color="#FFA500")
for b in bars:
    h = b.get_height()
    ax.text(b.get_x()+b.get_width()/2, h+1, f"{h:.1f}",
            ha='center', va='bottom', color='white')
ax.set_title("CO₂ (ppm)", color='white')
ax.tick_params(colors='white')
ax.spines['left'].set_color('white')
ax.spines['bottom'].set_color('white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', linestyle='--', alpha=0.4, color='white')
ax.set_ylim(min(values)-5, max(values)+5)

buf = BytesIO()
fig.savefig(buf, format='png', transparent=True, bbox_inches='tight')
plt.close(fig)
buf.seek(0)

# --- 3) Compose sur le fond ---
bg = Image.open("assets/images/carbonBG.jpg").convert("RGBA")
W, H = bg.size
draw = ImageDraw.Draw(bg)

# Police
try:
    font_title = ImageFont.truetype("assets/fonts/Arial.ttf", 60)
    font_txt   = ImageFont.truetype("assets/fonts/Arial.ttf", 40)
except:
    font_title = ImageFont.load_default()
    font_txt   = ImageFont.load_default()

# 3.1 Titre centré en haut
title = "Évolution du taux de CO2"
bbox = draw.textbbox((0,0), title, font=font_title)
w_t, h_t = bbox[2]-bbox[0], bbox[3]-bbox[1]
draw.text(((W-w_t)/2, 20), title, fill="white", font=font_title)

# 3.2 Texte descriptif juste en dessous
# On prend le bloc 'texte' et on le centralise aussi
# Juste avant d’écrire le bloc de texte :
lines_txt = texte.splitlines()

# 1) Mesure de la 1ʳᵉ ligne
w0 = 634

x0 = (W - w0) / 2
print(f"W = {W}, w0 = {w0}, x0 = {x0}")

# 3) Dessin de chaque ligne en partant de x0
y_cursor = 20 + h_t + 10
for line in lines_txt:
    # Hauteur de la ligne pour l’interligne
    _, h_line = draw.textbbox((0,0), line, font=font_txt)[2:]
    draw.text((x0, y_cursor), line, fill="white", font=font_txt)
    y_cursor += h_line + 5

# 3.3 Coller le graphique après le texte
chart = Image.open(buf).convert("RGBA")
# Choix du filtre de redimensionnement
try:
    resample_filter = Image.Resampling.LANCZOS
except AttributeError:
    resample_filter = getattr(Image, 'LANCZOS', Image.BICUBIC)
new_w = W - 80
new_h = int(new_w * chart.height / chart.width)
chart = chart.resize((new_w, new_h), resample=resample_filter)
bg.paste(chart, ((W-new_w)//2, int(y_cursor+10)), chart)

# --- 4) Enregistre et publie ---
os.makedirs("Image", exist_ok=True)
out = "Image/carbon_story.png"
bg.save(out)
print("Image enregistrée !")

if PUBLISH:
    bot = Client()
    bot.login(login, password)
    bot.photo_upload_to_story(out, caption="Taux de CO₂ 🌍")
    print("Publié en story !")