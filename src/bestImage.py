# -*-coding:UTF8 -*
#-------------------------
# TD Morphologie
#@author: cteuliere
#-------------------------

import numpy as np
import cv2
from matplotlib import pyplot as plt
from PIL import Image
import sys
import os 

###############################################################
# Fonction de seuillage d'une image :

def Median(I, D):
    imgFiltre = np.zeros(I.shape)
    for i in range(1, len(I)-int(D/2)):
        for j in range(1, len(I[i])-int(D/2)):
            imgFiltre[i][j] = MedianFiltre(I, D, i, j)
    return imgFiltre

def MedianFiltre(I, D, x, y):
    med = []
    m = int(D/2)
    for i in range(D):
        for j in range(D):
            med.append(I[x + i-m][y + j-m])
    med.sort()
    return med[int(len(med)/2)]

def soustractionIm(I1, I2):
    Isous = np.zeros(I1.shape)
    for i in range(len(I1)):
        for j in range(len(I1[i])):
            Isous[i, j] = abs(I1[i, j] - I2[i, j])
            
    return Isous

def seuillageHyst(I, seuilMax, seuilMin):
    Is = np.zeros(I.shape)
    for i in range(len(I)):
        for j in range(len(I[i])):
            if I[i,j] >= seuilMax:
                Is[i, j] = 255
    nbrModif = 1
    while nbrModif > 0:
        nbrModif = 0
        for i in range(1, len(I)-1):
            for j in range(1, len(I[i]-1)):
                if I[i,j] >= seuilMin and Is[i, j] != 255 and ([i+1, j] == 255 or I[i-1, j] == 255 or [i, j+1] == 255 or I[i, j-1] == 255):
                    Is[i, j] = 255
                    nbrModif +=1
    return Is
    
def nbrBlackPixel(I):
    count = 0
    for i in range(len(I)):
        for j in range(len(I[i])):
            if I[i,j] == 0:
                count += 1
    return count

def nbrCouleur(I):
    count = 0
    listCouleur = []
    newCount = 0
    allRgb = False
    for i in range(len(I)):
        for j in range(len(I[i])):
            newCount = 0
            for k in listCouleur:
                allRgb = False
                for x in range(3):
                    if abs(int(I[i][j][x]) - int(k[x])) > 25:
                        allRgb = True
                if allRgb:
                    newCount +=1
            if newCount == len(listCouleur):
                count += 1
                listCouleur.append(I[i][j])
    return count

def initImage(filename):
    im = cv2.imread(filename) #Lecture d'une image avec OpenCV
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) # Conversion en niveaux de gris
    im = Median(im, 5)  #Debruitage
    return im

def getContour(im, element):
    erode1 = cv2.erode(im, element, iterations = 1)
    dilate1 = cv2.dilate(im, element, iterations = 1)
    image = soustractionIm(dilate1, erode1)
    image2 = seuillageHyst(image, 10, 10)
    Isous = cv2.morphologyEx(image2, cv2.MORPH_OPEN, element)
    Isous = cv2.morphologyEx(Isous, cv2.MORPH_CLOSE, element)
    count = 0
    countAll = 0
    for x in range(540):
        y = int(-0.728*x + 933)
        if y >= 0 and y < 1080:
            countAll += 1
            if Isous[y, x] == 255:
                count += 1
    return Isous, (count/countAll)*100

def bestImage(im1, im2, im3, im4):
    nbrBest = nbrCouleur(im1)
    print("nbrCouleur image 1 : {}".format(nbrBest))
    nbrIm2 = nbrCouleur(im2)
    print("nbrCouleur image 2 : {}".format(nbrIm2))
    nbrIm3 = nbrCouleur(im3)
    print("nbrCouleur image 3 : {}".format(nbrIm3))
    nbrIm4 = nbrCouleur(im4)
    print("nbrCouleur image 4 : {}".format(nbrIm4))

    number = 1
    if nbrBest < nbrIm2:
        nbrBest = nbrIm2
        number = 2
    if nbrBest < nbrIm3:
        nbrBest = nbrIm3
        number = 3
    if nbrBest < nbrIm4:
        number = 4
    return number
###############################################################
# Fonction principale du script :
def main(name="ZoRfAzQpDIZaD-QGoXTyDg_"):
    print(name)
    element = np.ones((5,5), np.uint8)

    # contour sur PanoramaRevers (OK)
    im_gray = initImage("Image/PanoramaRevers.jpg")
    _, ratio = getContour(im_gray, element)
    print(ratio)

    # On ne s'intéresse aux 4 vues plates que si ratio<60%
    if ratio < 60:
        # construit le préfixe de chemin complet
        base = os.path.join("Image", f"{name}")

        # charge les 4 images couleur
        paths = [ base + suffix for suffix in ("0.jpg","90.jpg","180.jpg","270.jpg") ]
        imgs  = []
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(f"Le fichier {p} est introuvable")
            imgs.append(cv2.imread(p))

        # appel de ton bestImage original (qui prend 4 np.array)
        number = bestImage(imgs[0], imgs[1], imgs[2], imgs[3])

        # renvoie l’orientation choisie — c’est le suffixe .jpg
        return f"{['0','90','180','270'][number-1]}.jpg"

    # sinon, on renvoie par défaut la première vue
    return "0.jpg"