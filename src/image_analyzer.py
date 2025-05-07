import os
import cv2
import numpy as np

from custom_logger import CustomLogger


class ImageAnalyzer:
    def __init__(self, image_dir="Image"):
        self.image_dir = image_dir
        self.element = np.ones((5, 5), np.uint8)
        self.logger = CustomLogger(__name__)

    def median_filter(self, I, D):
        imgFiltre = np.zeros(I.shape)
        for i in range(1, len(I) - int(D / 2)):
            for j in range(1, len(I[i]) - int(D / 2)):
                imgFiltre[i][j] = self.median_value(I, D, i, j)
        return imgFiltre

    def median_value(self, I, D, x, y):
        med = []
        m = int(D / 2)
        for i in range(D):
            for j in range(D):
                med.append(I[x + i - m][y + j - m])
        med.sort()
        return med[int(len(med) / 2)]

    def subtract_images(self, I1, I2):
        return np.abs(I1.astype(int) - I2.astype(int)).astype(np.uint8)

    def hysteresis_threshold(self, I, seuilMax, seuilMin):
        Is = np.zeros(I.shape, dtype=np.uint8)
        Is[I >= seuilMax] = 255
        nbrModif = 1

        while nbrModif > 0:
            nbrModif = 0
            for i in range(1, I.shape[0] - 1):
                for j in range(1, I.shape[1] - 1):
                    if I[i, j] >= seuilMin and Is[i, j] != 255:
                        if any(Is[i + dx, j + dy] == 255 for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]):
                            Is[i, j] = 255
                            nbrModif += 1
        return Is

    def count_black_pixels(self, I):
        return np.sum(I == 0)

    def count_distinct_colors(self, I, tolerance=25):
        unique_colors = []
        for i in range(I.shape[0]):
            for j in range(I.shape[1]):
                pixel = I[i, j]
                if all(any(abs(int(pixel[c]) - int(ref[c])) > tolerance for c in range(3)) for ref in unique_colors):
                    unique_colors.append(pixel)
        return len(unique_colors)

    def init_image(self, filename):
        im = cv2.imread(filename)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return self.median_filter(im, 5)

    def get_contour_ratio(self, im):
        erode1 = cv2.erode(im, self.element, iterations=1)
        dilate1 = cv2.dilate(im, self.element, iterations=1)
        image = self.subtract_images(dilate1, erode1)
        image2 = self.hysteresis_threshold(image, 10, 10)
        Isous = cv2.morphologyEx(image2, cv2.MORPH_OPEN, self.element)
        Isous = cv2.morphologyEx(Isous, cv2.MORPH_CLOSE, self.element)

        count = 0
        countAll = 0
        for x in range(540):
            y = int(-0.728 * x + 933)
            if 0 <= y < 1080:
                countAll += 1
                if Isous[y, x] == 255:
                    count += 1
        return Isous, (count / countAll) * 100 if countAll > 0 else 0

    def best_image_from_set(self, imgs):
        counts = [self.count_distinct_colors(img) for img in imgs]
        for i, count in enumerate(counts, 1):
            self.logger.debug(f"Number of colors in image {i}: {count}")

        return int(np.argmax(counts)) + 1

    def analyze(self, name="ZoRfAzQpDIZaD-QGoXTyDg_"):
        im_gray = self.init_image(os.path.join(self.image_dir, "PanoramaRevers.jpg"))
        _, ratio = self.get_contour_ratio(im_gray)
        self.logger.debug(f"border ratio: {ratio:.2f}%")

        if ratio < 60:
            base = os.path.join(self.image_dir, name)
            suffixes = ["0.jpg", "90.jpg", "180.jpg", "270.jpg"]
            paths = [base + suffix for suffix in suffixes]

            imgs = []
            for p in paths:
                if not os.path.exists(p):
                    raise FileNotFoundError(f"File not found: {p}")
                imgs.append(cv2.imread(p))

            best_index = self.best_image_from_set(imgs)
            return suffixes[best_index - 1]

        return "0.jpg"
