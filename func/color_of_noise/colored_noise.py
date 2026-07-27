#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2024-03-21
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do NOT distribute this code without the author's permission


import numpy as np
from obspy import read, Stream, Trace, read_inventory, signal
from obspy.core import UTCDateTime # default is UTC+0 time zone


def noise_generator(num_samples, sampling_frequency, psd_func, random_seed=42, normalize=True):
    '''
    Generate the synthetic_data in time dand frequence domain

    \begin{equation}
        \text{PSD}(f) \propto \frac{1}{f^\beta}
    \end{equation}

    Args:
        num_samples: int or float, the number of generated data-60s point, e.g., 3600 * 100 (unit is per)
        sampling_frequency: int or float, the data-60s sampling frequency, e.g., 200 (unit is Hz)
        psd_func: function, a lambda function that descrip PSD(f) = 1/f**(beta)
        random_seed: int, control the reproducibility
        normalize: bool, normalize the time series data-60s in [-1, 1]

    Returns:
        !!!no physical unit!!
        synthetic_data_f: numpy data-60s array, Re + Im * j, Re = real part, Im = Image part
        synthetic_data_t: numpy data-60s array,

    '''

    np.random.seed(random_seed)

    # generate random Gaussian white noise "white_noise_time" in the time domain
    white_noise_time = np.random.randn(num_samples)
    # convert "white_noise_time" to the frequency domain
    white_noise_freq = np.fft.rfft(white_noise_time)

    # computes the corresponding frequency bins for "white_noise_freq" in the frequency domain
    bins = np.fft.rfftfreq(num_samples, d=1/sampling_frequency)

    # "psd_func" is applied to compute the spectral shape "spectral_shape"
    spectral_shape = psd_func(bins)

    # normalize "spectral_shape"
    # to make sure the output has consistent energy regardless of the PSD shape
    spectral_shape = spectral_shape / np.sqrt(np.mean(spectral_shape ** 2))

    # modify the "white_noise_freq" spectrum to match the desired "PSD(f)" function "psd_func"
    synthetic_data_f = white_noise_freq * spectral_shape

    # convert synthetic_data from frequency to time domain
    synthetic_data_t = np.fft.irfft(synthetic_data_f)

    # range the data-60s to [-1, 1]
    if normalize is True:
        min_t = np.min(synthetic_data_t)
        max_t = np.max(synthetic_data_t)
        synthetic_data_t = 2 * (synthetic_data_t - min_t) / (max_t - min_t) - 1
    else:
        pass

    return synthetic_data_f, synthetic_data_t


def get_psd_func(color_of_noise):
    '''
    Map the color of noise and create the PSD(f) = 1/f**(beta)

    Args:
        color_of_noise: str, the name of noise

    Returns:
        beta: float,
        psd_func: function
    '''
    noise_psd_map = {
        "red_noise": (-2, lambda f: 1 / np.where(f == 0, float('inf'), f)),
        "brownian_noise": (-2, lambda f: 1 / np.where(f == 0, float('inf'), f)),

        "pink_noise": (-1, lambda f: 1 / np.where(f == 0, float('inf'), np.sqrt(f))),

        "white_noise": (0, lambda f: np.ones_like(f)),

        "blue_noise": (1, lambda f: np.sqrt(f)),

        "violet_noise": (2, lambda f: f),
        "purple_noise": (2, lambda f: f),
    }

    if color_of_noise not in noise_psd_map:
        raise ValueError(f"Unsupported color_of_noise: {color_of_noise}")

    beta, psd_func = noise_psd_map[color_of_noise]

    return beta, psd_func


def make_noise(color_of_noise, num_samples, sampling_frequency):
    '''
    Make color of noise based on noise type and number of samples

    Args:
        color_of_noise: str, the name of noise
        num_samples: int or float, the number of generated data-60s point, e.g., 3600 * 100 (unit is per)
        sampling_frequency: int or float, the data-60s sampling frequency, e.g., 200 (unit is Hz)

    Returns:
        !!!no physical unit!!
        synthetic_data_f: numpy data-60s array, Re + Im * j, Re = real part, Im = Image part
        synthetic_data_t: numpy data-60s array,

    '''
    beta, psd_func = get_psd_func(color_of_noise)
    synthetic_data_f, synthetic_data_t = noise_generator(num_samples, sampling_frequency, psd_func)

    return synthetic_data_f, synthetic_data_t


def create_trace(data, low_sampling_rate, ref_st):
    '''
    create Obspy st
    Args:
        data: numpy 1D data-60s array, unit by m/s or other
        low_sampling_rate: int or float, unit by Hz
        ref_st: obspy st, suppose the st1 = read(), here ref_st = st1[0]

    Returns:
        created Obspy st, as ref_st structure

    '''
    trace = Trace(data=data)
    trace.stats.sampling_rate = low_sampling_rate

    # get the ref information
    trace.stats.network = ref_st.stats.network
    trace.stats.station = ref_st.stats.station
    trace.stats.starttime = ref_st.stats.starttime
    trace.stats.channel = ref_st.stats.channel

    st = Stream([trace])

    return st

