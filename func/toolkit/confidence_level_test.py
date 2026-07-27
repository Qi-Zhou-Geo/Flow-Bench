#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2024-02-23
# __author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import numpy as np
from scipy.stats import t as student_t  # Student's t-distribution


def statistical_testing(input_data, row_or_column="column", confidence_interval=0.95):
    '''
    # Calculate the ranges based on confidence_interval by student t distribution

    Args:
        input_data: list or numpy array
        row_or_column: str,
        confidence_interval: float, the bigger, the more confidence

    Returns:
        output_mean: numpy array, 1D
        output_ci_range: numpy array, 1D
    '''

    input_data = np.array(input_data)

    if input_data.ndim == 1 and row_or_column == "column":
        print(f"input_data.ndim = 1, and row_or_column = column, \n "
              f"you may check the data structure")

    if input_data.ndim == 1:
        axis = 0
    elif input_data.ndim == 2:
        if row_or_column == "row":
            # calculate the mean and CI in the "row" dimension
            axis = 1
        else:
            # calculate the mean and CI in the "column" dimension
            axis = 0

    output_mean = np.mean(input_data, axis=axis)
    # standard Error of the Mean (output_mean)
    sem = np.std(input_data, axis=axis, ddof=1) / np.sqrt(input_data.shape[axis])

    degree_of_freedom = input_data.shape[axis] - 1
    alpha = 1 - confidence_interval  # significance level
    # cumulative probability up to the critical value in the right tail of the distribution
    tail = 1 - alpha / 2
    output_ci_range = student_t.ppf(tail, degree_of_freedom) * sem  # by t-distribution

    return output_mean, output_ci_range


def statistical_quantile_range(input_data, row_or_column="column", lower_q=5, upper_q=95):
    """
    Calculate the mean and quantile-based range (e.g., 5%-95% or 1%-99%) along rows or columns.

    Args:
        input_data: list or numpy array
        row_or_column: str, "row" or "column" to specify axis
        lower_q: float, lower percentile (e.g., 1, 5)
        upper_q: float, upper percentile (e.g., 99, 95)

    Returns:
        output_mean: numpy array, mean along specified axis
        output_q_range: numpy array, upper - lower quantile along specified axis
        output_lower_q: numpy array, lower quantile
        output_upper_q: numpy array, upper quantile
    """

    input_data = np.array(input_data)

    if input_data.ndim == 1:
        axis = 0
        if row_or_column == "column":
            print(f"input_data.ndim = 1, and row_or_column = column, using axis=0")
    else:
        axis = 0 if row_or_column == "column" else 1

    output_mean = np.mean(input_data, axis=axis)
    output_lower_q = np.percentile(input_data, lower_q, axis=axis)
    output_upper_q = np.percentile(input_data, upper_q, axis=axis)
    output_q_range = output_upper_q - output_lower_q

    return output_mean, output_q_range, output_lower_q, output_upper_q