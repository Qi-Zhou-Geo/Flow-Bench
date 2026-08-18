#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-08-18T13:11:10
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

# region


# https://www.gfz-potsdam.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/pool-components/clipp-werte
# https://www.gfz-potsdam.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/pool-components/poles-and-zeros/trillium-c-120s

# total sensitivity = sensitivity_sensor * sensitivity_logger
# total sensitivity: counts per (meter per second) [counts / (m/s)]
# sensitivity_sensor: volts per (meter per second) [V·s/m, or V/(m/s)]
# sensitivity_logger: counts per volts [counts / V]

# Zeros and Poles for sensor
# GFZ geophone
# https://www.gfz.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/pool-components/poles-and-zeros/3d-geophone
# Trillium Compact; 120 s ... 108 Hz
# https://www.gfz.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/pool-components/poles-and-zeros/trillium-c-120s

# Zeros and Poles for logger
# DATA-CUBE3
# https://www.gfz.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/pool-components/clipp-werte

# sensor_logger_type = {
# works for AA
#     'zeros': [(a + bj)],
#
#     'poles': [(a + bj)],

# alway set as 1 for Obspy, and set sensitivity as: total sensitivity = sensitivity_sensor * sensitivity_logger
#     'gain': 1,
#     'sensitivity': sensitivity_sensor * sensitivity_logger # ctotal sensitivity [counts / (m/s)]
# }

# endregion


def load_paz(sensor_type):

    paz_dict = {
        "paz-IGU-16HR-EB-3C-5Hz": {
            # works for SmartSolo IGU-16HR 3C
            # works for Jiangjia 2023 -> Prof. Dr. Shuai Li 2025 data, Luding 2023 STA01 DP* data
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [(-22.211059 + 22.217768j), (-22.211059 - 22.217768j)],
            "gain": 1000,
            "sensitivity": 76.7,  # counts / (m/s)
        },
        "paz-3D-Geophone-PE-6-B16": {
            # works for 3D Geophone PE-6/B; 4.5 ... 500 Hz(*) with DATA-CUBE3,
            # works for Jiangjia (gain 16) -> Prof. Dr. Shuai Li 2023 data
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [(-19.78 + 20.20j), (-19.78 - 20.20j)],
            "gain": 1,
            "sensitivity": 27.7 * 6.5574 * 1e7,  # counts / (m/s)
        },
        "paz-3D-Geophone-PE-6-B32": {
            # works for 3D Geophone PE-6/B; 4.5 ... 500 Hz(*) with DATA-CUBE3,
            # works for Ergou (gain 32) -> Prof. Dr. Yan Yan 2022 data
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [(-19.78 + 20.20j), (-19.78 - 20.20j)],
            "gain": 1,
            "sensitivity": 27.7 * 1.3115 * 1e8,  # counts / (m/s)
        },
        "paz-3D-NoiseScope": {
            # works for paz_3D_NoiseScope
            # works for Foutangba -> Prof. Dr. Yan Yan 2022 data
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [
                (-0.444221 - 0.6565j),
                (-0.444221 + 0.6565j),
                (-222.110595 - 222.17759j),
                (-222.110595 + 222.17759j),
            ],
            "gain": 298,
            # 6.71140939 * 1e9 = 2000 [V·s/m] * 1/298 [nV/count, nanovolts/count]
            "sensitivity": 6.71140939 * 1e9,  # counts / (m/s)
        },
        "paz-PMS10": {
            # works for PMS-10 short-period seismometer,
            # works for Tianmo data
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [(-0.44429 + 0.44429j), (-0.44429 - 0.44429j), (-666.43 + 666.43j), (-666.43 - 666.43j)],
            "gain": 888264,  # MUST set as 888264
            "sensitivity": 8.38 * 1e8,  # counts / (m/s)
        },
        "paz-smart-solo-Hailuogou": {
            # works for SmartSolo IGU-16HR 3C
            # works for Hailuogou 2024 -> Prof. Dr. Zongji Yang data,
            # DOI: https://doi.org/10.1029/2025WR042515
            "zeros": [(0 + 0j), (0 + 0j)],
            "poles": [(-22.211059 + 22.217768j), (-22.211059 - 22.217768j)],
            "gain": 1,
            "sensitivity": 76.8 * 8000,  # counts / (m/s)
        },
        #
        # The following catchments/sensors use scalar amplitude calibration.
        # The raw waveform amplitude is converted to ground velocity in m/s by:
        #
        #     velocity [m/s] = raw_amplitude [counts] / velocity_scale [counts per m/s]
        #
        # For waveforms already stored in m/s, set velocity_scale = 1.0
        # For waveforms stored as digital counts, velocity_scale is the number of counts corresponding to 1.0 m/s
        #
        # original unit is already m/s.
        "unknown-ChalkCliffs": 1.0,
        #
        # digital counts >> m/s
        "unknown-Goulinping": 2 * 10**9,
        #
        # digital counts >> m/s
        "unknown-Ruapehu": 5 * 10**9,
        #
        # digital counts >> m/s
        "unknown-Hongqi": 838860800.0,  # (2.5 / 2**23) / 250.0,
        #
        # digital counts >> m/s
        "unknown-Yanmen": 838860800.0,  # (2.5 / 2**23) / 250.0,
    }

    inv_or_paz = paz_dict.get(sensor_type, None)  # retuen None incase there is no metadata

    return inv_or_paz
