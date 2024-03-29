#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twente Dodecahedron
"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/project-Dodecahedron"
__date__ = "20-12-2023"
__version__ = "2.0"
# pylint: disable=bare-except, broad-except

import os
import sys
import time

import numpy as np
import psutil

# Mechanism to support both PyQt and PySide
# -----------------------------------------

PYQT5 = "PyQt5"
PYQT6 = "PyQt6"
PYSIDE2 = "PySide2"
PYSIDE6 = "PySide6"
QT_LIB_ORDER = [PYQT5, PYSIDE2, PYSIDE6, PYQT6]
QT_LIB = None

# Parse optional cli argument to enfore a QT_LIB
# cli example: python benchmark.py pyside6
if len(sys.argv) > 1:
    arg1 = str(sys.argv[1]).upper()
    for i, lib in enumerate(QT_LIB_ORDER):
        if arg1 == lib.upper():
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in QT_LIB_ORDER:
        if lib in sys.modules:
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in QT_LIB_ORDER:
        try:
            __import__(lib)
            QT_LIB = lib
            break
        except ImportError:
            pass

if QT_LIB is None:
    this_file = __file__.split(os.sep)[-1]
    raise ImportError(
        f"{this_file} requires PyQt5, PyQt6, PySide2 or PySide6; "
        "none of these packages could be imported."
    )

# fmt: off
# pylint: disable=import-error, no-name-in-module
if QT_LIB == PYQT5:
    from PyQt5 import QtCore, QtGui, QtWidgets as QtWid    # type: ignore
    from PyQt5.QtCore import pyqtSlot as Slot              # type: ignore
    from PyQt5.QtCore import pyqtSignal as Signal          # type: ignore
elif QT_LIB == PYQT6:
    from PyQt6 import QtCore, QtGui, QtWidgets as QtWid    # type: ignore
    from PyQt6.QtCore import pyqtSlot as Slot              # type: ignore
    from PyQt6.QtCore import pyqtSignal as Signal          # type: ignore
elif QT_LIB == PYSIDE2:
    from PySide2 import QtCore, QtGui, QtWidgets as QtWid  # type: ignore
    from PySide2.QtCore import Slot                        # type: ignore
    from PySide2.QtCore import Signal                      # type: ignore
elif QT_LIB == PYSIDE6:
    from PySide6 import QtCore, QtGui, QtWidgets as QtWid  # type: ignore
    from PySide6.QtCore import Slot                        # type: ignore
    from PySide6.QtCore import Signal                      # type: ignore
# pylint: enable=import-error, no-name-in-module
# fmt: on

# pylint: disable=c-extension-no-member
QT_VERSION = QtCore.QT_VERSION_STR if QT_LIB in (PYQT5, PYQT6) else QtCore.__version__
# pylint: enable=c-extension-no-member

# \end[Mechanism to support both PyQt and PySide]
# -----------------------------------------------

import pyqtgraph as pg

print(f"{QT_LIB:9s} {QT_VERSION}")
print(f"PyQtGraph {pg.__version__}")

TRY_USING_OPENGL = True
if TRY_USING_OPENGL:
    try:
        import OpenGL.GL as gl  # pylint: disable=unused-import
        from OpenGL.version import __version__ as gl_version
    except:
        print("PyOpenGL  not found")
        print("To install: `conda install pyopengl` or `pip install pyopengl`")
    else:
        print(f"PyOpenGL  {gl_version}")
        pg.setConfigOptions(useOpenGL=True)
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(enableExperimental=True)
else:
    print("PyOpenGL  disabled")

from dvg_debug_functions import tprint, dprint, print_fancy_traceback as pft
from dvg_pyqt_controls import (
    create_Toggle_button,
    SS_TEXTBOX_READ_ONLY,
    SS_GROUP,
)
from dvg_pyqt_filelogger import FileLogger
from dvg_pyqtgraph_threadsafe import (
    HistoryChartCurve,
    LegendSelect,
    PlotManager,
)

from dvg_devices.Arduino_protocol_serial import Arduino
from dvg_devices.Julabo_circulator_protocol_RS232 import Julabo_circulator
from dvg_devices.Julabo_circulator_qdev import Julabo_circulator_qdev
from dvg_qdeviceio import QDeviceIO

# Global pyqtgraph configuration
# pg.setConfigOptions(leftButtonPan=False)
pg.setConfigOption("foreground", "#EEE")

# Constants
# fmt: off
DAQ_INTERVAL_MS    = 1000  # [ms]
CHART_INTERVAL_MS  = 500   # [ms]
CHART_HISTORY_TIME = 7200  # [s]
# fmt: on

# Show debug info in terminal? Warning: Slow! Do not leave on unintentionally.
DEBUG = False


def get_current_date_time():
    cur_date_time = QtCore.QDateTime.currentDateTime()
    return (
        cur_date_time.toString("dd-MM-yyyy"),  # Date
        cur_date_time.toString("HH:mm:ss"),  # Time
        cur_date_time.toString("yyMMdd_HHmmss"),  # Reverse notation date-time
    )


# ------------------------------------------------------------------------------
#   Arduino state
# ------------------------------------------------------------------------------


class State(object):
    """Reflects the actual readings, parsed into separate variables, of the
    Arduino. There should only be one instance of the State class.
    """

    def __init__(self):
        self.time = np.nan  # [s]
        self.ds_temp = np.nan  # ['C]
        self.bme_temp = np.nan  # ['C]
        self.bme_humi = np.nan  # [%]
        self.bme_pres = np.nan  # [bar]


state = State()

# ------------------------------------------------------------------------------
#   MainWindow
# ------------------------------------------------------------------------------


class MainWindow(QtWid.QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.setWindowTitle("Dodecahedron logger")
        self.setGeometry(350, 60, 1200, 900)
        self.setStyleSheet(SS_TEXTBOX_READ_ONLY + SS_GROUP)

        # -------------------------
        #   Top frame
        # -------------------------

        # Left box
        self.qlbl_update_counter = QtWid.QLabel("0")
        self.qlbl_DAQ_rate = QtWid.QLabel("DAQ: nan Hz")
        self.qlbl_DAQ_rate.setStyleSheet("QLabel {min-width: 7em}")

        vbox_left = QtWid.QVBoxLayout()
        vbox_left.addWidget(self.qlbl_update_counter, stretch=0)
        vbox_left.addStretch(1)
        vbox_left.addWidget(self.qlbl_DAQ_rate, stretch=0)

        # Middle box
        self.qlbl_title = QtWid.QLabel(
            "Dodecahedron logger",
            font=QtGui.QFont("Palatino", 14, weight=QtGui.QFont.Bold),
        )
        self.qlbl_title.setAlignment(QtCore.Qt.AlignCenter)
        self.qlbl_cur_date_time = QtWid.QLabel("00-00-0000    00:00:00")
        self.qlbl_cur_date_time.setAlignment(QtCore.Qt.AlignCenter)
        self.qpbt_record = create_Toggle_button(
            "Click to start recording to file"
        )
        # fmt: off
        self.qpbt_record.clicked.connect(lambda state: log.record(state)) # pylint: disable=unnecessary-lambda
        # fmt: on

        vbox_middle = QtWid.QVBoxLayout()
        vbox_middle.addWidget(self.qlbl_title)
        vbox_middle.addWidget(self.qlbl_cur_date_time)
        vbox_middle.addWidget(self.qpbt_record)

        # Right box
        self.qpbt_exit = QtWid.QPushButton("Exit")
        self.qpbt_exit.clicked.connect(self.close)
        self.qpbt_exit.setMinimumHeight(30)
        self.qlbl_recording_time = QtWid.QLabel(alignment=QtCore.Qt.AlignRight)

        vbox_right = QtWid.QVBoxLayout()
        vbox_right.addWidget(self.qpbt_exit, stretch=0)
        vbox_right.addStretch(1)
        vbox_right.addWidget(self.qlbl_recording_time, stretch=0)

        # Round up top frame
        hbox_top = QtWid.QHBoxLayout()
        hbox_top.addLayout(vbox_left, stretch=0)
        hbox_top.addStretch(1)
        hbox_top.addLayout(vbox_middle, stretch=0)
        hbox_top.addStretch(1)
        hbox_top.addLayout(vbox_right, stretch=0)

        # -------------------------
        #   Bottom frame
        # -------------------------

        #  Charts
        # -------------------------

        self.gw = pg.GraphicsLayoutWidget()

        # Plot: Julabo temperatures
        p = {"color": "#EEE", "font-size": "10pt"}
        self.pi_julabo = self.gw.addPlot(row=0, col=0)
        self.pi_julabo.setLabel("left", text="temperature (°C)", **p)

        # Plot: Arduino temperatures
        self.pi_temp = self.gw.addPlot(row=1, col=0)
        self.pi_temp.setLabel("left", text="temperature (°C)", **p)

        # Plot: Arduino humidity
        self.pi_humi = self.gw.addPlot(row=2, col=0)
        self.pi_humi.setLabel("left", text="humidity (%)", **p)

        # Plot: Arduino pressure
        self.pi_pres = self.gw.addPlot(row=3, col=0)
        self.pi_pres.setLabel("left", text="pressure (mbar)", **p)

        self.plots = [self.pi_julabo, self.pi_temp, self.pi_humi, self.pi_pres]
        for plot in self.plots:
            plot.setClipToView(True)
            plot.showGrid(x=1, y=1)
            plot.setLabel("bottom", text="history (s)", **p)
            plot.setMenuEnabled(True)
            plot.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
            plot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            plot.setAutoVisible(y=True)
            plot.setRange(xRange=[-CHART_HISTORY_TIME, 0])

        # Curves
        capacity = round(CHART_HISTORY_TIME * 1e3 / DAQ_INTERVAL_MS)
        PEN_01 = pg.mkPen(color=[255, 255, 0], width=3)
        PEN_02 = pg.mkPen(color=[252, 15, 192], width=3)
        PEN_03 = pg.mkPen(color=[0, 255, 255], width=3)
        PEN_04 = pg.mkPen(color=[255, 255, 255], width=3)
        PEN_05 = pg.mkPen(color=[255, 127, 39], width=3)
        PEN_06 = pg.mkPen(color=[0, 255, 0], width=3)

        self.tscurve_julabo_setp = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_julabo.plot(pen=PEN_05, name="Julabo setp."),
        )

        self.tscurve_julabo_bath = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_julabo.plot(pen=PEN_06, name="Julabo bath"),
        )

        self.tscurve_ds_temp = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_temp.plot(pen=PEN_01, name="DS temp."),
        )
        self.tscurve_bme_temp = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_temp.plot(pen=PEN_02, name="BME temp."),
        )
        self.tscurve_bme_humi = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_humi.plot(pen=PEN_03, name="BME humi."),
        )
        self.tscurve_bme_pres = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.pi_pres.plot(pen=PEN_04, name="BME pres."),
        )

        self.tscurves = [
            self.tscurve_julabo_setp,
            self.tscurve_julabo_bath,
            self.tscurve_ds_temp,
            self.tscurve_bme_temp,
            self.tscurve_bme_humi,
            self.tscurve_bme_pres,
        ]

        #  Group `Readings`
        # -------------------------

        legend = LegendSelect(
            linked_curves=self.tscurves, hide_toggle_button=True
        )

        p = {
            "readOnly": True,
            "alignment": QtCore.Qt.AlignRight,
            "maximumWidth": 54,
        }
        self.qlin_ds_temp = QtWid.QLineEdit(**p)
        self.qlin_bme_temp = QtWid.QLineEdit(**p)
        self.qlin_bme_humi = QtWid.QLineEdit(**p)
        self.qlin_bme_pres = QtWid.QLineEdit(**p)

        # fmt: off
        legend.grid.setHorizontalSpacing(6)
        legend.grid.addWidget(self.qlin_ds_temp       , 2, 2)
        legend.grid.addWidget(QtWid.QLabel("± 0.5 °C"), 2, 3)
        legend.grid.addWidget(self.qlin_bme_temp      , 3, 2)
        legend.grid.addWidget(QtWid.QLabel("± 0.5 °C"), 3, 3)
        legend.grid.addWidget(self.qlin_bme_humi      , 4, 2)
        legend.grid.addWidget(QtWid.QLabel("± 3 %")   , 4, 3)
        legend.grid.addWidget(self.qlin_bme_pres      , 5, 2)
        legend.grid.addWidget(QtWid.QLabel("± 1 mbar"), 5, 3)
        # fmt: on

        qgrp_readings = QtWid.QGroupBox("Readings")
        qgrp_readings.setLayout(legend.grid)

        #  Group 'Log comments'
        # -------------------------

        self.qtxt_comments = QtWid.QTextEdit()
        grid = QtWid.QGridLayout()
        grid.addWidget(self.qtxt_comments, 0, 0)

        qgrp_comments = QtWid.QGroupBox("Log comments")
        qgrp_comments.setLayout(grid)

        #  Group 'Charts'
        # -------------------------

        self.plot_manager = PlotManager(parent=self)
        self.plot_manager.add_autorange_buttons(linked_plots=self.plots)
        self.plot_manager.add_preset_buttons(
            linked_plots=self.plots,
            linked_curves=self.tscurves,
            presets=[
                {
                    "button_label": "01:00",
                    "x_axis_label": "history (sec)",
                    "x_axis_divisor": 1,
                    "x_axis_range": (-60, 0),
                },
                {
                    "button_label": "10:00",
                    "x_axis_label": "history (min)",
                    "x_axis_divisor": 60,
                    "x_axis_range": (-10, 0),
                },
                {
                    "button_label": "30:00",
                    "x_axis_label": "history (min)",
                    "x_axis_divisor": 60,
                    "x_axis_range": (-30, 0),
                },
                {
                    "button_label": "60:00",
                    "x_axis_label": "history (min)",
                    "x_axis_divisor": 60,
                    "x_axis_range": (-60, 0),
                },
                {
                    "button_label": "120:00",
                    "x_axis_label": "history (min)",
                    "x_axis_divisor": 60,
                    "x_axis_range": (-120, 0),
                },
            ],
        )
        self.plot_manager.add_clear_button(linked_curves=self.tscurves)
        self.plot_manager.perform_preset(1)

        qgrp_chart = QtWid.QGroupBox("Charts")
        qgrp_chart.setLayout(self.plot_manager.grid)

        vbox = QtWid.QVBoxLayout()
        vbox.addWidget(qgrp_readings)
        vbox.addWidget(qgrp_comments)
        vbox.addWidget(qgrp_chart, alignment=QtCore.Qt.AlignLeft)
        vbox.addStretch()

        # Round up bottom frame
        hbox_bot = QtWid.QHBoxLayout()
        hbox_bot.addWidget(self.gw, 1)
        hbox_bot.addLayout(vbox, 0)
        hbox_bot.addWidget(
            qdev_julabo.grpb, alignment=QtCore.Qt.AlignTop, stretch=0
        )

        # -------------------------
        #   Round up full window
        # -------------------------

        vbox = QtWid.QVBoxLayout(self)
        vbox.addLayout(hbox_top, stretch=0)
        vbox.addSpacerItem(QtWid.QSpacerItem(0, 10))
        vbox.addLayout(hbox_bot, stretch=1)

    # --------------------------------------------------------------------------
    #   Handle controls
    # --------------------------------------------------------------------------

    @Slot()
    def update_GUI(self):
        str_cur_date, str_cur_time, _ = get_current_date_time()
        self.qlbl_cur_date_time.setText(
            "%s    %s" % (str_cur_date, str_cur_time)
        )
        self.qlbl_update_counter.setText("%i" % qdev_ard.update_counter_DAQ)
        self.qlbl_DAQ_rate.setText(
            "DAQ: %.1f Hz" % qdev_ard.obtained_DAQ_rate_Hz
        )
        if log.is_recording():
            self.qlbl_recording_time.setText(log.pretty_elapsed())

        self.qlin_ds_temp.setText("%.1f" % state.ds_temp)
        self.qlin_bme_temp.setText("%.1f" % state.bme_temp)
        self.qlin_bme_humi.setText("%.1f" % state.bme_humi)
        self.qlin_bme_pres.setText("%.1f" % state.bme_pres)

    @Slot()
    def update_chart(self):
        if DEBUG:
            tprint("update_chart")

        for tscurve in self.tscurves:
            tscurve.update()


# ------------------------------------------------------------------------------
#   Program termination routines
# ------------------------------------------------------------------------------


def stop_running():
    app.processEvents()
    qdev_ard.quit()
    qdev_julabo.quit()
    log.close()

    print("Stopping timers................ ", end="")
    timer_GUI.stop()
    timer_charts.stop()
    print("done.")


@Slot()
def notify_connection_lost():
    stop_running()

    window.qlbl_title.setText("! ! !    LOST CONNECTION    ! ! !")
    str_cur_date, str_cur_time, _ = get_current_date_time()
    str_msg = "%s %s\nLost connection to Arduino." % (
        str_cur_date,
        str_cur_time,
    )
    print("\nCRITICAL ERROR @ %s" % str_msg)
    reply = QtWid.QMessageBox.warning(
        window, "CRITICAL ERROR", str_msg, QtWid.QMessageBox.Ok
    )

    if reply == QtWid.QMessageBox.Ok:
        pass  # Leave the GUI open for read-only inspection by the user


@Slot()
def about_to_quit():
    print("\nAbout to quit")
    stop_running()
    ard.close()


# ------------------------------------------------------------------------------
#   Your Arduino update function
# ------------------------------------------------------------------------------


def DAQ_function():
    # Date-time keeping
    str_cur_date, str_cur_time, str_cur_datetime = get_current_date_time()

    # Query the Arduino for its state
    success, tmp_state = ard.query_ascii_values("?", delimiter="\t")
    if not (success):
        dprint(
            "'%s' reports IOError @ %s %s"
            % (ard.name, str_cur_date, str_cur_time)
        )
        return False

    # Parse readings into separate state variables
    try:
        (
            state.time,
            state.ds_temp,
            state.bme_temp,
            state.bme_humi,
            state.bme_pres,
        ) = tmp_state
        state.time /= 1000  # Arduino time, [msec] to [s]
        state.bme_pres /= 100  # [Pa] to [mbar]
    except Exception as err:
        pft(err, 3)
        dprint(
            "'%s' reports IOError @ %s %s"
            % (ard.name, str_cur_date, str_cur_time)
        )
        return False

    # Catch very intermittent DS18B20 sensor errors
    if state.ds_temp <= -127.0:
        state.ds_temp = np.nan

    # We will use PC time instead
    state.time = time.perf_counter()

    # Add readings to chart histories
    window.tscurve_julabo_setp.appendData(state.time, julabo.state.setpoint)
    window.tscurve_julabo_bath.appendData(state.time, julabo.state.bath_temp)
    window.tscurve_ds_temp.appendData(state.time, state.ds_temp)
    window.tscurve_bme_temp.appendData(state.time, state.bme_temp)
    window.tscurve_bme_humi.appendData(state.time, state.bme_humi)
    window.tscurve_bme_pres.appendData(state.time, state.bme_pres)

    # Logging to file
    log.update(filepath=str_cur_datetime + ".txt", mode="w")

    # Return success
    return True


def write_header_to_log():
    log.write("[HEADER]\n")
    log.write(window.qtxt_comments.toPlainText())
    log.write("\n\n[DATA]\n")
    log.write("[s]\t[±0.5 °C]\t[±0.5 °C]\t[±3 pct]\t[±1 mbar]\t[°C]\t[°C]\n")
    log.write(
        "time\tDS_temp\tBME_temp\tBME_humi\tBME_pres\tJulabo_setp\tJulabo_bath\n"
    )


def write_data_to_log():
    log.write(
        "%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.2f\t%.2f\n"
        % (
            log.elapsed(),
            state.ds_temp,
            state.bme_temp,
            state.bme_humi,
            state.bme_pres,
            julabo.state.setpoint,
            julabo.state.bath_temp,
        )
    )


# ------------------------------------------------------------------------------
#   Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Set priority of this process to maximum in the operating system
    print("PID: %s\n" % os.getpid())
    try:
        proc = psutil.Process(os.getpid())
        if os.name == "nt":
            proc.nice(psutil.REALTIME_PRIORITY_CLASS)  # Windows
        else:
            proc.nice(-20)  # Other
    except:
        print("Warning: Could not set process to maximum priority.\n")

    # --------------------------------------------------------------------------
    #   Connect to devices
    # --------------------------------------------------------------------------

    # Arduino
    ard = Arduino(name="Ard", connect_to_specific_ID="Dodecahedron logger")
    ard.serial_settings["baudrate"] = 115200
    ard.auto_connect(filepath_last_known_port="config/port_Arduino.txt")

    if not (ard.is_alive):
        print("\nCheck connection and try resetting the Arduino.")
        print("Exiting...\n")
        sys.exit(0)

    # Julabo
    julabo = Julabo_circulator(name="Julabo")
    if julabo.auto_connect(filepath_last_known_port="config/port_Julabo.txt"):
        julabo.begin()

    # --------------------------------------------------------------------------
    #   Create application
    # --------------------------------------------------------------------------
    QtCore.QThread.currentThread().setObjectName("MAIN")  # For DEBUG info

    app = QtWid.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Arial", 9))
    app.aboutToQuit.connect(about_to_quit)

    # --------------------------------------------------------------------------
    #   Set up multithreaded communication with the devices
    # --------------------------------------------------------------------------

    # Arduino
    qdev_ard = QDeviceIO(ard)
    qdev_ard.create_worker_DAQ(
        DAQ_function=DAQ_function,
        DAQ_interval_ms=DAQ_INTERVAL_MS,
        critical_not_alive_count=3,
        debug=DEBUG,
    )

    # Julabo
    qdev_julabo = Julabo_circulator_qdev(
        dev=julabo, DAQ_interval_ms=DAQ_INTERVAL_MS, debug=DEBUG
    )

    # --------------------------------------------------------------------------
    #   Create GUI
    # --------------------------------------------------------------------------

    window = MainWindow()

    # Connect signals
    qdev_ard.signal_DAQ_updated.connect(window.update_GUI)
    qdev_ard.signal_connection_lost.connect(notify_connection_lost)

    # --------------------------------------------------------------------------
    #   File logger
    # --------------------------------------------------------------------------

    log = FileLogger(
        write_header_function=write_header_to_log,
        write_data_function=write_data_to_log,
    )
    log.signal_recording_started.connect(
        lambda filepath: window.qpbt_record.setText(
            "Recording to file: %s" % filepath
        )
    )
    log.signal_recording_stopped.connect(
        lambda: window.qpbt_record.setText("Click to start recording to file")
    )

    # --------------------------------------------------------------------------
    #   Timers
    # --------------------------------------------------------------------------

    timer_GUI = QtCore.QTimer()
    timer_GUI.timeout.connect(window.update_GUI)
    timer_GUI.start(100)

    timer_charts = QtCore.QTimer()
    timer_charts.timeout.connect(window.update_chart)
    timer_charts.start(CHART_INTERVAL_MS)

    # --------------------------------------------------------------------------
    #   Start the main GUI event loop
    # --------------------------------------------------------------------------

    qdev_ard.start()
    qdev_julabo.start()

    window.show()
    if QT_LIB in (PYQT5, PYSIDE2):
        sys.exit(app.exec_())
    else:
        sys.exit(app.exec())
