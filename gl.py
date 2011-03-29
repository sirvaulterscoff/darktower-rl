import textwrap

__wizard_mode__ = False
__dlvl__ = 1
__xl__ = 1
__turn_count__ = 1

__game_state__ = "playing"

__fov_recompute__ = True

__msgs__ = []
MSG_WIDTH = 50
MSG_COUNT = 250

__show_chapter__ = True
__chapter_text__ = 'Chapter 1. Departure'
def message(text, level):
    wraped_msg = textwrap.wrap(text, MSG_WIDTH)

    for line in wraped_msg:
        if len(__msgs__) == 250:
            del __msgs__[0]

        #add the new line as a tuple, with the text and the color
        __msgs__.append((line, level))