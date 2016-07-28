# must be imported first to prevent issues
from kivy.config import Config
Config.set('graphics', 'width', 800)
Config.set('graphics', 'height', 600)

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import Screen, ScreenManager

import gc
import numpy as np
import os

import config
import data_io
import image_widgets as imw
import utils


# loading widget instructions
Builder.load_file('screens.kv')
Builder.load_file('widgets.kv')

# ease-of-access for the only screenmanager in use
MANAGER = None

# pre-load game music
musicA = SoundLoader.load("audio/A Forest Defenders 2 - Light.wav")
musicB = SoundLoader.load("audio/B Forest Defenders 2 - Dense.wav")


# specialized version of screen that handles keyboard presses and has a cursor system,
# used for all the screens outside the loading screen
class KeyScreen(Screen):
    def __init__(self, **kwargs):
        super(KeyScreen, self).__init__(**kwargs)

        self._keyboard = None

        # cursor options
        # determines direction the cursor traverses the array in
        self.cursor_reverse = False
        # whether cursor wraps around or stops at both ends
        self.cursor_wrap = False
        # array of kivy widgets that the cursor will traverse
        self.cursor_array = []

        self.cursor_active = True
        self.cursor_index = -1
        self.cursor = None

    # initializes keyboard before the screen starts
    def on_pre_enter(self, *args):
        super(KeyScreen, self).on_pre_enter(*args)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    # deactivates the keyboard (for this screen) once the screen stops
    def on_leave(self, *args):
        self._keyboard_closed()

    # erases cursor from the screen, without moving it
    def clear_cursor(self):
        if self.cursor:
            self.canvas.remove(self.cursor)

    # displays selection on currect cursor
    # setting offset to a value other than default (0) moves the cursor by that much
    def cursor_select(self, offset=0):
        if self.cursor_active:

            # computes next cursor position based on offset and wrap mode
            if self.cursor_wrap:
                index = (max(self.cursor_index, 0) + offset) % len(self.cursor_array)
            else:
                index = self.cursor_index + offset

            # updates the cursor if the new position is valid
            if 0 <= index < len(self.cursor_array):
                self.cursor_index = index
                current = self.cursor_array[self.cursor_index]

                # clears current cursor and forces refresh
                self.clear_cursor()
                self.canvas.ask_update()

                # draws new cursor and forces refresh
                with self.canvas:
                    Color(rgba=config.cursor_color)
                    self.cursor = Rectangle(pos=current.pos, size=current.size)
                self.canvas.ask_update()

    # action to take when pressing the "validate" button on the current cursor selection
    # default behavior is to click on the selected button
    def cursor_validate(self):
        self.cursor_array[self.cursor_index].trigger_action()

    # method to deactive the keyboard if it's still active
    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None

    # handles button presses in that screen
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]

        # to handle reversed cursor traversal order
        up = "down" if self.cursor_reverse else "up"
        down = "up" if self.cursor_reverse else "down"

        # cursor movement
        if key == up:
            self.cursor_select(-1)
        elif key == down:
            self.cursor_select(1)

        # validate current selected widget
        elif key == "spacebar":
            if self.cursor_index != -1:
                self.clear_cursor()
                self.cursor_validate()
                self.cursor_index = -1


class BackKeyScreen(KeyScreen):
    def __init__(self, previous, **kwargs):
        super(BackKeyScreen, self).__init__(**kwargs)

        # set previous screen for back button
        self.previous = previous

    # returns to previous screen
    def back(self):
        self.manager.switch_to(self.previous, direction='right')


class LoadingScreen(Screen):
    pass


# screen corresponding to the main menu
class MainMenuScreen(KeyScreen):
    # layout containing the screen's buttons, used for cursor function
    layout = ObjectProperty()

    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)

        # cursor options
        self.cursor_array = self.layout.children[:-1]
        self.cursor_reverse = True
        self.cursor_wrap = True

    # switches to the how to screen
    def howto(self):
        self.manager.switch_to(HowToScreen(name="HowTo", previous=self), direction='left')

    # switches to the training mode menu
    def training_mode(self):
        self.manager.switch_to(TrainingModeScreen(name="TrainingMode", previous=self), direction='left')

    # sets loading screen to switch to free mode
    def free_mode(self):
        self.manager.add_widget(LoadingScreen(name="Loading"))
        self.manager.current = "Loading"
        Clock.schedule_once(lambda x: self.launch_free_mode(), 1)

    # launches new game in free mode after obtaining a random level
    def launch_free_mode(self):
        level = data_io.get_level()

        if level:
            self.manager.switch_to(GameScreen(name="Game", previous=self,
                                              image_set=imw.ImageSet(raw=level)),
                                   direction='left')


# "how to" screen
class HowToScreen(BackKeyScreen):
    # reference to back button for cursor use
    bback = ObjectProperty()
    # text contained on the screen, stored here for ease of reading
    text = StringProperty()

    def __init__(self, **kwargs):
        super(HowToScreen, self).__init__(**kwargs)

        # cursor can only select back button
        self.cursor_array = [self.bback]
        self.cursor_wrap = True

        # main text for the screen
        self.text = "[b]Overview:[/b] The goal of Forest Defenders 2 is to correctly label satellite maps.\n\n" + \
                    "[b]How to:[/b] You can drag-and-drop fragments in the right-most box onto the map, " + \
                    "and use the buttons to adjust its rotation or scale. " + \
                    "The sprout will grow according to how accurate your labelling is!\n\n" + \
                    "[b]End:[/b] You win the level if you can label enough for the sprout to grow into a tree! " + \
                    "Or you lose the level if you allow the chainsaw to reach it first." + \
                    "\n\n\n"


# screen for picking training mode difficulty
class TrainingModeScreen(BackKeyScreen):
    # layout containing the screen's buttons, used for cursor function
    layout = ObjectProperty()

    def __init__(self, **kwargs):
        super(TrainingModeScreen, self).__init__(**kwargs)

        # cursor options
        self.cursor_array = self.layout.children[:-1]
        self.cursor_reverse = True
        self.cursor_wrap = True

    # switches to level screen of the given difficulty
    def levels(self, difficulty):
        self.manager.switch_to(TrainingLevelScreen(name="Training", previous=self,
                                                   difficulty=difficulty, level_list=None),
                               direction='left')


# screen for picking level from given training difficulty
class TrainingLevelScreen(BackKeyScreen):
    # layout containing the screen's buttons, used for cursor function
    layout = ObjectProperty()
    # grid containing the level maps
    grid = ObjectProperty()
    # level difficulty
    difficulty = StringProperty()

    def __init__(self, difficulty, level_list, **kwargs):
        super(TrainingLevelScreen, self).__init__(**kwargs)
        self.difficulty = difficulty

        # checks for the level directory and lists its files
        if os.path.exists(config.level_directory):
            for l in os.listdir(config.level_directory):

                # checks the files with the correct naming conventions (DIFFICULTY_NAME.png)
                split = l.split("_")
                if split[0] == difficulty and (level_list is None or l[1] in level_list):
                    levelpath = os.path.join(config.level_directory, l)

                    # loads files onto the grid
                    if os.path.isfile(levelpath):
                        img = Image(source=levelpath)
                        img.bind(on_touch_down=self.select_level)
                        self.grid.add_widget(img)

        # cursor options
        self.cursor_array = self.layout.children[:-1]
        self.cursor_reverse = True
        self.cursor_wrap = True

    # launches the level corresponding to the selected image
    def select_level(self, view, touch):
        if view.collide_point(touch.x, touch.y) and not touch.is_mouse_scrolling:
            self.manager.switch_to(GameScreen(name="Game", previous=self,
                                              image_set=imw.ImageSet(raw=view.source)),
                                   direction='left')


# screen that displays during game overs and victory
class GameOverScreen(KeyScreen):
    # title to display on the screen
    title = StringProperty()

    def __init__(self, title, next_screen, **kwargs):
        super(GameOverScreen, self).__init__(**kwargs)
        self.title = title

        # screen to return to on exit
        self.next = next_screen

    # pressing any key continues to the next screen
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.cont()
        return True

    # continues to the next screen and activates the garbage collector to try to lower memory usage
    def cont(self):
        gc.collect()

        # checks whether to switch screens by name or object
        if self.next.name in self.manager.screen_names:
            self.manager.current = self.next.name
        else:
            self.manager.switch_to(self.next)


# screen for the main game
class GameScreen(KeyScreen):
    # ImageWidget containing the map
    image = ObjectProperty()
    # tree object, used to manipulate its growth
    tree = ObjectProperty()
    # cutter object, used to move the chainsaw
    cutter = ObjectProperty()
    # main layout of the screen, needed for adding/removing widgets
    layout = ObjectProperty()
    # box containing the fragments
    label_box = ObjectProperty()
    # image source to send to the ImageWidget map
    source = StringProperty()
    # box covering the fragment box before color has been picked
    color_picker = ObjectProperty()

    # - "previous" is the screen this screen was launched from
    # - "image_set" is an ImageSet object containing the map
    # - "fragment_list" allows for loading only a specific set of fragments instead of all of them
    def __init__(self, previous, image_set, fragment_list=None, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        # screen we came from, to pass on to game over/victory screen
        self.previous = previous

        # set image for the map and prepare it for color selection
        self.source = image_set.sources["raw"]
        self.image.imdata = utils.ImageArray.load(self.source)
        self.image.bind(on_touch_down=self.color_drop)

        # loads fragments from fragment directory
        self.f_index = 0
        self.fragments = []
        if os.path.exists(config.fragment_directory):
            for f in os.listdir(config.fragment_directory):
                if fragment_list is None or f in fragment_list:
                    imgpath = os.path.join(config.fragment_directory, f)
                    if os.path.isfile(imgpath):
                        img = Image(source=imgpath)
                        img.bind(on_touch_down=self.im_press)
                        self.fragments.append(img)

        # cursor options
        self.cursor_active = False
        self.cursor_array = self.fragments

        self.picker = None
        self.scatter = None
        self.cutter_event = None

        # starting values
        self.completion = 0
        self.tree_start = self.tree.height
        self.forest_color = None
        self.started = False

    # displays fragments in fragment box, changing index by offset if necessary
    def display_fragments(self, offset=0):
        # computes new fragment index if valid
        if 0 <= self.f_index + offset < len(self.fragments):
            self.f_index += offset

        # erases old fragments and displays new ones
        self.label_box.clear_widgets()
        for i in range(self.f_index, self.f_index + config.fragment_count):
            if 0 <= i < len(self.fragments):
                self.label_box.add_widget(self.fragments[i])

    # changes cursor behavior to call the "im_press" method on the selected fragment
    def cursor_validate(self):
        self.im_press(self.fragments[self.cursor_index])
        self.scatter.display_buttons()

    # checks if the scatter is on the image, and if so, applies it
    def validate_scatter(self):
        if self.image.intersects(self.scatter):
            # attempts to apply the mask with the current scatter
            valid, prog = self.image.mask(self.forest_color, self.scatter,
                                          *self.image.get_intersect_coords(self.scatter))

            # mask was validated
            if valid:
                # increases completion and grows tree accordingly
                self.completion += prog
                completion_percent = self.completion * 1.0 / self.image.imdata.size
                self.grow_tree(completion_percent)

                # reset the chainsaw's progression
                self.reset_cutter()

                # destroys the scatter
                self.scatter.deactivate()
                self.scatter.unbind(on_touch_up=self.im_release)
                self.scatter.parent.remove_widget(self.scatter)
                self.scatter = None

    # cancels a scatter without applying it
    def cancel_scatter(self):
        self.remove_widget(self.scatter)
        self.scatter = None

    # obtains the color below the mouse/cursor and attemps to register it as the forest color
    def color_drop(self, view, touch=None):
        # check for collision
        if not touch or (self.image.collide_point(touch.x, touch.y) and not touch.is_mouse_scrolling):
            # convert coordinates to normalized
            coords = (touch.x, touch.y) if touch else self.picker.pos
            x, y = (coords[0] - self.image.x) / self.image.width, (coords[1] - self.image.y) / self.image.height

            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                # convert coordinates to pixel array indices
                row, col = int((1 - y) * self.image.imdata.rows), int(x * self.image.imdata.cols)

                # gets color by doing mean around cursor selection
                self.forest_color = np.mean(np.mean(self.image.imdata[row-2:row+2, col-2:col+2], axis=0), axis=0)
                self.forest_color = map(lambda c: int(c), self.forest_color)

                # destroys color picker cursor and box
                self.image.unbind(on_touch_down=self.color_drop)
                self.layout.remove_widget(self.color_picker)

                if self.picker:
                    self.remove_widget(self.picker)
                    self.picker = None

                # activates cursor mode for fragments and displays them
                self.cursor_active = True
                self.display_fragments()

    # method called when selecting a fragment
    def im_press(self, view, touch=None):
        # check for collision
        if not touch or (view.collide_point(touch.x, touch.y) and not touch.is_mouse_scrolling):
            # destroy the current scatter if there is one
            if self.scatter:
                self.cancel_scatter()

            # create new scatter from selected fragment
            self.scatter = imw.ScatterFragment(validate=self.validate_scatter,
                                               cancel=self.cancel_scatter,
                                               image=view.source)
            self.scatter.bind(on_touch_up=self.im_release)

            # set scatter options and display it
            self.scatter.im = view
            self.scatter.center = touch.pos if touch else self.center
            self.add_widget(self.scatter)
            self.scatter.scale = 1.0

            # send touch information down to scatter to be able to drag it already
            if touch:
                self.scatter.on_touch_down(touch)

            # if the time limit with the chainsaw is not yet active, start it now
            if not self.started:
                self.start_clock()

    # displays the buttons once the scatter has been let go of for the first time
    def im_release(self, scatter, touch):
        if scatter.collide_point(touch.x, touch.y) and touch.grab_current:
            self.scatter.display_buttons()

    # starts the time limit with the chainsaw
    def start_clock(self, *args):
        self.cutter_event = Clock.schedule_interval(self.move_cutter, config.cutter_time / 10.0)
        self.started = True

    # moves the chainsaw towards the tree
    def move_cutter(self, dt):
        ph = {'right': self.cutter.pos_hint['right'] - .1, 'y': self.cutter.pos_hint['y']}
        anim = Animation(pos_hint=ph, duration=1)
        anim.bind(on_complete=lambda i, j: self.check_cut())
        anim.start(self.cutter)

    # resets the chainsaw's position, cancels the time limit, then restarts it after the downtime is over
    def reset_cutter(self):
        self.cutter_event.cancel()

        ph = {'right': 1.0}
        anim = Animation(pos_hint=ph, duration=config.cutter_downtime)
        anim.bind(on_complete=lambda i, j: self.start_clock())
        anim.start(self.cutter)

    # checks whether the chainsaw has collided with the tree
    def check_cut(self):
        # if it's collided, the player has lost and we switch to the game over screen
        if self.cutter.collide_widget(self.tree):
            self.cutter_event.cancel()
            MANAGER.switch_to(GameOverScreen(title="Game Over", next_screen=self.previous))

    # changes the tree's height to match the given completion state
    def grow_tree(self, completion_percent):
        # the tree hasn't reached the target height yet
        if completion_percent < config.complete_percent:
            # compute new height with given completion
            height = self.tree_start + ((self.height - self.tree_start) * completion_percent / config.complete_percent)

            anim = Animation(height=height, duration=2)

            # tree needs to transition between sapling and tree
            if self.tree.height < 1.7 * self.tree.width <= height:
                anim.bind(on_complete=self.update_tree)

            anim.start(self.tree)

        # the tree has reached the target height and the player has won
        else:
            self.win()

    # transitions tree from sapling image to tree image
    def update_tree(self, *args):
        sapling = self.tree
        parent = self.tree.parent
        self.tree = imw.TreeWidget(size=sapling.size, pos=sapling.pos,
                                   size_hint=sapling.size_hint, pos_hint=sapling.pos_hint)
        parent.remove_widget(sapling)
        parent.add_widget(self.tree)

    # the player has won!
    # we cancel ongoing events, save the player's results, and switch to the victory screen
    def win(self):
        if self.cutter_event:
            self.cutter_event.cancel()

        data_io.save_level(name=self.source.split("/")[1].split(".")[0], data=self.image.imdata)

        self.manager.switch_to(GameOverScreen(title="Success!", next_screen=self.previous))

    # handles button presses in this screen
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]

        # we currently have a fragment selected
        if self.scatter:
            # move scatter around
            if key == "up":
                self.scatter.y += config.translate_step
            elif key == "down":
                self.scatter.y -= config.translate_step
            elif key == "left":
                self.scatter.x -= config.translate_step
            elif key == "right":
                self.scatter.x += config.translate_step

            # rotate scatter
            elif key == "x":
                self.scatter.rotation += config.rotate_step
            elif key == "c":
                self.scatter.rotation -= config.rotate_step

            # scale scatter
            elif key == "a":
                self.scatter.scale -= config.scale_step
            elif key == "s":
                self.scatter.scale += config.scale_step

            # validate scatter
            elif key == "spacebar":
                self.validate_scatter()

        # we do not yet have a fragment selected, but we've already picked a color
        elif self.cursor_active:
            # switch between pages
            if key == "left":
                self.display_fragments(-8)
            elif key == "right":
                self.display_fragments(8)

            # switch between or validate fragments
            else:
                super(GameScreen, self)._on_keyboard_down(keyboard, keycode, text, modifiers)
                self.display_fragments()

        # we haven't picked a color yet
        else:
            # we already have a color picker onscreen
            if self.picker:
                # move the color picker around
                if key == "up":
                    self.picker.y += config.translate_step
                elif key == "down":
                    self.picker.y -= config.translate_step
                elif key == "left":
                    self.picker.x -= config.translate_step
                elif key == "right":
                    self.picker.x += config.translate_step

                # validate the color choice
                elif key == "spacebar":
                    self.color_drop(self.image)

            # we initialize a new color picker
            else:
                self.picker = Scatter(center=self.center)
                self.picker.add_widget(Image(size=(50, 50), source="images/fd2_cursor.png"))
                self.add_widget(self.picker)


# main application class
class ForestDefenders2App(App):
    # changes window title
    title = "Forest Defenders 2"

    def __init__(self, **kwargs):
        super(ForestDefenders2App, self).__init__(**kwargs)

        # initialize new ScreenManager for handling screens, and set it as global for ease of use
        self.manager = ScreenManager()
        global MANAGER
        MANAGER = self.manager

    def build(self):
        # load and start playing game audio
        if musicA:
            musicA.loop = True
            musicA.play()

        # set starting screen
        self.manager.switch_to(MainMenuScreen(name="MainMenu"))
        return self.manager


if __name__ == '__main__':
    ForestDefenders2App().run()
