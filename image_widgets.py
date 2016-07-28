from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

import matplotlib.pyplot as plt  # FOR TESTING
from scipy import misc, ndimage

import config
import utils


# utility class used to more easily transfer image sources across classes
# at the moment, typically only uses the "raw" kwarg, but allows for easier modification
class ImageSet:
    def __init__(self, **sources):
        self.sources = sources


class ScatterButton(Button):
    pass


class TreeWidget(Widget):
    pass


# widget that contains a fragment and its buttons
class ScatterFragment(Scatter):
    # texture to apply to the image within the scatter
    tex = ObjectProperty()
    # layout containing the fragment buttons
    buttons = ObjectProperty()

    def __init__(self, validate, cancel, image, **kwargs):
        super(ScatterFragment, self).__init__(**kwargs)

        # callbacks for the validation and cancel buttons
        self.validate = validate
        self.cancel = cancel

        # loading image from source and setting transparency
        self.image_array = utils.ImageArray.load(image)
        self.image_array[:, :, 3] = config.fragment_transparency
        self.tex = self.image_array.get_texture()

        # boolean to prevent from trying to reload buttons when they're already present
        self.has_buttons = False

    # removes buttons and all possible interactions with the fragment
    def deactivate(self):
        self.do_rotation = False
        self.do_scale = False
        self.do_translation = False
        self.remove_widget(self.buttons)

    # utility methods for modifying the scale and rotation via buttons
    def adjust_scale(self, scale_change):
        self.scale += scale_change

    def adjust_rot(self, rot_change):
        self.rotation += rot_change

    # displays buttons next to the fragment if they're not already there
    def display_buttons(self):
        if not self.has_buttons:
            # rotation buttons and layout
            rot_layout = BoxLayout(orientation="horizontal")
            rot_left = ScatterButton(text="<-")
            rot_left.bind(on_press=lambda x: self.adjust_rot(config.rotate_step))
            rot_right = ScatterButton(text="->")
            rot_right.bind(on_press=lambda x: self.adjust_rot(-config.rotate_step))
            rot_layout.add_widget(rot_left)
            rot_layout.add_widget(rot_right)

            # scaling buttons and layout
            scale_layout = BoxLayout(orientation="horizontal")
            scale_smaller = ScatterButton(text="-")
            scale_smaller.bind(on_press=lambda x: self.adjust_scale(-config.scale_step))
            scale_bigger = ScatterButton(text="+")
            scale_bigger.bind(on_press=lambda x: self.adjust_scale(config.scale_step))
            scale_layout.add_widget(scale_smaller)
            scale_layout.add_widget(scale_bigger)

            # validate/cancel buttons and layout
            validate_layout = BoxLayout(orientation="horizontal")
            validate_check = ScatterButton(text="v")
            validate_check.bind(on_press=lambda x: self.validate())
            validate_cancel = ScatterButton(text="x")
            validate_cancel.bind(on_press=lambda x: self.cancel())
            validate_layout.add_widget(validate_check)
            validate_layout.add_widget(validate_cancel)

            # adding everything to the scatter
            self.buttons.add_widget(rot_layout)
            self.buttons.add_widget(scale_layout)
            self.buttons.add_widget(validate_layout)

            self.has_buttons = True


# widget that contains the map image and all the methods to interact with it
class ImageWidget(Image):
    def __init__(self, **kwargs):
        super(ImageWidget, self).__init__(**kwargs)

    # returns whether the given view intersects with the map at any point
    # required for checking collision with scatters, due to local/window coordinates
    def intersects(self, view):
        im_x, im_y = self.to_window(*self.pos)
        im_right = im_x + self.width
        im_top = im_y + self.height

        sc_x, sc_y = view.to_window(*view.pos)
        sc_right = sc_x + view.width
        sc_top = sc_y + view.height

        return sc_right >= im_x and sc_x <= im_right and sc_top >= im_y and sc_y <= im_top

    # returns the normalized x, y, right and top values for a point that intersects the map
    def get_intersect_coords(self, view):
        x, y = self.to_window(*self.pos)

        normalized = [(view.x - x) / self.width, (view.y - y) / self.height,
                      (view.right - x) / self.width, (view.top - y) / self.height]
        return normalized

    # method that compares a fragment to the map and masks the map accordingly
    # - "forest" corresponds to our color target for forests
    # - "scatter" is the fragment we have selected
    # - the other inputs are the normalized values obtained through "get_intersect_coords"
    def mask(self, forest, scatter, x, y, right, top):
        # convert the bound (0-1) normalized coords to the size that corresponds in the map pixel data
        local_x = int(max(0.0, x) * self.imdata.cols)
        local_y = int((1.0 - max(0.0, y)) * self.imdata.rows)
        local_right = int(min(1.0, right) * self.imdata.cols)
        local_top = int((1.0 - min(1.0, top)) * self.imdata.rows)

        # alternate coords that are not bounded, required for handling intersecting fragments
        local_x_unbounded = int(x * self.imdata.cols)
        local_top_unbounded = int((1.0 - top) * self.imdata.rows)

        # size to resize the fragment to for array comparison
        size = (int((right - x) * self.imdata.cols),
                int((top - y) * self.imdata.cols))

        # resize and rotate fragment pixel array according to the scatter parameters
        fragment = ndimage.rotate(scatter.image_array[:, :, :3], scatter.rotation, order=0)
        fragment = misc.imresize(fragment, size=size, interp='nearest')

        progress = 0
        off = 0
        mask = {}
        if config.debug_mode:
            distribution = {}

        # iterate over all the pixels in the map that are "underneath" fragment pixels
        for row in xrange(local_top, local_y - 1):
            for col in xrange(local_x, local_right - 1):

                # ignore pixels that have already been previously labeled
                if tuple(self.imdata[row, col, :3]) not in [config.forest_example, config.not_example]:
                    index = tuple(fragment[row - local_top_unbounded, col - local_x_unbounded, :3])

                    if index == config.forest_example:
                        dif = 0
                        # compute difference from target color
                        for chan in xrange(3):
                            dif += abs(forest[chan] - self.imdata[row, col, chan])

                        if config.debug_mode:
                            distribution[dif] = distribution.get(dif, 0) + 1

                        # consider the pixel "potentially wrong" if it's above the threshold
                        if dif > config.forest_threshold:
                            off += 1
                    elif index == config.not_example:
                        pass
                    else:
                        continue

                    # register map masking according to the labeling
                    progress += 1
                    mask[(row, col)] = index

        # total fragment size
        total = (local_right - local_x) * (local_y - local_top)

        # displays debug information about difference distribution
        if config.debug_mode:
            if distribution:
                print "  min:", min(distribution.values()), "; max:", max(distribution.values())
                print (total - off) / (total * 1.0), "% of area is forest"
            plt.plot(distribution.keys(), distribution.values())
            plt.ylabel("Frequency")
            plt.xlabel("Difference from target")
            plt.show()

        # fragment is valid if there are more "correct" pixels than the validation rate
        valid = (total - off) / (total * 1.0) >= config.forest_validation_rate

        # applies the mask if the fragment is validated
        if valid:
            for pixel in mask:
                self.imdata[pixel[0], pixel[1], :3] = mask[pixel]
            self.texture = self.imdata.get_texture()

        return valid, progress
