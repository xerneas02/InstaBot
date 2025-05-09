import numpy as np
from skimage.transform import warp

from custom_logger import CustomLogger

class TinyPlanetTransformer:
    def __init__(self, input_shape=(1080, 1080), output_shape=(1080, 1080)):
        """
        Initialise le transformateur avec les dimensions de l'image source (input_shape)
        et de l'image de sortie (output_shape).
        """
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.logger = CustomLogger(__name__)
        self.logger.info(f"Transformer initialized with input shape: {input_shape} and output shape: {output_shape}")

    def scale_by_5_and_offset(self, coords):
        out = coords * 5
        out[:, 0] += 1000
        out[:, 1] += 300
        return out

    def output_coord_to_r_theta(self, coords):
        """Convertit des coordonnées cartésiennes en coordonnées polaires normalisées (r, θ)."""
        x_offset = coords[:, 0] - (self.output_shape[1] / 2)
        y_offset = coords[:, 1] - (self.output_shape[0] / 2)

        r = np.sqrt(x_offset ** 2 + y_offset ** 2)
        theta = np.arctan2(y_offset, x_offset)

        max_x_offset, max_y_offset = self.output_shape[1] / 2, self.output_shape[0] / 2
        max_r = np.sqrt(max_x_offset ** 2 + max_y_offset ** 2)

        r /= max_r
        theta = (theta + np.pi) / (2 * np.pi)

        return np.vstack((r, theta)).T

    def r_theta_to_input_coords(self, r_theta):
        """Convertit des coordonnées (r, θ) en coordonnées dans l'image source (x, y)."""
        r, theta = r_theta[:, 0], r_theta[:, 1]
        theta = theta - np.floor(theta)

        max_x, max_y = self.input_shape[1] - 1, self.input_shape[0] - 1
        xs = theta * max_x
        ys = (1 - r) * max_y

        return np.hstack((xs[:, np.newaxis], ys[:, np.newaxis]))

    def little_planet_map(self, coords):
        """Applique la transformation 'little planet' aux coordonnées données."""
        r_theta = self.output_coord_to_r_theta(coords)
        r_theta[:, 0] = r_theta[:, 0] ** 0.6

        r_theta[:, 1] += 0.1
        return self.r_theta_to_input_coords(r_theta)

    def warp(self, image, mapping_func=None, output_shape=None):
        """
        Applique la projection définie par mapping_func sur une image.

        :param image: Image numpy (H x W x C)
        :param mapping_func: Fonction de transformation (par défaut : little_planet_map)
        :param output_shape: Dimensions de sortie (par défaut : self.output_shape)
        :return: Image transformée (numpy array)
        """
        if mapping_func is None:
            mapping_func = self.little_planet_map
        if output_shape is None:
            output_shape = self.output_shape
        return warp(image, mapping_func, output_shape=output_shape, mode="wrap")
