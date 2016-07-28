import random
import os
import time

import config


# function used to obtain a level when in free mode
# modify only this function if you ever want to change how to load levels
def get_level():
    # TODO: modify code here to load random level from server
    # in the meantime, we just pick a random level from the level list

    if os.path.exists(config.level_directory):
        m = random.choice(os.listdir(config.level_directory))
        return os.path.join(config.level_directory, m)
    else:
        return None


# function used to save the user solution once a level has been completed
# modify only this function if you ever want to change where solutions are stored
def save_level(name, data):
    # TODO: modify code here to send results to server
    # in the meantime, we save the solution to a file

    data.save(os.path.join("results", name + "_result" + time.time() + ".png"))
