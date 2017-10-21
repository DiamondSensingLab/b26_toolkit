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
import time

from b26_toolkit.src.instruments import NI6259
from PyLabControl.src.core import Script, Parameter


class SetMagnetDistance(Script):
    """
This script moves the magnet by a certain distance in a specified direction
    """

    _DEFAULT_SETTINGS = [
        Parameter('dir_channel', 'do1', ['do0','do1','do2','do3'], 'digital output channel to set motor direction'),
        Parameter('enable_channel', 'do0', ['do0', 'do1', 'do2', 'do3'], 'digital output channel to set motor enable'),
        Parameter('pulse_channel', 'ctr1', ['ctr0','ctr1'], 'digital output channel to pulse motor'),
        Parameter('n_pulses', 10, int, 'number of drive pulses to send to motor'),
        Parameter('pulse_rate', 2, [0,0.01,0.02,0.05,0.1,0.2,0.5,1,2], 'pulse rate in kHz'),
        Parameter('direction', 1, [0,1], 'direction to move the magnet (0)=towards sample, (1)=away from sample'),
    ]

    _INSTRUMENTS = {'NI6259':  NI6259}

    _SCRIPTS = {}


    def __init__(self, instruments = None, scripts = None, name = None, settings = None, log_function = None, data_path = None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts, log_function= log_function, data_path = data_path)
        self.daq_out = self.instruments['NI6259']['instance']

    def _function(self):
        DutyCycle = 0.5;
        """
        This is the actual function that will be executed. It uses only information that is provided in the settings property
        will be overwritten in the __init__
        """

        # DAQ digital task for setting motor direction
        task = self.daq_out.setup_DO([self.settings['dir_channel']])
        self.daq_out.run(task)
        self.daq_out.DO_write(task, [self.settings['direction']])
        self.daq_out.stop(task)

        # DAQ digital task to enable motor driver:
        task = self.daq_out.setup_DO([self.settings['enable_channel']])
        self.daq_out.run(task)
        self.daq_out.DO_write(task, [1])
        self.daq_out.stop(task)

        self.daq_out.output_N_dig_pulses(self.settings['n_pulses'], self.settings['pulse_rate'], DutyCycle, self.settings['pulse_channel'])

        # DAQ digital task to disable motor driver:
        task = self.daq_out.setup_DO([self.settings['enable_channel']])
        self.daq_out.run(task)
        self.daq_out.DO_write(task, [0])
        self.daq_out.stop(task)

        self.log('magnet displaced by {:} pulses at {:}kHz'.format(self.settings['n_pulses'], self.settings['pulse_rate']))
