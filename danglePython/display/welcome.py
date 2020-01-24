#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-18 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK

"""
Unicode font rendering & scrolling.
"""

import os
import random
from demo_opts import get_device
from luma.core.virtual import viewport, snapshot, range_overlap
from luma.core.sprite_system import framerate_regulator
from PIL import ImageFont

# Messages - max length at smallest font is around 24 chars
welcome = [
    [u"Welcome", "white", "black"],
    [u"Team\n☸ Dangle ☸", "black", "white"],
    [u"⚠ Danger ⚠\nAhead", "white", "black"],
    [u"PiWars", "black", "white"],
    [u"Let the\nchallenges begin...", "black", "white"]
]

def make_font(name, size):
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)


def lerp_1d(start, end, n):
    delta = float(end - start) / float(n)
    for i in range(n):
        yield int(round(start + (i * delta)))
    yield end


def lerp_2d(start, end, n):
    x = lerp_1d(start[0], end[0], n)
    y = lerp_1d(start[1], end[1], n)

    try:
        while True:
            yield next(x), next(y)
    except StopIteration:
        pass


def pairs(generator):
    try:
        last = next(generator)
        while True:
            curr = next(generator)
            yield last, curr
            last = curr
    except StopIteration:
        pass


def infinite_shuffle(arr):
    copy = list(arr)
    while True:
        #random.shuffle(copy)
        for elem in copy:
            yield elem


def make_snapshot(width, height, text, fonts, fgcolor="white", bgcolor="black"):

    def render(draw, width, height):
        # Try in reducing font size until we find one where the width fits
        for font in fonts:
            size = draw.multiline_textsize(text, font)
            if size[0] <= width:
                 break
        # Render in the center
        left = (width - size[0]) // 2
        top = (height - size[1]) // 2
        draw.rectangle(((left, top), (left+size[0], top+size[1])), fill=bgcolor)
        s2 = draw.multiline_text((left, top), text=text, font=font, fill=fgcolor,
                            align="center", spacing=-2)

    return snapshot(width, height, render, interval=10)


def random_point(maxx, maxy):
    return random.randint(0, maxx), random.randint(0, maxy)


def overlapping(pt_a, pt_b, w, h):
    la, ta = pt_a
    ra, ba = la + w, ta + h
    lb, tb = pt_b
    rb, bb = lb + w, tb + h
    return range_overlap(la, ra, lb, rb) and range_overlap(ta, ba, tb, bb)


def main():
    regulator = framerate_regulator(fps=30)
    fonts = [make_font("code2000.ttf", sz) for sz in range(36, 8, -2)]
    sq = device.width * 2
    virtual = viewport(device, sq, sq)

    for msgwelcome_a, msgwelcome_b in pairs(infinite_shuffle(welcome)):
        welcome_a, fgcolor_a, bgcolor_a = msgwelcome_a
        welcome_b, fgcolor_b, bgcolor_b = msgwelcome_b
        widget_a = make_snapshot(device.width, device.height, welcome_a, fonts, fgcolor_a, bgcolor_a)
        widget_b = make_snapshot(device.width, device.height, welcome_b, fonts, fgcolor_b, bgcolor_b)

        posn_a = random_point(virtual.width - device.width, virtual.height - device.height)
        posn_b = random_point(virtual.width - device.width, virtual.height - device.height)

        while overlapping(posn_a, posn_b, device.width, device.height):
            posn_b = random_point(virtual.width - device.width, virtual.height - device.height)

        virtual.add_hotspot(widget_a, posn_a)
        virtual.add_hotspot(widget_b, posn_b)

        virtual.set_position(posn_a)
        for _ in range(30):
            with regulator:
                pass
        
        for posn in lerp_2d(posn_a, posn_b, device.width // 6):
            with regulator:
                virtual.set_position(posn)

        virtual.remove_hotspot(widget_a, posn_a)
        virtual.remove_hotspot(widget_b, posn_b)


if __name__ == "__main__":
    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass
