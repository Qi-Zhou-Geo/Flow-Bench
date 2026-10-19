#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-10-15T16:46:31
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


def utm_epsg_from_lonlat(lon, lat):  # in degree

    zone = min(int((lon + 180) / 6) + 1, 60)

    if lat >= 0:
        base = 32600  # northern hemisphere
    else:
        base = 32700  # southern hemisphere

    return f"EPSG:{base + zone}"
