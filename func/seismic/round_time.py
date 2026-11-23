#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-10-20T17:49:28
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission
import math
from obspy import UTCDateTime


def round_time(t, fmt="%Y-%m-%dT%H:%M:%S", direction="nearest"):

    t = UTCDateTime(t)

    # seconds since start of hour
    seconds = t.minute * 60 + t.second + t.microsecond / 1e6

    if direction == "previous":
        round_seconds = math.floor(seconds / 900) * 900
    elif direction == "next":
        round_seconds = math.ceil(seconds / 900) * 900
    elif direction == "nearest":
        round_seconds = round(seconds / 900) * 900
    else:
        raise ValueError("direction must be 'previous', 'next', or 'nearest'")

    # reset to start of hour, then add rounded seconds
    t_round = UTCDateTime(year=t.year, month=t.month, day=t.day, hour=t.hour) + round_seconds
    t_round = t_round.strftime(fmt)

    return t_round
