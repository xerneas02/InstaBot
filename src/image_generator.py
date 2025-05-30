import os
import glob
import random
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from geopy.geocoders import Nominatim

from streetview_downloader import StreetViewDownloader
from image_analyzer import ImageAnalyzer
from tiny_planet_transformer import TinyPlanetTransformer
import meteo
from options import WHEATHER
from custom_logger import CustomLogger

import py360convert


class ImageGenerator:
    def __init__(self, output_dir="Image"):
        self.logger = CustomLogger(__name__)
        self.output_dir = output_dir
        self.google_key = os.getenv("GOOGLE_KEY")
        os.makedirs(self.output_dir, exist_ok=True)

    def get_random_coordinates(self):
        while True :
            lat = random.randint(-9000000, 9000000) / 100000
            lon = random.randint(-18000000, 18000000) / 100000

            #lat, lon = 39.90802, -76.6381

            self.logger.debug(f"Trying coordinates: {lat}, {lon}")

            result = StreetViewDownloader.find_nearest_panorama(lat=lat, lon=lon, API_KEY=self.google_key)
            if result != None:
                pano_id, lat, lon = result
                self.logger.debug(f"Coordinates found: {lat}, {lon}")
                return pano_id, lat, lon

    def reverse_geocode(self, lat, lon):
        """
        Tentative de reverse geocoding sur le point donné, puis sur ses voisins si échec.
        Retourne (country, state, city) ou ('Unknown','Unknown','Unknown') si toutes tentatives échouent.
        """
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut

        locator = Nominatim(user_agent="myGeocoder")
        # Offsets en degrés (~111m latitude) pour tester autour
        offsets = [
            (0, 0),
            (0.001, 0), (-0.001, 0),
            (0, 0.001), (0, -0.001),
            (0.001, 0.001), (0.001, -0.001),
            (-0.001, 0.001), (-0.001, -0.001),
        ]

        for dx, dy in offsets:
            try:
                lat_i = lat + dx
                lon_i = lon + dy
                location = locator.reverse(f"{lat_i}, {lon_i}", exactly_one=True, timeout=10)
                if location and hasattr(location, 'raw'):
                    addr = location.raw.get('address', {})
                    country = addr.get('country', '')
                    # Plusieurs clés possibles pour ville/région
                    city  = addr.get('city')  or addr.get('town')    or ''
                    state = addr.get('state') or addr.get('region')  or ''
                    self.logger.info(f"Location found: {country}, {state}, {city}")
                    return country, state, city
            except GeocoderTimedOut:
                # On réessaie le même offset une fois
                try:
                    location = locator.reverse(f"{lat_i}, {lon_i}", exactly_one=True, timeout=10)
                    if location and hasattr(location, 'raw'):
                        addr = location.raw.get('address', {})
                        country = addr.get('country', '')
                        city  = addr.get('city')  or addr.get('town')   or ''
                        state = addr.get('state') or addr.get('region') or ''
                        self.logger.info(f"Location found (retry): {country}, {state}, {city}")
                        return country, state, city
                except Exception:
                    continue
            except Exception:
                continue

        # Si aucune tentative ne réussit
        self.logger.warning("Location error: all reverse geocode attempts failed.")
        return None

    def get_weather_image(self, lat, lon):
        temperature, weather_desc = meteo.get_temp_and_weather(lat, lon)
        self.logger.debug(f"Météo : {weather_desc}, {temperature}°C")

        meteo_image = Image.open("assets/images/sky.jpg")
        draw = ImageDraw.Draw(meteo_image)

        text_temp = f"{temperature:.1f}°C"
        text_desc = weather_desc
        font_size = 40

        try:
            font = ImageFont.truetype('assets/fonts/American Captain.ttf', font_size)
            self.logger.info("Font loaded")
        except OSError:
            font = ImageFont.load_default()
            self.logger.warning("Fallback font used")

        draw.text((15, 15), text_desc, fill=(15, 15, 15), font=font)
        draw.text((15, 15 + font_size + 5), text_temp, fill=(15, 15, 15), font=font)

        meteo_path = os.path.join(self.output_dir, "meteo.jpg")
        meteo_image.save(meteo_path)
        self.logger.info("Weather image created")

    def download_flat_images(self, panoid):
        faces = {}
        specs = [
            ("front",  0,   0),
            ("right",  90,  0),
            ("back",   180, 0),
            ("left",   270, 0),
            ("up",     0,   90),
            ("down",   0,  -90),
        ]

        for face_name, heading, pitch in specs:
            fname = f"{panoid}_{face_name}"
            StreetViewDownloader.api_download(
                panoid=panoid,
                heading=heading,
                pitch=pitch,
                flat_dir=self.output_dir,
                key=self.google_key,
                width=640,
                height=640,
                fov=90,
                fname=fname
            )
            img = Image.open(f"{self.output_dir}/{fname}.jpg")
            faces[face_name] = img

        return faces

    def stitch_images(self, images):
        widths, heights = zip(*(img.size for img in images))
        pano_w = sum(widths)
        pano_h = max(heights)
        panorama = Image.new('RGB', (pano_w, pano_h))
        x_offset = 0
        for img in images:
            panorama.paste(img, (x_offset, 0))
            x_offset += img.width
        return panorama

    def create_panorama(self, panoid):
        faces = {
            'F': np.array(Image.open(f'Image/{panoid}_front.jpg')),
            'R': np.array(Image.open(f'Image/{panoid}_right.jpg')),
            'B': np.array(Image.open(f'Image/{panoid}_back.jpg')),
            'L': np.array(Image.open(f'Image/{panoid}_left.jpg')),
            'U': np.array(Image.open(f'Image/{panoid}_up.jpg')),
            'D': np.array(Image.open(f'Image/{panoid}_down.jpg')),
        }

        H = faces['F'].shape[0]
        equi = py360convert.c2e(faces, h=H, w=2*H, mode='bilinear', cube_format='dict')
        equi_img = Image.fromarray(equi)
        return np.array(equi_img)

    def create_panorama_versions(self, panoid):
        #panorama_np = np.array(panorama)
        panorama_np = self.create_panorama(panoid)
        tiny = TinyPlanetTransformer(input_shape=panorama_np.shape, output_shape=(1080, 1080))
        
        result = tiny.warp(panorama_np, tiny.little_planet_map, output_shape=tiny.output_shape)
        out_img = Image.fromarray((result * 255).round().astype(np.uint8))
        out_img.save(os.path.join(self.output_dir, "Panorama.jpg"))
        self.logger.info("Panorama image created")

        inv = np.rot90(panorama_np, 2)
        tiny.input_shape = inv.shape
        result_inv = tiny.warp(inv, tiny.little_planet_map, output_shape=tiny.output_shape)
        out_img_inv = Image.fromarray((result_inv * 255).round().astype(np.uint8))
        out_img_inv.save(os.path.join(self.output_dir, "PanoramaRevers.jpg"))
        self.logger.info("Inverted panorama image created")

    def create_best_image(self, panoid):
        path = StreetViewDownloader.tiles_info(panoid)[0][2][:-7]
        self.logger.debug(f"Base path for best image: {path}")
        imageAnalyzer = ImageAnalyzer()
        retour = imageAnalyzer.analyze(path)

        if retour == "Error":
            self.logger.warning("No best image found.")
            return None

        best = path + retour
        img = Image.open(f"{self.output_dir}/{best}")
        cropped = img.crop((11, 0, 629, 618))
        cropped.save(os.path.join(self.output_dir, "imageToPost.jpg"))
        self.logger.info("Image to post created")
        return best, path

    def start(self):
        self.logger.info("Start image generation loop")

        while True:
            try:
                panoid, lat, lon = self.get_random_coordinates()
                self.logger.debug(f"Random coordinates: {lat}, {lon}")

                self.logger.debug(f"Using panoid: {panoid}")
                result = self.reverse_geocode(lat, lon)

                if result is None:
                    continue
                
                country, state, city = result

                if WHEATHER:
                    self.get_weather_image(lat, lon)

                images = self.download_flat_images(panoid)
                #panorama = self.stitch_images(images)
                self.create_panorama_versions(panoid)
                
                #best_img = self.create_best_image(panoid)

                path = panoid + "_"

                self.logger.debug("Image generation complete")
                return round(lat, 5), round(lon, 5), [country, state, city], path

            except Exception as e:
                self.logger.error(f"Exception in image generation: {e}")
                continue
