import re
import os
import time
import shutil
import random
import requests
import itertools
import numpy as np
from PIL import Image
from datetime import datetime
from io import BytesIO
import math

from custom_logger import CustomLogger

class StreetViewDownloader:
    # class variables
    logger = CustomLogger(__name__)

    @staticmethod
    def find_nearest_panorama(lat, lon, radius=500000, API_KEY="Your_Api_Key"):
        """
        Renvoie (panoid, pano_lat, pano_lng) du panorama le plus proche,
        ou None si aucun panorama dans le rayon.
        """
        url = "https://maps.googleapis.com/maps/api/streetview/metadata"
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "key": API_KEY
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        print(data)
        if data.get("status") == "OK":
            loc = data["location"]
            return data["pano_id"], loc["lat"], loc["lng"]
        else:
            print(f"Erreur : {data.get('status')}")
            return None

    @staticmethod
    def _panoids_url(lat, lon):
        url = "https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{0:}!4d{1:}!2d50!3m10!2m2!1sen!2sGB!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m10!1e1!1e2!1e3!1e4!1e8!1e6!5m1!1e2!6m1!1e2&callback=_xdc_._v2mub5"
        return url.format(lat, lon)

    @staticmethod
    def _panoids_data(lat, lon, proxies=None):
        url = StreetViewDownloader._panoids_url(lat, lon)
        statuscode = -1
        while statuscode != 200:
            response = None
            try:
                response = requests.get(url, proxies=proxies)
                statuscode = response.status_code
            except (requests.ConnectionError, requests.Timeout) as e:
                statuscode = 0
                StreetViewDownloader.logger.warning(f"Connection issue: {e}")
                time.sleep(1)
        return response

    @staticmethod
    def panoids(lat, lon, closest=False, disp=False, proxies=None):
        trace = ""
        count = 0
        resp = None
        found = False
        original_lat, original_lon = lat, lon

        # 1) Recherche en spirale avec plusieurs rayons croissants
        """
        for max_radius in [0.5, 2.0, 10.0, 50.0, 200.0, 1000.0]:
            for dx, dy in spiral_offsets(step=0.5, max_radius=max_radius):
                count += 1
                qlat, qlon = original_lat + dy, original_lon + dx
                trace += f"({qlat:.6f}, {qlon:.6f})\n"
                print(f"Recherche en spirale : ({qlat:.6f}, {qlon:.6f})")
                resp = _panoids_data(qlat, qlon)
                if resp.text[67] + resp.text[68] != "no":
                    lat, lon = qlat, qlon
                    found = True
                    break
            if found:
                break"""

        # 2) Si toujours rien, fallback sur jitter aléatoire (comme avant) jusqu'à trouver
        while not found:
            count += 1
            # jitter aléatoire
            add = random.randint(-1000000, 1000000) / 10000
            while original_lat + add < -90 or original_lat + add > 90:
                add = random.randint(-1000000, 1000000) / 10000
            qlat = original_lat + add
            add = random.randint(-1000000, 1000000) / 10000
            while original_lon + add < -180 or original_lon + add > 180:
                add = random.randint(-1000000, 1000000) / 10000
            qlon = original_lon + add

            trace += f"({qlat:.6f}, {qlon:.6f})\n"
            resp = StreetViewDownloader._panoids_data(qlat, qlon)
            if resp.text[67] + resp.text[68] != "no":
                lat, lon = qlat, qlon
                found = True
                break
            
        StreetViewDownloader.logger.info(f"Panoids found after {count} attempts")

        # Extraction des panoids + coords (inchangé)
        pans = re.findall(
            r'\[[0-9]+,"(.+?)"\].+?\[\[null,null,'
            r'(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)',
            resp.text
        )
        pans = [
            {"panoid": p[0], "lat": float(p[1]), "lon": float(p[2])}
            for p in pans
        ]
        pans = [p for i, p in enumerate(pans) if p not in pans[:i]]
        if disp:
            for pan in pans:
                print(pan)

        # Extraction et assignation des dates (inchangé)
        dates = re.findall(r'([0-9]?[0-9]?[0-9])?,?\[(20[0-9][0-9]),([0-9]+)\]', resp.text)
        dates = [list(d)[1:] for d in dates]
        if dates:
            dates = [[int(v) for v in d] for d in dates if 1 <= int(d[1]) <= 12]
            year, month = dates.pop(-1)
            pans[0].update({'year': year, 'month': month})
            dates.reverse()
            for i, (y, m) in enumerate(dates):
                pans[-1-i].update({'year': y, 'month': m})

        # Tri chronologique (inchangé)
        def _key(p):
            return datetime(p['year'], p['month'], 1) if 'year' in p else datetime(3000,1,1)
        pans.sort(key=_key)

        # Retour identique
        if closest:
            return [pans[i] for i in range(len(dates))], lat, lon
        else:
            return pans, lat, lon

    @staticmethod
    def tiles_info(panoid, zoom=5):
        image_url = "http://cbk0.google.com/cbk?output=tile&panoid={}&zoom={}&x={}&y={}"
        coord = list(itertools.product(range(26), range(13)))
        return [(x, y, f"{panoid}_{x}x{y}.jpg", image_url.format(panoid, zoom, x, y)) for x, y in coord]

    @staticmethod
    def delete_tiles(tiles, directory):
        for _, _, fname, _ in tiles:
            try:
                os.remove(os.path.join(directory, fname))
            except OSError as e:
                StreetViewDownloader.logger.warning(f"Failed to delete tile {fname}: {e}")

    @staticmethod
    def find_nearest_panorama(lat, lon, radius=500000, API_KEY="Your_Api_Key"):
        """
        Renvoie (panoid, pano_lat, pano_lng) du panorama le plus proche,
        ou None si aucun panorama dans le rayon.
        """
        url = "https://maps.googleapis.com/maps/api/streetview/metadata"
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "key": API_KEY
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK":
            loc = data["location"]
            return data["pano_id"], loc["lat"], loc["lng"]
        else:
            StreetViewDownloader.logger.warning(f"Error: {data.get('status')}")
            return None
    
    @staticmethod
    def spiral_offsets(step=0.0005, max_radius=90):
        """
        Génère des (dx,dy) formant une spirale autour de (0,0),
        jusqu’à max_radius (en degrés décimaux).
        """
        x = y = 0
        dx, dy = step, 0
        segment_length = 1
        while math.hypot(x, y) <= max_radius:
            for _ in range(segment_length):
                if math.hypot(x, y) > max_radius:
                    return
                yield x, y
                x, y = x + dx, y + dy
            dx, dy = -dy, dx
            if dy == 0:
                segment_length += 1

    @staticmethod
    def download_panorama_v3(panoid, zoom=5, disp=False):
        '''
        v3: télécharge et assemble les tuiles d'une image Street View en mémoire.
        - panoid : identifiant panorama Google
        - zoom : niveau de zoom (1 à 5 recommandé, 2-3 conseillé pour la fiabilité)
        - disp : afficher la progression du téléchargement
        Retourne : une image panorama (format numpy array)
        '''
        tile_width = 512
        tile_height = 512
        img_w = 416 * (2 ** zoom)
        img_h = 416 * (2 ** (zoom - 1))
        tiles = tiles_info(panoid, zoom=zoom)
        valid_tiles = []

        for i, tile in enumerate(tiles):
            x, y, fname, url = tile

            if disp and i % 20 == 0:
                StreetViewDownloader.logger.info(f"Download of image {i+1} / {len(tiles)}")

            # Vérifie si la tuile est dans la zone valide
            if x * tile_width >= img_w or y * tile_height >= img_h:
                continue

            # Tentative de téléchargement avec gestion des erreurs
            success = False
            for attempt in range(3):
                try:
                    response = requests.get(url, stream=True, timeout=5)
                    if response.status_code == 200:
                        tile_img = Image.open(BytesIO(response.content))
                        valid_tiles.append(tile_img)
                        success = True
                        break
                    else:
                        StreetViewDownloader.logger.warning(f"HTTTP Error {response.status_code} for {url}")
                except Exception as e:
                    StreetViewDownloader.logger.warning(f"Error while downloading {url}: {e}")
                    time.sleep(1)
            
            if not success:
                StreetViewDownloader.logger.warning(f"Invalid tile {url}, adding black tile")
                valid_tiles.append(Image.new('RGB', (tile_width, tile_height), (0, 0, 0)))  # tuile noire

        # Assemblage de l'image finale
        panorama = Image.new('RGB', (img_w, img_h))
        i = 0
        for x, y, fname, url in tiles:
            if x * tile_width < img_w and y * tile_height < img_h:
                tile = valid_tiles[i]
                panorama.paste(im=tile, box=(x * tile_width, y * tile_height))
                i += 1

        return np.array(panorama)

    @staticmethod
    def download_panorama_v1(panoid, zoom=5, disp=False, directory='temp'):
        '''
        v1: simplely concatenate original functions
        input:
            panoid
        output:
            panorama image (uncropped)
        '''
        tiles = tiles_info( panoid, zoom=zoom)
        if not os.path.exists(directory):
            os.makedirs( directory )
        # function of download_tiles
        for i, (x, y, fname, url) in enumerate(tiles):

            if disp and i % 20 == 0:
                StreetViewDownloader.logger.info("Image %d / %d" % (i, len(tiles)))

            # Try to download the image file
            while True:
                try:
                    response = requests.get(url, stream=True)
                    break
                except requests.ConnectionError:
                    StreetViewDownloader.logger.warning("Connection error. Trying again in 2 seconds.")
                    time.sleep(2)
            with open(directory + '/' + fname, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
        # function of stich_tiles
        tile_width = 512
        tile_height = 512

        panorama = Image.new('RGB', (26*tile_width, 13*tile_height))

        for x, y, fname, url in tiles:
            fname = directory + "/" + fname
            tile = Image.open(fname)
            panorama.paste(im=tile, box=(x*tile_width, y*tile_height))
            del tile
        delete_tiles( tiles, directory )
        return np.array(panorama)

    @staticmethod
    def download_panorama_v2(panoid, zoom=5, disp=False, directory='temp'):
        '''
        v2: if tile is in invalid region, just skip them. obsolete: use black block instead of downloading
        input:
            panoid
        output:
            panorama image (uncropped)
        '''
        img_w, img_h = 416*(2**zoom), 416*( 2**(zoom-1) )
        tile_width = 512
        tile_height = 512
        
        tiles = tiles_info( panoid, zoom=zoom)
        valid_tiles = []
        if not os.path.exists(directory):
            os.makedirs( directory )
        # function of download_tiles
        for i, tile in enumerate(tiles):
            x, y, fname, url = tile
            if disp and i % 20 == 0:
                StreetViewDownloader.logger.info("Image %d / %d" % (i, len(tiles)))
            if x*tile_width < img_w and y*tile_height < img_h: # tile is valid
                valid_tiles.append(tile)
                # Try to download the image file
                while True:
                    try:
                        response = requests.get(url, stream=True)
                        break
                    except requests.ConnectionError:
                        StreetViewDownloader.logger.warning("Connection error. Trying again in 2 seconds.")
                        time.sleep(2)
                with open(directory + '/' + fname, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response
                
        # function to stich
        panorama = Image.new('RGB', (img_w, img_h))
        for x, y, fname, url in tiles:
            if x*tile_width < img_w and y*tile_height < img_h: # tile is valid
                fname = directory + "/" + fname
                tile = Image.open(fname)
                panorama.paste(im=tile, box=(x*tile_width, y*tile_height))
                del tile
        StreetViewDownloader.delete_tiles( valid_tiles, directory )
        return np.array(panorama)

    @staticmethod
    def delete_tiles(tiles, directory):
        for x, y, fname, url in tiles:
            os.remove(directory + "/" + fname)

    @staticmethod
    def api_download(panoid, heading, flat_dir, key, width=640, height=640,
                    fov=120, pitch=0, extension='jpg', year=2017, fname=None):
        """
        Download an image using the official API. These are not panoramas.

        Params:
            :panoid: the panorama id
            :heading: the heading of the photo. Each photo is taken with a 360
                camera. You need to specify a direction in degrees as the photo
                will only cover a partial region of the panorama. The recommended
                headings to use are 0, 90, 180, or 270.
            :flat_dir: the direction to save the image to.
            :key: your API key.
            :width: downloaded image width (max 640 for non-premium downloads).
            :height: downloaded image height (max 640 for non-premium downloads).
            :fov: image field-of-view.
            :image_format: desired image format.
            :fname: file name

        You can find instructions to obtain an API key here: https://developers.google.com/maps/documentation/streetview/
        """
        if not fname:
            fname = "%s_%s_%s" % (year, panoid, str(heading))
        image_format = extension if extension != 'jpg' else 'jpeg'

        url = "https://maps.googleapis.com/maps/api/streetview"
        params = {
            # maximum permitted size for free calls
            "size": "%dx%d" % (width, height),
            "fov": fov,
            "pitch": pitch,
            "heading": heading,
            "pano": panoid,
            "key": key
        }

        response = requests.get(url, params=params, stream=True)
        try:
            img = Image.open(BytesIO(response.content))
            filename = '%s/%s.%s' % (flat_dir, fname, extension)
            img.save(filename, image_format)
        except:
            StreetViewDownloader.logger.warning("Image not found")
            filename = None
        del response
        return filename

    @staticmethod
    def download_flats(panoid, flat_dir, key, width=400, height=300,
                    fov=120, pitch=0, extension='jpg', year=2017):
        for heading in [0, 90, 180, 270]:
            StreetViewDownloader.api_download(panoid, heading, flat_dir, key, width, height, fov, pitch, extension, year)
