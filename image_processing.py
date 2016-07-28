import utils
import config

import functools as ft
import os


def get_filename(col, row, variant):
    return os.path.join(config.level_directory, str(col) + "_" + str(row) + "_" + variant + ".png")


# TODO: adapt for square images and single raw
def process(source, cols, rows):
    imarrays = [utils.ImageArray.load(source + "1.png"),
                utils.ImageArray.load(source + "2.png")]

    width = int(imarrays[0].cols / cols)
    height = int(imarrays[0].rows / rows)

    for row in range(rows-1, -1, -1):
        for col in range(cols):
            fn = ft.partial(get_filename, col, row)
            data = map(lambda a: a[row * height: (row + 1) * height, col * width: (col + 1) * width], imarrays)
            imts = map(lambda i: utils.ImageArray(height, width, data=data[i]), range(len(imarrays)))

            imts[0].save(fn("raw1"))
            imts[1].save(fn("raw2"))

            mixed = utils.ImageFilter.compute_mixed(*imts)
            mixed.save(fn("mix"))

            grey = utils.ImageFilter.greyscale(imts[0])
            grey.save(fn("grey"))

    print "success!"


def mix_nir(rgb_source, nir_source):
    rgb = utils.ImageArray.load(rgb_source)
    nir = utils.ImageArray.load(nir_source)
    assert rgb.data.shape[:2] == nir.data.shape[:2], "sizes do not match"

    rows, cols = rgb.data.shape[:2]
    image = utils.ImageArray(rows, cols)

    for x in xrange(rows):
        for y in xrange(cols):
            a = rgb[x, y, 1] / 255.0
            b = nir[x, y, 1] / 255.0
            # v = int((1 - (1 - a) * (1 - b)) * 255)
            # v = int(2 * a * b * 255) if a < 0.5 else int((1 - 2 * (1 - a) * (1 - b)) * 255)
            v = int(2 * a * b * 255) if b < 0.5 else int((1 - 2 * (1 - a) * (1 - b)) * 255)
            image[x, y] = (rgb[x, y, 0], v, rgb[x, y, 2], 255)
            # for c in xrange(3):
            #     a = rgb[x, y, c] / 255.0
            #     b = nir[x, y, c] / 255.0
            #     image[x, y, c] = int(2 * a * b * 255) if a < 0.5 else int(1 - 2 * (1 - a) * (1 - b) * 255)
            # image[x, y, 3] = 255

    # image.save("images/asdf.png")
    return image

mix_nir("images/rgb_small.png", "images/ndvi_small.png")
