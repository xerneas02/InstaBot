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
import pyowm
from pyowm.utils import timestamps, formatting

OpenWMapKey = os.getenv("OPENW_MAP_KEY")
GoogleKey = os.getenv("GOOGLE_KEY")

def start(debug):
    debug.write("\nGetImage :\n\n")
    good = True
    #OpenWMap = pyowm.OWM(OpenWMapKey)
    key = GoogleKey
    dirc = "Image"
    while good:
        debug.write("Debut de boucle :\n")
        lat = random.randint(-9000000,9000000)/100000
        lon = random.randint(-18000000,18000000)/100000
        debug.write("Coordonnées de départ : {}, {}\n".format(lat, lon))
        loc = []
        panoids, lat, lon = streetview.panoids(lat=lat, lon=lon)
        #panoids, lat, lon = streetview.panoids(lat=-5.89923, lon=-76.10207) 
        debug.write("Coordonnées : {}, {}\n".format(lat, lon))  
        panoid = panoids[0]['panoid']
        locator = Nominatim(user_agent="myGeocoder")

        location = locator.reverse("{}, {}".format(lat, lon), exactly_one=True)
        address = location.raw['address']
        country = address.get('country', '')
        city = address.get('city', '')
        state = address.get('state', '')
        debug.write("Localisation trouvé : {}, {}, {}\n".format(country, state, city))
        ## Meteo
        """
        fontSize = 40
        mgr = OpenWMap.weather_manager()
        today = formatting.to_UNIXtime(timestamps.datetime.today())
        one_call = mgr.one_call(lat=lat, lon=lon, dt=today)
        temperature = one_call.current.temperature('celsius').get('temp', None)
        data = str(one_call.current).split(",")[2]
        data = data[17:len(data)-1]
        meteoImage = Image.open("src/sky.jpg")
        metoImageEdit = ImageDraw.Draw(meteoImage)
        debug.write("Meteo : {}, {}°\n".format(data, temperature))
        currentWeather = "Current weather at " + country

        """
        loc.append(country)

        
        if len(state) > 0:
            currentWeather = "Current weather at " + state
            loc.append(state)

        if len(city) > 0: 
            currentWeather = "Current weather at " + city
            loc.append(city)
        
        """
        while (320 - (len(currentWeather)*((fontSize-2)/2)/2)) < 10:
            fontSize -= 1 
        debug.write("Taille de police : {}\n".format(fontSize))
        
        font = ImageFont.truetype('arial.ttf', fontSize)
        metoImageEdit.text((15, 15), data, (15, 15, 15), font=font)
        metoImageEdit.text((550-fontSize, 550), (str(temperature) + "°"), (15, 15, 15), font=font)
        metoImageEdit.text((abs(320 - (len(currentWeather)*((fontSize-2)/2)/2)), 320 - fontSize), (currentWeather), (15, 15, 15), font=font)
        print(320 - (len(currentWeather)*((fontSize)/2)/2), 320 - fontSize)
        meteoImage.save("Image/meteo.jpg")
        print(country, " : ", data, " ", str(temperature) , "°")
        debug.write("Image meteo créé!\n")
        """

        #streetview.download_flats(panoid, key=key, flat_dir=dirc, fov=90, width=1080, height=1090)
        #panorama = streetview.download_panorama_v3(panoid, zoom=3, disp=False)

        #tiny.input_shape = panorama.shape
        #final_image = tiny.warp(panorama, tiny.little_planet_3, output_shape=tiny.output_shape)

        flat_imgs = []
        headings = [0, 90, 180, 270]
        for heading in headings:
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
        total_width = sum(widths)
        max_height = max(heights)
        panorama = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for img in flat_imgs:
            panorama.paste(img, (x_offset, 0))
            x_offset += img.width
        panorama_np = np.array(panorama)

        tiny.input_shape = panorama_np.shape
        final_image = tiny.warp(panorama_np, tiny.little_planet_3, output_shape=tiny.output_shape)


        
    #    currentDT = datetime.datetime.now()
    #    file_name = f"imgs/{currentDT.day}D{currentDT.month}M{currentDT.year}Y_{currentDT.hour}h{currentDT.minute}m{currentDT.second}s.jpg"
        file_name = "Image/Panorama.jpg"
        debug.write("Image panorama créé.\n")

        final_image = Image.fromarray((final_image * 255).round().astype(np.uint8), 'RGB')
        final_image.save(file_name)

        panorama = np.rot90(panorama, 2)
        final_image = tiny.warp(panorama, tiny.little_planet_3, output_shape=tiny.output_shape)
    #    currentDT = datetime.datetime.now()
    #    file_name = f"imgs/{currentDT.day}D{currentDT.month}M{currentDT.year}Y_{currentDT.hour}h{currentDT.minute}m{currentDT.second}s.jpg"
        file_name = "Image/PanoramaRevers.jpg"

        final_image = Image.fromarray((final_image * 255).round().astype(np.uint8), 'RGB')
        final_image.save(file_name)
        debug.write("Image panorama inverse créé.\n")

        path = streetview.tiles_info(panoid)[0][2]
        path = path[:len(path)-7]
        debug.write("nom Image : {}\n".format(path))
        retour = bestImage.main(path)
        if path != "Error":
            path += retour
            debug.write("Image choisie : {}\n".format(path))
            good=False
            path = "Image/" + path

            img = Image.open(path)
            area = (11, 0, 629, 618)
            cropped_img = img.crop(area)
            cropped_img.save("Image/imageToPost.jpg")
            debug.write("choisie.\ngetImage fini!\n\n")
            return int(lat*100000)/100000, int(lon*100000)/100000, loc, debug