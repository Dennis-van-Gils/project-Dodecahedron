.. image:: https://requires.io/github/Dennis-van-Gils/project-Dodecahedron/requirements.svg?branch=main
    :target: https://requires.io/github/Dennis-van-Gils/project-Dodecahedron/requirements/?branch=main
    :alt: Requirements Status
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/License-MIT-purple.svg
    :target: https://github.com/Dennis-van-Gils/project-Dodecahedron/blob/master/LICENSE.txt

Twente Dodecahedron
===================
*A Physics of Fluids project.*

Control program for the Twente Dodecahedron: a scientific setup in order to
study isotropic droplet-laden turbulence. This program logs the temperature
and humidity readings and it controls the circulating bath that is connected to
the setup's heat exhanging plates.

- Github: https://github.com/Dennis-van-Gils/project-Dodecahedron

.. image:: https://raw.githubusercontent.com/Dennis-van-Gils/project-Dodecahedron/master/images/screenshot.png

Hardware
========
* Adafruit #3857: Adafruit Feather M4 Express - Featuring ATSAMD51 Cortex M4
* Adafruit #381: Waterproof 1-Wire DS18B20 Compatible Digital temperature sensor
* Pimoroni PIM472: BME280 Breakout - Temperature, Pressure, Humidity Sensor
* Julabo FP51-SL: Ultra-Low Refrigerated / Heating Circulator

Instructions
============
Download the `latest release <https://github.com/Dennis-van-Gils/project-Dodecahedron/releases/latest>`_
and unpack to a folder onto your drive.

Flashing the firmware
---------------------

Double click the reset button of the Feather while plugged into your PC. This
will mount a drive called `FEATHERBOOT`. Copy
`src_mcu/_build_Feather_M4/CURRENT.UF2 <https://github.com/Dennis-van-Gils/project-Dodecahedron/raw/main/src_mcu/_build_Feather_M4/CURRENT.UF2>`_
onto the Featherboot drive. It will restart automatically with the new
firmware.

Running the application
-----------------------

Preferred Python distributions:
    * `Anaconda <https://www.anaconda.com>`_
    * `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_

Open `Anaconda Prompt` and navigate to the unpacked folder. Run the following to
install the necessary packages: ::

    cd src_python
    pip install -r requirements.txt
    
Now you can run the application: ::

    python main.py

LED status lights
=================

* Solid blue: Booting and setting up
* Solid green: Ready for communication
* Flashing green: Sensor data is being send over USB
