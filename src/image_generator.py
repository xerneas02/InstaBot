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


class ImageGenerator:
    def __init__(self, output_dir="Image"):
        self.logger = CustomLogger(__name__)
        self.output_dir = output_dir
        self.google_key = os.getenv("GOOGLE_KEY")
        print(self.google_key)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_random_coordinates(self):
<<<<<<< HEAD
        while True :
            lat = random.randint(-9000000, 9000000) / 100000
            lon = random.randint(-18000000, 18000000) / 100000
            self.logger.debug(f"Trying coordinates: {lat}, {lon}")

            result = StreetViewDownloader.find_nearest_panorama(lat=lat, lon=lon, API_KEY=self.google_key)
            if result != None:
                _, lat, lon = result
                self.logger.debug(f"Coordinates found: {lat}, {lon}")
                return lat, lon
=======
        lat = random.randint(-9000000, 9000000) / 100000
        lon = random.randint(-18000000, 18000000) / 100000
        return lat, lon
>>>>>>> logging

    def reverse_geocode(self, lat, lon):
        locator = Nominatim(user_agent="myGeocoder")
        location = locator.reverse(f"{lat}, {lon}", exactly_one=True)
        address = location.raw.get('address', {})
<<<<<<< HEAD

        try:
            locator = Nominatim(user_agent="myGeocoder")
            location = locator.reverse(f"{lat}, {lon}", exactly_one=True)
            address = location.raw.get('address', {})
            country = address.get('country', '')
            city    = address.get('city', '')
            state   = address.get('state', '')
            debug.write(f"Localisation trouvée : {country}, {state}, {city}\n")
            self.logger.info(f"Location found: {country}, {state}, {city}")
            return country, state, city
        except:
            country = "Unkown"
            city    = "Unkown"
            state   = "Unkown"
            self.logger.warning("Location error, coordinates unknown.")
            return "Unkown", "Unkown", "Unkown"
=======
        return address.get('country', ''), address.get('state', ''), address.get('city', '')
>>>>>>> logging

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
        images = []
        for heading in [0, 90, 180, 270]:
            fname = f"{panoid}_{heading}"
            StreetViewDownloader.api_download(
                panoid=panoid,
                heading=heading,
                flat_dir=self.output_dir,
                key=self.google_key,
                width=1080,
                height=1080,
                fov=90,
                fname=fname
            )
            images.append(Image.open(f"{self.output_dir}/{fname}.jpg"))
        return images

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

    def create_panorama_versions(self, panorama):
        panorama_np = np.array(panorama)
        tiny = TinyPlanetTransformer(input_shape=panorama_np.shape, output_shape=(1080, 1080))
        
        result = tiny.warp(panorama_np, tiny.little_planet_map, output_shape=tiny.output_shape)
        out_img = Image.fromarray((result * 255).round().astype(np.uint8))
        out_img.save(os.path.join(self.output_dir, "Panorama.jpg"))
        self.logger.info("Panorama image created")

        inv = np.rot90(panorama, 2)
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
        return best

    def start(self):
        self.logger.info("Start image generation loop")

        while True:
            try:
                lat, lon = self.get_random_coordinates()
                self.logger.debug(f"Random coordinates: {lat}, {lon}")

                panoids, lat, lon = StreetViewDownloader.panoids(lat=lat, lon=lon)
                if not panoids:
                    self.logger.warning("No panoids found, retrying...")
                    continue

                panoid = panoids[0]['panoid']
                self.logger.debug(f"Using panoid: {panoid}")
                country, state, city = self.reverse_geocode(lat, lon)

                if WHEATHER:
                    self.get_weather_image(lat, lon)

                images = self.download_flat_images(panoid)
                panorama = self.stitch_images(images)
                self.create_panorama_versions(panorama)
                best_img = self.create_best_image(panoid)

                if best_img:
                    self.logger.debug("Image generation complete")
                    return round(lat, 5), round(lon, 5), [country, state, city], path

            except Exception as e:
                self.logger.error(f"Exception in image generation: {e}")
                continue
