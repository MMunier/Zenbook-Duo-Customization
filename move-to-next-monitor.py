#!/usr/bin/python3
import sys

import Xlib
from Xlib import X, display
from Xlib.ext import randr

if not hasattr(sys, 'ps1'):
    sys.stderr = sys.stdout = open("/tmp/zenscreen_debug.log", "a")

SCALING = True

# https://stackoverflow.com/a/64502961
DISPLAY = display.Display()
default_screen = DISPLAY.get_default_screen()
screen = DISPLAY.screen(default_screen)

screen_count = DISPLAY.screen_count()

if screen_count != 1:
    print(f"Unexpected screen_count: {screen_count}")

NET_ACTIVE_WINDOW   = DISPLAY.intern_atom('_NET_ACTIVE_WINDOW')
NET_WM_NAME         = DISPLAY.intern_atom('NET_WM_NAME')  # UTF-8
WM_NAME             = DISPLAY.intern_atom('WM_NAME')           # Legacy encoding

NET_WM_STATE        = DISPLAY.intern_atom('_NET_WM_STATE') 
_NET_WM_STATE_MAXIMIZED_HORZ = DISPLAY.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ') 
_NET_WM_STATE_MAXIMIZED_VERT = DISPLAY.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT') 

ACTIVE_WINDOW_ID = screen.root.get_full_property(NET_ACTIVE_WINDOW,Xlib.X.AnyPropertyType).value[0]
ACTIVE_WINDOW = DISPLAY.create_resource_object('window', ACTIVE_WINDOW_ID)
#ACTIVE_WINDOW = ACTIVE_WINDOW.query_tree().parent

active_vm_state = ACTIVE_WINDOW.get_full_property(NET_WM_STATE, 4).value

MAXIMIZED_HORZ = _NET_WM_STATE_MAXIMIZED_HORZ in active_vm_state
MAXIMIZED_VERT = _NET_WM_STATE_MAXIMIZED_VERT in active_vm_state

MAXIMIZE_STATUS = []
if MAXIMIZED_HORZ: MAXIMIZE_STATUS.append(_NET_WM_STATE_MAXIMIZED_HORZ)
if MAXIMIZED_VERT: MAXIMIZE_STATUS.append(_NET_WM_STATE_MAXIMIZED_VERT)

# print("MAX_VERT", MAXIMIZED_VERT)
# print("MAX_HORZ", MAXIMIZED_HORZ)

parent_window = ACTIVE_WINDOW.query_tree().parent
embedding_geom = parent_window.get_geometry()

active_geom = ACTIVE_WINDOW.get_geometry()
BORDER_X = active_geom.x
BORDER_Y = active_geom.y

def set_fullscreen_status(window, mode: bool, properties):
    # True:  enable
    # False: disable

    data = [int(mode)] + properties
    data = data + (5 - len(data)) * [0]
    event = Xlib.protocol.event.ClientMessage(
        window=window,
        client_type=NET_WM_STATE,
        data=(32,(data)))
    screen.root.send_event(event, event_mask=Xlib.X.SubstructureRedirectMask)

def get_display_info():
    result = []

    res = randr.get_screen_resources(screen.root)
    for output in res.outputs:
        params = DISPLAY.xrandr_get_output_info(output, res.config_timestamp)
        if not params.crtc:
           continue

        crtc = DISPLAY.xrandr_get_crtc_info(params.crtc, res.config_timestamp)
        # print(crtc)
        # print(params)
        result.append({
            'name': params.name,
            'width': crtc.width,
            'height': crtc.height,
            'x': crtc.x,
            'y': crtc.y
        })

    return result

crtcs = get_display_info()
# print(ACTIVE_WINDOW.get_geometry())

def window_active_crtc(crtc_desc, window_geometry):
    x_center = window_geometry.x + window_geometry.width // 2
    y_center = window_geometry.y + window_geometry.height // 2

    return (crtc_desc['x'] <= x_center and crtc_desc['x'] + crtc_desc['width'] > x_center) \
        and (crtc_desc['y'] <= y_center and crtc_desc['y'] + crtc_desc['height'] > y_center)

is_active = [ window_active_crtc(crtc, embedding_geom) for crtc in crtcs]

# print(crtcs)
# print(is_active)

if not any(is_active):
    print("CENTER OF ACTIVE WINDOW NOT ON SCREEN!")
    new_x = 0 - BORDER_X
    new_y = 0 - BORDER_Y

    new_width = embedding_geom.width
    new_height = embedding_geom.height
 
if sum(is_active) > 1: 
        print("DISPLAYS ARE IN MIRRORING MODE, Result may be inconsistent")

if any(is_active):
    crtc_idx = 0
    while not is_active[crtc_idx % len(crtcs)]:
        crtc_idx += 1
    crtc_source = crtcs[crtc_idx % len(crtcs)]

    while is_active[crtc_idx % len(crtcs)]:
        crtc_idx += 1
    crtc_dest = crtcs[crtc_idx % len(crtcs)]


    if embedding_geom.width > crtc_source['width'] or embedding_geom.height > crtc_source['height']:
        print(f"Window {ACTIVE_WINDOW_ID} is larger than containing screen, ignoring")
        sys.exit(1) 

    # print(crtc_source, '->', crtc_dest)
    if SCALING:
        x_scale = crtc_dest['width'] / crtc_source['width']
        y_scale = crtc_dest['height'] / crtc_source['height']
    else:
        x_scale = 1
        y_scale = 1

    monitor_offset_x = embedding_geom.x - crtc_source['x']
    monitor_offset_y = embedding_geom.y - crtc_source['y']

    new_x = round(monitor_offset_x * x_scale) + crtc_dest['x'] - BORDER_X
    new_y = round(monitor_offset_y * y_scale) + crtc_dest['y'] - BORDER_Y
    new_width =  round(x_scale * embedding_geom.width)
    new_height = round(y_scale * embedding_geom.height)

print(f"Window-ID {ACTIVE_WINDOW_ID}, parent: {parent_window.id}, root: {screen.root.id}")
print(embedding_geom.x, embedding_geom.y, embedding_geom.width, embedding_geom.height)
print(new_x, new_y, new_width, new_height)

if len(MAXIMIZE_STATUS) > 0:
    set_fullscreen_status(ACTIVE_WINDOW, False, MAXIMIZE_STATUS)
parent_window.configure(x=new_x, y=new_y, width=new_width, height=new_height)
if len(MAXIMIZE_STATUS) > 0:
    set_fullscreen_status(ACTIVE_WINDOW, True, MAXIMIZE_STATUS)

DISPLAY.sync()
