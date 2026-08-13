#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = Last modified: 2026-08-13T13:50:09
#__author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
#__find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

from obspy import UTCDateTime


def round_time(t, fmt="%Y-%m-%dT%H:%M:%S"):
    
    t = UTCDateTime(t)

    # seconds since start of hour
    seconds = t.minute * 60 + t.second + t.microsecond / 1e6

    # nearest 15-min block in seconds
    round_seconds = round(seconds / 900) * 900

    # reset to start of hour, then add rounded seconds
    t_round = UTCDateTime(year=t.year, month=t.month, day=t.day, hour=t.hour) + round_seconds
    t_round = t_round.strftime(fmt)
    
    return t_round
