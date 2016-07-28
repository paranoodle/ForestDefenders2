# This file contains config info to set up most of the options in the program

# directory in which to store temporary level files
level_directory = "levels/"
# directory in which the fragments are stored (loaded automatically)
fragment_directory = "fragments/"


# color to use for cursor overlay
# format is normalized RGBA tuple/list (length 4, values from 0.0 to 1.0)
cursor_color = (0, 0, 1, 0.2)


# percentage required for a level to be considered completed
# format is float percentage, between 0.0 and 1.0 (100%)
complete_percent = 0.5
# time limit per fragment (seconds)
cutter_time = 20.0
# time before cutter restarts (seconds)
cutter_downtime = 5.0


# transparency level to use for fragments (non-normalized, 0-255 integer)
fragment_transparency = 100
# number of fragments per page (integer)
fragment_count = 8
# step to use when translating fragments, in pixels (float or integer)
translate_step = 5
# step to use when scaling fragments, in percentage offset
# (0.1 corresponds to a step of 10%, for values like 100% -> 110% -> 120%)
scale_step = 0.1
# step to use when rotating fragments, in degrees
rotate_step = 30


# the color corresponding to something explicitly not forests in the fragment previews
# format is non-normalized RGB (length 3, values from 0-255)
not_example = (0, 0, 0)

# the forest color displayed in the fragment previews
# format is non-normalized RGB (length 3, values from 0-255)
forest_example = (0, 255, 0)
# the threshold before a color is considered too far from the target forest color
forest_threshold = 20
# percent of forest under a fragment required for the fragment to be counted as valid
# format is float percentage, between 0.0 and 1.0 (100%)
forest_validation_rate = 0.8



# only use this if you know what you're doing
# displays various data useful when debugging
debug_mode = False
