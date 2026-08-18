#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-17T09:44:21
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numbers
from obspy import Inventory


def cooking_recipe(st, inv_or_paz, f_min=1, f_max=25):

    st_copy = st.copy()

    st_copy.merge(method=1, fill_value="latest", interpolation_samples=0)
    st_copy._cleanup()
    st_copy.detrend("linear")
    st_copy.detrend("demean")
    st_copy.taper(max_percentage=0.01)

    pre_filt = (0.5 * f_min, f_min, f_max, 1.2 * f_max)
    if isinstance(inv_or_paz, Inventory) is True:
        st_copy = st_copy.remove_response(output="VEL", pre_filt=pre_filt, water_level=60, inventory=inv_or_paz)
    elif isinstance(inv_or_paz, dict) is True:
        st_copy = st_copy.simulate(paz_remove=inv_or_paz, paz_simulate=None, remove_sensitivity=True, pre_filt=pre_filt)
    elif isinstance(inv_or_paz, numbers.Number) is True:
        st_copy[0].data = st_copy[0].data / inv_or_paz
    else:
        raise ValueError(f"Unsupported inv_or_paz: {inv_or_paz}")

    st_copy.filter("bandpass", freqmin=f_min, freqmax=f_max)
    st_copy.detrend("linear")
    st_copy.detrend("demean")

    return st_copy
