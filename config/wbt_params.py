#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-11-02T20:34:58
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


def load_wbt_params():

    wbt_threshold_default = 500
    wbt_threshold_dict = {
        "Casamicciola": 5,
        "Chalk Cliffs": 5,
        "Hsiaolin": 100,
    }

    snap_dist_default = 0.001
    snap_dist_dict = {
        "Ergou": 0.03,
        "Huangbengliu": 0.03,
        "Museum Fire": 0.03,
        "Gorkha": 0.03,
        "Montecito": 0.03,
        "Bothekoshi": 0.03,
        "Tbilisa": 0.01,
        "Yanmen": 0.03,
        "Helens": 0.01,
        "Joffre": 0.005,
    }

    return wbt_threshold_default, wbt_threshold_dict, snap_dist_default, snap_dist_dict
