import sys
import gl
import thirdparty.libtcod.libtcodpy as libtcod
from logging import log


KEYS = [
		(['y', '7', libtcod.KEY_KP7], ('move', (-1, -1))),
		(['k', '8', libtcod.KEY_UP, libtcod.KEY_KP8], ('move', (0, -1))),
		(['u', '9', libtcod.KEY_KP9], ('move', (1, -1))),
		(['h', '4', libtcod.KEY_LEFT, libtcod.KEY_KP4], ('move', (-1, 0))),
		(['.', '5', 's'], 'wait'),
		(['l', '6', libtcod.KEY_RIGHT, libtcod.KEY_KP6], ('move', (1, 0))),
		(['b', '1', libtcod.KEY_KP1], ('move', (-1, 1))),
		(['j', '2', libtcod.KEY_DOWN, libtcod.KEY_KP2], ('move', (0, 1))),
		(['n', '3', libtcod.KEY_KP3], ('move', (1, 1))),
		(['Q', libtcod.KEY_ESCAPE], 'quit'),
		(['g', ','], 'pick_up'),
		(['i'], 'inventory'),
		(['d'], 'drop'),
		(['>'], 'descend'),
		(['x'], 'look'),
		(['?'], 'help'),
		([libtcod.KEY_F1], 'wizard'),
]

def handle_keys(self, call_back):
    key = libtcod.console_wait_for_keypress(True)


def readkey():
	while True:
		key = libtcod.console_wait_for_keypress(True)
		#No need to react on service keys
		if key.vk == libtcod.KEY_ENTER and libtcod.KEY_ALT:
			#Alt+Enter: toggle fullscreen
			libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
			continue
		if key.vk in [libtcod.KEY_SHIFT, libtcod.KEY_CONTROL, libtcod.KEY_ALT, libtcod.KEY_CAPSLOCK]:
			continue
		if key.c != 0 and chr(key.c) not in '\x1b\n\r\t':
			s = chr(key.c)
			if key.shift:
				s = s.upper()
			return s
		elif key.vk:
			return key.vk

def parse_key(key):
    for keys, cmd in KEYS:
        if key in keys:
            return cmd
    return None
