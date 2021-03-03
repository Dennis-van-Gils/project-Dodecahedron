#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reads in a log file acquired with the Twente Dodecahedron control program.
A 2nd order Butterworth low-pass filter with a cut-off frequency of 0.1 Hz and
zero-phase distortion will be applied to the DS18B20 and BME280 timeseries.
Validated.
"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/project-Dodecahedron"
__date__ = "03-03-2021"
__version__ = "1.0"

import numpy as np
from scipy import signal
from pathlib import Path


class Log:
    def __init__(self):
        self.filename = ""
        self.header = [""]
        self.time = np.array([])
        self.DS_temp = np.array([])
        self.BME_temp = np.array([])
        self.BME_humi = np.array([])
        self.BME_pres = np.array([])
        self.Julabo_setp = np.array([])
        self.Julabo_bath = np.array([])


def read_log(filepath=None, apply_lowpass_filter: bool = True):
    """Reads in a log file acquired with the Twente Dodecahedron control
    program.

    Args:
        filepath (pathlib.Path, str):
            Path to the data file to open.

        apply_lowpass_filter (bool, default=True):
            Apply a 2nd order Butterworth low-pass filter with a cut-off
            frequency of 0.1 Hz and zero-phase distortion to the DS18B20 and
            BME280 timeseries?

    Returns: instance of Log class
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if not isinstance(filepath, Path):
        raise Exception(
            "Wrong type passed to read_log(). "
            "Should be (str) or (pathlib.Path)."
        )

    if not filepath.is_file():
        raise Exception("File can not be found\n %s" % filepath.name)

    with filepath.open() as f:
        log = Log()

        # Scan the first lines for the start of the header and data sections
        MAX_LINES = 100  # Stop scanning after this number of lines
        str_header = []
        success = False
        for i_line in range(MAX_LINES):
            str_line = f.readline().strip()

            if str_line.upper() == "[HEADER]":
                # Simply skip
                pass
            elif str_line.upper() == "[DATA]":
                # Found data section. Exit loop.
                i_line_data = i_line
                success = True
                break
            else:
                # We must be in the header section now
                str_header.append(str_line)

        if not success:
            raise Exception(
                "Incorrect file format. Could not find [DATA] " "section."
            )

        # Read in all data columns including column names
        tmp_table = np.genfromtxt(
            filepath.name,
            delimiter="\t",
            names=True,
            skip_header=i_line_data + 2,
        )

        # Rebuild into a Matlab style 'struct'
        log.filename = filepath.name[0:-4]
        log.header = str_header
        log.time = tmp_table["time"]
        log.DS_temp = tmp_table["DS_temp"]
        log.BME_temp = tmp_table["BME_temp"]
        log.BME_humi = tmp_table["BME_humi"]
        log.BME_pres = tmp_table["BME_pres"]
        log.Julabo_setp = tmp_table["Julabo_setp"]
        log.Julabo_bath = tmp_table["Julabo_bath"]

        if apply_lowpass_filter:
            # Apply low-pass filtering to specific timeseries
            f_s = 1 / np.mean(
                np.diff(log.time)
            )  # Original sampling frequency [Hz]
            f3dB_LP = 0.1  # Low-pass cut-off frequency: 0.1 [Hz]
            filt_b, filt_a = signal.butter(2, f3dB_LP / (f_s / 2), "lowpass")

            # Fill in the occasional NaN's in the DS_temp signal
            mask = np.isnan(log.DS_temp)
            log.DS_temp[mask] = np.interp(
                np.flatnonzero(mask), np.flatnonzero(~mask), log.DS_temp[~mask]
            )

            log.DS_temp = signal.filtfilt(filt_b, filt_a, log.DS_temp)
            log.BME_temp = signal.filtfilt(filt_b, filt_a, log.BME_temp)
            log.BME_humi = signal.filtfilt(filt_b, filt_a, log.BME_humi)
            log.BME_pres = signal.filtfilt(filt_b, filt_a, log.BME_pres)
            # log.Julabo_setp = signal.filtfilt(filt_b, filt_a, log.Julabo_setp)
            # log.Julabo_bath = signal.filtfilt(filt_b, filt_a, log.Julabo_bath)

    return log
