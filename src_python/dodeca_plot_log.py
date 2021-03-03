#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot timeseries of a log file acquired by the Twente Dodecahedron control
program. The plot will be saved as image to disk.
"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/project-Dodecahedron"
__date__ = "03-03-2021"
__version__ = "1.0"

import sys
import os
import numpy as np

import tkinter
from tkinter import filedialog

import matplotlib as mpl
import matplotlib.pyplot as plt

from dodeca_read_log import read_log, Log

# Characters
CHAR_PM = u"\u00B1"
CHAR_DEG = u"\u00B0"

# Colors
cm = (
    np.array(
        [
            [255, 255, 0],
            [252, 15, 192],
            [0, 255, 255],
            [255, 255, 255],
            [255, 127, 39],
            [0, 255, 0],
        ]
    )
    / 255
)

# ------------------------------------------------------------------------------
#   plot_log
# ------------------------------------------------------------------------------


def plot_log(log: Log):
    """
    Args:
        log (dodeca_read_log.Log): Log data structure
    """

    # --------------------------------------------------------------------------
    #   Prepare figure
    # --------------------------------------------------------------------------

    mpl.style.use("dark_background")
    mpl.rcParams["font.size"] = 12
    # mpl.rcParams['font.weight'] = "bold"
    mpl.rcParams["axes.titlesize"] = 14
    mpl.rcParams["axes.labelsize"] = 14
    mpl.rcParams["axes.titleweight"] = "bold"
    mpl.rcParams["axes.formatter.useoffset"] = False
    # mpl.rcParams["axes.labelweight"] = "bold"
    mpl.rcParams["lines.linewidth"] = 2
    mpl.rcParams["grid.color"] = "0.25"

    fig1 = plt.figure(figsize=(16, 10), dpi=90)
    fig1.canvas.set_window_title("%s" % log.filename)

    ax1 = fig1.add_subplot(4, 1, 1)
    ax2 = fig1.add_subplot(4, 1, 2, sharex=ax1)
    ax3 = fig1.add_subplot(4, 1, 3, sharex=ax1)
    ax4 = fig1.add_subplot(4, 1, 4, sharex=ax1)

    # Julabo temperatures
    ax1.plot(
        log.time, log.Julabo_setp, "-", color=cm[4], label=("Julabo setp."),
    )
    ax1.plot(
        log.time, log.Julabo_bath, "-", color=cm[5], label=("Julabo bath"),
    )

    ax1.set_title("%s\nJulabo temperatures" % (log.filename))
    ax1.set_xlabel("time (s)")
    ax1.set_ylabel("temperature (%sC)" % CHAR_DEG)
    ax1.grid(True)

    # Arduino temperatures
    ax2.plot(log.time, log.DS_temp, color=cm[0], label="DS temp.")
    ax2.plot(log.time, log.BME_temp, color=cm[1], label="BME temp.")

    ax2.set_title("Arduino temperatures (%s 0.5 K)" % CHAR_PM)
    ax2.set_xlabel("time (s)")
    ax2.set_ylabel("temperature (%sC)" % CHAR_DEG)
    ax2.grid(True)

    # Arduino humitidy
    ax3.plot(log.time, log.BME_humi, color=cm[2], label="BME humi.")

    ax3.set_title("Humidity (%s 3 %%)" % CHAR_PM)
    ax3.set_xlabel("time (s)")
    ax3.set_ylabel("humidity (%)")
    ax3.grid(True)

    # Arduino pressure
    ax4.plot(log.time, log.BME_pres, color=cm[3], label="BME pres.")

    ax4.set_title("Pressure (%s 1 mbar)" % CHAR_PM)
    ax4.set_xlabel("time (s)")
    ax4.set_ylabel("pressure (mbar)")
    ax4.grid(True)

    # --------------------------------------------------------------------------
    #   Final make-up
    # --------------------------------------------------------------------------

    ax_w = 0.9
    ax_h = 0.15

    ax1.set_position([0.08, 0.79, ax_w, ax_h])
    ax2.set_position([0.08, 0.55, ax_w, ax_h])
    ax3.set_position([0.08, 0.31, ax_w, ax_h])
    ax4.set_position([0.08, 0.07, ax_w, ax_h])

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper left")

    # --------------------------------------------------------------------------
    #   Save figure
    # --------------------------------------------------------------------------

    img_format = "png"
    fn_save = "%s.%s" % (log.filename, img_format)
    plt.savefig(
        fn_save,
        dpi=90,
        orientation="portrait",
        papertype="A4",
        format=img_format,
        transparent=False,
    )
    print("Saved image: %s" % fn_save)


# ------------------------------------------------------------------------------
#   Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Check for optional input arguments
    filename_supplied = False
    for arg in sys.argv[1:]:
        filename = arg
        filename_supplied = True

    root = tkinter.Tk()
    root.withdraw()  # Disable root window

    if not filename_supplied:
        filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select data file",
            filetypes=(("text files", "*.txt"), ("all files", "*.*")),
        )
    if filename == "":
        sys.exit(0)

    root.destroy()  # Close file dialog

    print("Reading file: %s" % filename)
    plot_log(read_log(filename))
    plt.show()
