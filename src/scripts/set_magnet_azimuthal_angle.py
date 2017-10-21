"""
    This file is part of b26_toolkit, a PyLabControl add-on for experiments in Harvard LISE B26.
    Copyright (C) <2016>  Arthur Safira, Jan Gieseler, Aaron Kabcenell

    b26_toolkit is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    b26_toolkit is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with b26_toolkit.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
# from b26_toolkit.src.instruments.thorlabs_servo_controller import KDC101
from b26_toolkit.src.instruments.dcservo_kinesis_dll import KDC101
from PyLabControl.src.core import Script, Parameter

class SetMagnetAzimuthalAngle(Script):
    """
    This script sets magnet azimuthal angle via rotation stage controlled by KDC101
    """

    _DEFAULT_SETTINGS = [
        Parameter('azimuthal_angle', 0, float, 'azimuthal angle to set'),
        Parameter('azimuthal_angular_speed', 0, float, 'azimuthal angle to set')
    ]

    _INSTRUMENTS = {'KDC101':  KDC101}

    _SCRIPTS = {}


    def __init__(self, instruments = None, scripts = None, name = None, settings = None, log_function = None, data_path = None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts,
                        log_function= log_function, data_path = data_path)
        self.azimuth_controller = self.instruments['KDC101']['instance']

    def _function(self):
        angle = (self.settings['azimuthal_angle'] + 360) % 360
        self.azimuth_controller._move_servo(angle, self.settings['azimuthal_angular_speed'])
        self.log('magnet azimuthal angle set to {:}deg'.format(self.settings['azimuthal_angle']))
