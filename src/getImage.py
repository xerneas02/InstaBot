import streetview
import bestImage
import matplotlib.pyplot as plt
import random
import geopy
from geopy.geocoders import Nominatim
import numpy as np
import cv2
from matplotlib import pyplot as plt
import sys
from PIL import Image, ImageFont, ImageDraw
import os
import glob
import tiny_planet as tiny
import meteo
from options import WHEATHER

GoogleKey = os.getenv("GOOGLE_KEY")


def start(debug):
    debug.write("\nGetImage :\n\n")
    good = True
    key = GoogleKey
    dirc = "Image"
    os.makedirs(dirc, exist_ok=True)

    while good:
        debug.write("Debut de boucle :\n")
        # Choix aléatoire de coordonnées
        lat = random.randint(-9000000, 9000000) / 100000
        lon = random.randint(-18000000, 18000000) / 100000
        debug.write(f"Coordonnées de départ : {lat}, {lon}\n")
        loc = []

        # Récupère le panoid le plus proche
        panoids, lat, lon = streetview.panoids(lat=lat, lon=lon)
        debug.write(f"Coordonnées ajustées : {lat}, {lon}\n")
        panoid = panoids[0]['panoid']

        # Reverse geocoding
        locator = Nominatim(user_agent="myGeocoder")
        location = locator.reverse(f"{lat}, {lon}", exactly_one=True)
        address = location.raw.get('address', {})
        country = address.get('country', '')
        city    = address.get('city', '')
        state   = address.get('state', '')
        debug.write(f"Localisation trouvée : {country}, {state}, {city}\n")

        # Météo avec le module meteo.py
        if WHEATHER:
            temperature, weather_desc = meteo.get_temp_and_weather(lat, lon)
            debug.write(f"Météo : {weather_desc}, {temperature}°C\n")
            # Prépare l'image météo
            meteo_image = Image.open("assets/images/sky.jpg")
            draw = ImageDraw.Draw(meteo_image)
            # Texte météo et température
            text_temp = f"{temperature:.1f}°C"
            text_desc = weather_desc
            # Ajuste la taille de police si besoin
            font_size = 40
            # On essaie d'utiliser Arial, sinon on revient à une police par défaut
            try:
                font = ImageFont.truetype('arial.ttf', font_size)
            except OSError:
                font = ImageFont.load_default()
                        # Positionner à votre convenance
            draw.text((15, 15), text_desc, fill=(15,15,15), font=font)
            draw.text((15, 15+font_size+5), text_temp, fill=(15,15,15), font=font)
            meteo_image.save(os.path.join(dirc, "meteo.jpg"))
            debug.write("Image météo créée !\n")

        # Téléchargement des vues plates 4 directions
        flat_imgs = []
        for heading in [0, 90, 180, 270]:
            fname = f"{panoid}_{heading}"
            streetview.api_download(
                panoid=panoid,
                heading=heading,
                flat_dir=dirc,
                key=key,
                width=1080,
                height=1080,
                fov=90,
                fname=fname
            )
            flat_imgs.append(Image.open(f"{dirc}/{fname}.jpg"))

        # Assembler horizontalement
        widths, heights = zip(*(img.size for img in flat_imgs))
        pano_w = sum(widths)
        pano_h = max(heights)
        panorama = Image.new('RGB', (pano_w, pano_h))
        x_off = 0
        for img in flat_imgs:
            panorama.paste(img, (x_off, 0))
            x_off += img.width
        panorama_np = np.array(panorama)

        # Warp en tiny planet
        tiny.input_shape = panorama_np.shape
        final = tiny.warp(panorama_np, tiny.little_planet_3, output_shape=tiny.output_shape)

        # Sauvegarde des deux versions
        out1 = Image.fromarray((final*255).round().astype(np.uint8))
        out1.save(os.path.join(dirc, "Panorama.jpg"))
        debug.write("Image panorama créée.\n")

        # version inversée
        inv = np.rot90(panorama, 2)
        tiny.input_shape = inv.shape
        final2 = tiny.warp(inv, tiny.little_planet_3, output_shape=tiny.output_shape)
        out2 = Image.fromarray((final2*255).round().astype(np.uint8))
        out2.save(os.path.join(dirc, "PanoramaRevers.jpg"))
        debug.write("Image panorama inverse créée.\n")

        # Sélection de la meilleure image
        path = streetview.tiles_info(panoid)[0][2][:-7]
        debug.write(f"Nom de base pour bestImage : {path}\n")
        retour = bestImage.main(path)
        if retour != "Error":
            best = path + retour
            debug.write(f"Image choisie : {best}\n")
            img = Image.open("Image/"+best)
            cropped = img.crop((11, 0, 629, 618))
            cropped.save(os.path.join(dirc, "imageToPost.jpg"))
            debug.write("ImageToPost créée. getImage fini !\n\n")
            return round(lat, 5), round(lon, 5), [country, state, city], debug
