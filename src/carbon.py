import urllib.request
from instagrapi import Client
from instagrapi.types import Location, StoryMention, StoryLocation, StoryLink, StoryHashtag
from PIL import Image, ImageFont, ImageDraw

urllib.request.urlretrieve("https://www.esrl.noaa.gov/gmd/webdata/ccgg/trends/co2/co2_weekly_mlo.txt", "co2.txt")
co2 = open("co2.txt", "r")
co2R = co2.read()
co2.close()
lastLine = ""
lineAbove = ""
i = len(co2R)-2
while i != 0 and co2R[i] != "\n":
    lastLine += co2R[i]
    i -= 1
lastLine = "".join(reversed(lastLine))
lastLine = lastLine.split()
i -= 1
while i != 0 and co2R[i] != "\n":
    lineAbove += co2R[i]
    i -= 1
lineAbove = "".join(reversed(lineAbove))
lineAbove = lineAbove.split()

texte = "\n\nLe taux de co2 dans l'atmosphère :\n\n\n\n\nLa semaine dérnière {} ppm\n\n\n\n\nIl y a deux semaines {} ppm\n\n\n\n\nIl y a 1 an {} ppm\n\n\n\n\nIl y a 10 ans {} ppm\n\n\n\n\n ppm = partie pour million".format(lastLine[4], lineAbove[4], lastLine[6], lastLine[7])

carbonImage = Image.open("src/carbonBG.jpg")
carbonImageEdit = ImageDraw.Draw(carbonImage)
font = ImageFont.truetype('arial.ttf', 60)
carbonImageEdit.text((60, 15), texte, (255, 255, 255), font=font)
carbonImage.save("Image/carbon.jpg")

bot = Client()
bot.login("imageduglobe", "3macs*C/EstGeni4l")
print("Bot log in!\n")


bot.photo_upload_to_story(
    "Image/carbon.jpg",
    caption="Test"
)

