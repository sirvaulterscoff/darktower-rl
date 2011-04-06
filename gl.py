import textwrap

__wizard_mode__ = False
__dlvl__ = 1
__xl__ = 1
__turn_count__ = 1

__game_state__ = "playing"

__fov_recompute__ = True

__msgs__ = []
__msg_history__ = []
MSG_WIDTH = 50
MSG_COUNT = 10

__hp_warning__ = 0.5

__show_chapter__ = True
__chapter_text__ = 'Chapter 1. Departure'
#DEBUG - debug only (wiz mode), NONE -general info, WARN - warning (hp/mp),
# critical - critical hits, stepping on traps, critical hp level,
#info - general info on skills level up etc
message_levels = { 'DEBUG' : 0,  'NONE' : 1, 'WARN' : 2, 'CRITICAL' : 3, 'INFO' : 4, 'DAMAGE': 5}

def message(text, level = 1):
    if isinstance(level, str):
        level = message_levels[level]
    wraped_msg = textwrap.wrap(text, MSG_WIDTH)

    for line in wraped_msg:
        if len(__msgs__) == MSG_COUNT:
            __msg_history__.append(__msgs__.pop(0))

        #add the new line as a tuple, with the text and the color
        __msgs__.append((line, level))