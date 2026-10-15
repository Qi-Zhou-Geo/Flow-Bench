#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-11T13:33:58
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.ndimage import uniform_filter1d

from dtaidistance import dtw


def min_max_normalize(x, size=19):
    """
    Normalize the 1D array to 0-1

    Args:
        x:

    Returns:

    """

    x = uniform_filter1d(x**2, size=19)  # if the data is 1/10 Hz, rolling mean energy over 19 * 10 s
    x_normalized = (x - np.min(x)) / (np.max(x) - np.min(x))

    return x_normalized


def calculate_dwt_matrix(traces_amp):
    """
    Calculate the DWT for each pari.

    Args:
        traces_amp (List(numpy.array)): denosied and normalized seismic data

    Returns:
        distance_matrix: 2D matrix
    """

    num_of_sequence = len(traces_amp)
    distance_matrix = np.zeros((num_of_sequence, num_of_sequence))

    # loop and create the matrix
    for i in range(num_of_sequence):
        for j in range(i + 1, num_of_sequence):  # avoid redundant calculations
            # dtw.distance or dtw.distance_fast (c-based),
            # return a bounded distance, 0 means that two instances are equal
            distance = dtw.distance_fast(traces_amp[i], traces_amp[j])
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance

    return distance_matrix
