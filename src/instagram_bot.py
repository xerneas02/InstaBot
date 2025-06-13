import os
import glob
import random
from time import sleep
from PIL import Image
import traceback

from instagrapi import Client
from instagrapi.types import Location, Usertag
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ChallengeRequired, ClientError


# Internal imports
from image_generator import ImageGenerator
from custom_logger import CustomLogger
from options import PUBLISH

from typing import List

def all_files_exist(paths: List[str]) -> bool:
    """
    Retourne True si tous les chemins de `paths` pointent vers un fichier existant,
    sinon affiche la liste des fichiers manquants et retourne False.
    """
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        print("Fichiers non trouvés :", missing)
        return False
    return True

class InstagramBot:
    SESSION_FILE = "insta_session.json"

    def __init__(self):
        self.logger = CustomLogger(__name__)
        self.login = os.getenv("LOGIN_INSTAGRAM")
        self.password = os.getenv("PASSWORD_INSTAGRAM")
        self.error = True
        self.max_attempts = 5
        self.attempts = 0
        self.bot = None
        self.proxy = os.getenv("PROXY_URL")

    def clear_image_folder(self, folder="Image"):
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            os.remove(f)
        self.logger.info("Image folder emptied")

    def format_location(self, location_list):
        loc = ", ".join(location_list)
        self.logger.debug(f"location = {loc}")
        return loc

    def generate_caption(self, lat, lon, loc, location):
        location_tag = ("".join(str(location[0]).split(" "))).split("/")[0].lower()
        text = (
            f"Location : {loc}\n"
            f"Latitude : {lat}, Longitude : {lon}\n"
            "Bot made by @eikthyrnir02 and @yannis.rch\n"
            "#googlemap #googleearth #googlestreetview #google #bot #photo #paysage "
            "#picture #landscape #beautifull #programmation #code #programming #globe "
            "#earth #panorama #360 #littleplanet #tinyplanet #ia #random #meteo "
            "#360photography #inverted360 #tinyearth360 #360tinyplanet #photosphere "
            f"#{location_tag} #everyday #photos"
        )
        self.logger.debug(f"Text generated")
        return text

    def login_bot(self):
        self.logger.info("Starting Instagram login process")
        self.bot = Client()

        try:
            # Attempt to load existing session
            if os.path.exists(self.SESSION_FILE):
                self.logger.debug(f"Session file found at {self.SESSION_FILE}, loading...")
                try:
                    self.bot.load_settings(self.SESSION_FILE)
                    self.logger.info("Loaded existing session settings successfully")
                except Exception as e:
                    self.logger.error(f"Failed to load session settings: {e}")
                    self.logger.debug(traceback.format_exc())
            else:
                self.logger.debug("No session file found, will perform fresh login")

            # Perform login
            self.logger.debug("Attempting to login with provided credentials")
            try:
                self.bot.login(self.login, self.password)
                self.logger.info("Login successful")
            except TwoFactorRequired as e:
                self.logger.error("Two-factor authentication required")
                self.logger.debug(traceback.format_exc())
                raise
            except ChallengeRequired as e:
                self.logger.error("Challenge required: further verification needed")
                self.logger.debug(traceback.format_exc())
                raise
            except LoginRequired as e:
                self.logger.error("Login required: invalid session, re-authenticating")
                self.logger.debug(traceback.format_exc())
                raise
            except ClientError as e:
                self.logger.error(f"Client error during login: {e}")
                self.logger.debug(traceback.format_exc())
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error during login: {e}")
                self.logger.debug(traceback.format_exc())
                raise

            # Save session settings after successful login
            try:
                self.bot.dump_settings(self.SESSION_FILE)
                self.logger.info("Session settings saved to file")
            except Exception as e:
                self.logger.error(f"Failed to dump session settings: {e}")
                self.logger.debug(traceback.format_exc())

        except Exception as e:
            self.logger.critical("Instagram login process failed", exc_info=True)
            raise

    def upload_post(self, album_path, caption):
        self.bot.album_upload(album_path, caption=caption)
        self.logger.info("Album uploaded")

    def run(self):
        self.logger.info("Start botInsta")

        while self.error and self.attempts < self.max_attempts:
            self.attempts += 1
            try:
                self.clear_image_folder()

                imageGenerator = ImageGenerator()
                lat, lon, location, path = imageGenerator.start()
                self.logger.debug(f"latitude = {lat}, longitude = {lon}")

                loc = self.format_location(location)
                caption = self.generate_caption(lat, lon, loc, location)

                if PUBLISH:
                    self.login_bot()

                    wait_minutes = random.randint(5, 20)
                    self.logger.info(f"Attente de {wait_minutes} minutes avant publication.")
                    sleep(wait_minutes * 60)

                    album_path = [
                        "Image/Panorama.jpg",
                        "Image/PanoramaRevers.jpg",
                        f"Image/{path}front.jpg",
                        f"Image/{path}right.jpg",
                        f"Image/{path}back.jpg",
                        f"Image/{path}left.jpg"
                    ]

                    # Check if all files exist before uploading
                    #print(f"Checking if all files exist {all_files_exist(album_path)}")
                    self.upload_post(album_path, caption)

                    # save images to a folder
                    for image_path in album_path:
                        image = Image.open(image_path)
                        image.save(os.path.join("Image", os.path.basename(image_path)))

                self.logger.info("End of the process")
                self.error = False

            except Exception as e:
                self.logger.error(f"Error: {e}")

        if self.attempts <= 3:
            self.logger.info("Images published" if PUBLISH else "Images created")
        else:
            self.logger.error("Too many tries!")


if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()