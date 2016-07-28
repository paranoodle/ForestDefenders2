from kivy.graphics.texture import Texture

import errno
import numpy as np
import os
from scipy import misc


# represents an image in easily-editable format, with data in the form of an rgb or rgba numpy matrix
class ImageArray:
    # creates new image with given row and column size
    # - if data is kept empty, it's initialized as a black transparent image of the given size
    # - if data is given, it checks that its size corresponds to the given size, then copies its contents
    def __init__(self, rows, cols, data=None):
        self.rows = rows
        self.cols = cols
        self.size = rows * cols

        if data is not None:
            assert data.shape[0] == rows and data.shape[1] == cols,\
                "data does not match given size, expected (" + str(rows) + "," + str(cols) +\
                ") got " + str(data.shape[:2])
            assert data.shape[2] in [3, 4], "color array is of incorrect dimensions"

            if data.shape[2] == 3:
                self.data[:, :, :3] = data[:, :, :]
                self.data[:, :, 3] = 255
            elif data.shape[2] == 4:
                self.data = np.copy(data)
        else:
            self.data = np.zeros((rows, cols, 4))

    def __str__(self):
        return "Image array of size " + str(self.rows) + "x" + str(self.cols)

    # for easier access of the image data via numpy indexes
    def __getitem__(self, *args):
        return self.data.__getitem__(*args)

    def __setitem__(self, *args):
        self.data.__setitem__(*args)

    # utility method for faster copying
    def copy(self):
        return ImageArray(self.rows, self.cols, self.data)

    # returns texture for use in kivy, via kivy's "texture" widget attribute
    def get_texture(self):
        tex = Texture.create((self.cols, self.rows), colorfmt='rgba')
        buf = bytearray(0)
        for x in xrange(self.rows):
            for y in xrange(self.cols):
                pixel = self.data[self.rows - 1 - x, y]
                pixel = map(lambda p: int(p), pixel)
                buf.extend(pixel)
        buf = ''.join(map(chr, buf))
        tex.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return tex

    # saves the image to a file, creating any directories if they don't already exist
    def save(self, filename):
        assert type(filename) == str, filename + " is not a string"
        d = os.path.dirname(filename)
        if d and not os.path.exists(d):
            try:
                os.makedirs(d)
                print "automatically created directory"
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        misc.imsave(filename, self.data)

    # loads an ImageArray from an image file at the given filename
    @staticmethod
    def load(filename):
        assert type(filename) == str, filename + " is not a string"
        im = misc.imread(filename)
        (rows, cols) = im.shape[:2]
        return ImageArray(rows, cols, data=im)


# utility class for applying various filters to ImageArrays
class ImageFilter:
    t_min = 10
    t_max = 50

    # equalizes the image values via a histogram
    @staticmethod
    def equalize(im):
        flat = im.data.flatten()
        hist, bins = np.histogram(flat, 256, normed=True)
        cdf = hist.cumsum()
        cdf = 255 * cdf / cdf[-1]
        return np.interp(flat, bins[:-1], cdf).reshape(im.data.shape)

    # converts the image to greyscale
    @staticmethod
    def greyscale(im):
        rows, cols = im.data.shape[:2]
        image = ImageArray(rows, cols)
        g = np.dot(im[..., :3], [0.299, 0.587, 0.114])

        for x in xrange(rows):
            for y in xrange(cols):
                image[x, y] = [g[x, y], g[x, y], g[x, y], 255]

        return image


# "trick" class to easily generate gradients through OpenGL quirks
class Gradient(object):

    # generates a horizontal gradient from two non-normalized RGBA colors
    @staticmethod
    def horizontal(rgba_left, rgba_right):
        texture = Texture.create(size=(2, 1), colorfmt="rgba")
        pixels = rgba_left + rgba_right
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    # generates a vertical gradient from two non-normalized RGBA colors
    @staticmethod
    def vertical(rgba_top, rgba_bottom):
        texture = Texture.create(size=(1, 2), colorfmt="rgba")
        pixels = rgba_bottom + rgba_top
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture
