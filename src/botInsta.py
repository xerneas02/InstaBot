import os
import glob
from time import sleep
import random
from PIL import Image
import getImage
import traceback
from instagrapi import Client
from instagrapi.types import Location, Usertag
import os

POST = False

login    = os.getenv("LOGIN_INSTAGRAM")
password = os.getenv("PASSWORD_INSTAGRAM")

error = True
debug = open("src/log.txt", "w")
debug.write("")
debug.close()
debug = open("src/log.txt", "a")
debug.write("Debut\n")
countLoop = 0
try:
    while(error and countLoop <= 5):
        countLoop += 1
        try: 
            files = glob.glob('Image/*')
            for f in files:
                os.remove(f)
            debug.write("fichier Image vidé\n")
            lat, lon, location, debug = getImage.start(debug)
            debug.write("latitude = {}, longitude = {}, ".format(lat, lon))
            loc = ""
            
            for i in location:
                loc += i + ", "
            loc = loc[:len(loc)-2]
            debug.write("location = {}\n".format(loc))

            if POST:
                bot = Client()
                bot.login(login, password)
                debug.write("Bot log in!\n")

                #yannis_id = bot.user_info("1722473835")
                #mathis_id = bot.user_info("19801251168")
                
                #tag = [Usertag(user=yannis_id, x=0, y=1), Usertag(user=mathis_id, x=1, y=1)]

                album_path = ["Image/Panorama.jpg", "Image/PanoramaRevers.jpg", "Image/imageToPost.jpg"]#, "Image/meteo.jpg"]

                print(location)
                text =  "Location : " + str(loc) + "\nLatitude : {}, Longitude : {}".format(lat, lon) + "\nBot made by @eikthyrnir02 and @yannis.rch\n#googlemap #googleearth #googlestreetview #google #bot #photo #paysage #picture #landscape #beautifull #programmation #code #programming #globe #earth #panorama #360 #littleplanet #tinyplanet #ia #random #meteo #360photography #inverted360 #tinyearth360 #360tinyplanet #photosphere #" + ("".join(str(location[0]).split(" "))).split("/")[0].lower() + " #everyday #photos"
                debug.write("\n{}\n\n".format(text))

                #loc = bot.location_complete(Location(name=country, lat=lat, lng=lon))
            
            
                bot.album_upload(
                    album_path,
                    caption = text,
                    #usertags=tag
                )

            debug.write("Fin\n")
            error = False
        except Exception as e:
            debug.write("Erreur : \n")
            debug.write("{}\n".format(e))
            error = True
            print(e)
            traceback.print_exc()
            debug.write("{}\n".format(traceback.format_exc()))
            sleep(60)

    if countLoop <= 3:
        if POST:
            print("Images published!")
            debug.write('Image publi!')
        else:
            print("Images created!")
            debug.write('Image créé!')
    else:
        print("Too many try!")
        debug.write("Trop d'erreur!")
except:
    pass
debug.close()