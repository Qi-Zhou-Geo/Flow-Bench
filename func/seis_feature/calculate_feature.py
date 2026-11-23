#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-10-23T14:48:46
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.signal import lfilter, butter


def seis_ES(data_m_s, nyquist_f, num_bin, f_lower_bin, f_upper_bin, ref_energy=1):
    # data_m_s: ground velocity in m/s, nyquist_f: in Hz
    # ref_energy: reference value in m**2/s (default 1 m**2/s)
    # returns ES = log10(energy / ref_energy), dimensionless

    full_freq = 2.0 * nyquist_f  # sampling frequency in Hz

    # if you use this, you need to make sure >> all input is correct
    ES = np.empty(num_bin, dtype=float)
    for bin_idx in range(num_bin):
        Fb, Fa = butter(  # type: ignore
            N=2,
            Wn=[f_lower_bin[bin_idx] / nyquist_f, f_upper_bin[bin_idx] / nyquist_f],
            btype="bandpass",
        )  # type: ignore

        data_m_s_filt = lfilter(b=Fb, a=Fa, x=data_m_s)
        energy = np.trapezoid(y=data_m_s_filt**2, dx=1.0 / full_freq)  # type: ignore unit by >> m**2/s

        # divide by ref_energy (m**2/s) -> pure number, then log10
        # to get energy back in m**2/s: ref_energy * 10**ES
        ES[bin_idx] = np.log10(energy / ref_energy)  # >> dimensionless

    return ES


def get_seis_ES(data_m_s, sps, f_lower_bin=None, f_upper_bin=None):
    """
    Calculate the log10 envelope integral for each frequency band.

    Args:
        data_m_s (array-like): 1D seismic velocity signal in m/s.

        sps (float): Sampling rate in Hz.

        f_lower_bin (array-like, optional): Lower band limits in Hz. Defaults to [1, 5, 10, 15, 20].
        f_upper_bin (array-like, optional): Upper band limits in Hz. Defaults to [5, 10, 15, 20, 25].

    Returns:
        np.ndarray: Log10 envelope integral for each frequency band.
    """

    # (1) Set the frequency bins
    if f_lower_bin is None:
        # use the default freqquency bin
        f_lower_bin = np.array([1, 5, 10, 15, 20])  # lower bounds of the dif_upper_binrent tested freq. bands
    else:
        f_lower_bin = np.array(f_lower_bin)

    if f_upper_bin is None:
        # use the default freqquency bin
        # 24.9 to avoid the boundary error for "butter"
        f_upper_bin = np.array([5, 10, 15, 20, 24.9])  # higher bounds of the dif_upper_binrent tested freq. bands
    else:
        f_upper_bin = np.array(f_upper_bin)

    # (2) Check the bin lengths
    if len(f_lower_bin) == len(f_upper_bin):
        num_bin = len(f_lower_bin)
    else:
        msg = f"Frequency-bound arrays must have the same length.\nf_lower_bin={f_lower_bin}, f_upper_bin={f_upper_bin}.\n\n"
        raise ValueError(f"{msg}")

    # (3) Check the maximum upper frequency
    nyquist_f = sps / 2
    max_freq = max(np.max(f_lower_bin), np.max(f_upper_bin))
    if max_freq >= nyquist_f:
        msg = f"Upper frequency boundary ({max_freq} Hz) must be below the Nyquist frequency ({nyquist_f} Hz)."
        raise ValueError(msg)

    # (4) Calculate ES for each frequency bin
    ES = seis_ES(
        data_m_s=data_m_s,
        nyquist_f=nyquist_f,
        num_bin=num_bin,
        f_lower_bin=f_lower_bin,
        f_upper_bin=f_upper_bin,
    )

    return ES
