import textwrap
import util

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
__trap_low_hp_warning__ = 0.3

__show_chapter__ = False
__chapter_text__ = 'Chapter 1. Departure'
log = util.create_logger()
#DEBUG - debug only (wiz mode), NONE -general info, WARN - warning (hp/mp),
# critical - critical hits, stepping on traps, critical hp level,
#info - general info on skills level up etc
message_levels = { 'DEBUG' : 0,  'NONE' : 1, 'WARN' : 2, 'CRITICAL' : 3, 'INFO' : 4, 'DAMAGE': 5}
prev_message = None
prev_message_count = 1
def message(text, level = 1):
    log.info(text)
    global prev_message, prev_message_count
    if isinstance(level, str):
        level = message_levels[level]
    wraped_msg = textwrap.wrap(text, MSG_WIDTH)
    if prev_message == hash(text):
        prev_message_count += 1
        for line in wraped_msg:
            __msgs__.pop()
        for line in wraped_msg:
            if len(__msgs__) == MSG_COUNT:
                __msg_history__.append(__msgs__.pop(0))
            __msgs__.append(('%s x%d' % (line, prev_message_count), level))
        return
    else:
        prev_message_count = 1
    prev_message = hash(text)
    for line in wraped_msg:
        if len(__msgs__) == MSG_COUNT:
            __msg_history__.append(__msgs__.pop(0))

        #add the new line as a tuple, with the text and the color
        __msgs__.append((line, level))


#create logger
import logging

logger = logging.getLogger("module_logger")
logger.setLevel(logging.DEBUG)
#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
#create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#add formatter to ch
ch.setFormatter(formatter)
#add ch to logger
logger.addHandler(ch)
gui_listener = None
player = None

def render_warn_yn_dialog(title):
    return gui_listener.render_yn_dialog(title, warn=True)

def require_hud_update():
    if gui_listener:
        gui_listener.render_ui(player)