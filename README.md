# Forest Defenders 2 #

Bachelor's project for Eléonore d'Agostino, Spring 2016

Forest Defenders 2 is the sequel to Forest Defenders, and is a game of the puzzle arcade genre.

It's coded entirely in Python, through the Kivy framework, and should run on any OS, though there currently aren't any packaged releases.

## How do I launch the game? ##

* Download this repository
* Install Kivy, Numpy and Scipy (using `pip` or any other method of your choice)
* Run `python main.py` from the folder you downloaded to

## How to play? ##

### Goal ###

Your goal is to label sections of satellite photos to indicate which parts contain forest, using "fragments" on the right side of the screen. Your progress is tracked by the sapling in the bottom-left corner, and you have a time limit through the chainsaw on the bottom.

### Mouse controls ###

Menus are navigated by clicking the buttons, and fragments can be clicked and dragged around. The buttons next to them can be used to rotate, scale, or validate/cancel them.

### Keyboard controls ###

Menus can be navigated with the up/down arrows to move across buttons, and the spacebar to select. During gameplay, the controls are as follows:

* If no fragment is currently selected:
  * The vertical arrows move the cursor between fragments on the current page
  * The horizontal arrows change fragment pages
  * The spacebar selects the currently highlighted fragment
* Once a fragment is selected:
  * The directional arrows move the fragment
  * The X and C keys rotate the fragment counterclockwise and clockwise respectively
  * The A and S keys respectively shrink or enlarge the fragment
  * The spacebar validates the fragment
