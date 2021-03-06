"""
    This file is part of b26_toolkit, a PyLabControl add-on for experiments in Harvard LISE B26.
    Copyright (C) <2016>  Arthur Safira, Jan Gieseler, Aaron Kabcenell

    Foobar is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Foobar is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
from collections import deque

from b26_toolkit.src.instruments import NI6259
from b26_toolkit.src.plotting.plots_1d import plot_counts
from PyLabControl.src.core import Parameter, Script
from b26_toolkit.src.instruments import CN041PulseBlaster


class Daq_Read_Counter(Script):
    """
This script reads the Counter input from the DAQ and plots it.
    """
    _DEFAULT_SETTINGS = [
        Parameter('integration_time', .25, float, 'Time per data point'),
        Parameter('counter_channel', 'ctr0', ['ctr0', 'ctr1'], 'Daq channel used for counter')
    ]

    _INSTRUMENTS = {'daq': NI6259, 'PB': CN041PulseBlaster}

    _SCRIPTS = {

    }

    def __init__(self, instruments, scripts=None, name=None, settings=None, log_function=None, data_path=None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings=settings, scripts=scripts, instruments=instruments,
                        log_function=log_function, data_path=data_path)

        self.data = {'counts': deque(), 'time': deque()}


    def _function(self):
        """
        This is the actual function that will be executed. It uses only information that is provided in the settings property
        will be overwritten in the __init__
        """
        # turn laser on
        self.instruments['PB']['instance'].update({'laser': {'status': True}})

        sample_rate = float(1) / self.settings['integration_time']
        normalization = self.settings['integration_time']/.001
        self.instruments['daq']['instance'].settings['digital_input'][self.settings['counter_channel']]['sample_rate'] = sample_rate

        self.data = {'counts': deque(), 'time': deque()}

        self.last_value = 0

        sample_num = 2

        task = self.instruments['daq']['instance'].setup_counter("ctr0", sample_num, continuous_acquisition=True)

        # start counter and scanning sequence
        self.instruments['daq']['instance'].run(task)

        # starting point for keeping track of time in seconds:
        start_time = time.time()
        while True:
            if self._abort:
                break



            # TODO: this is currently a nonblocking read so we add a time.sleep at the end so it doesn't read faster
            # than it acquires, this should be replaced with a blocking read in the future
            raw_data, num_read = self.instruments['daq']['instance'].read(task)
            #skip first read, which gives an anomolous value
            if num_read.value == 1:
                self.last_value = raw_data[0] #update running value to last measured value to prevent count spikes
                time.sleep(2.0 / sample_rate)
                continue
            print('raw data length: ', len(raw_data))
            self.data['time'].append(time.time() - start_time)
            self.data['time'].append(self.data['time'][-1] + 1 / sample_rate)
            for value in raw_data:
                self.data['counts'].append(((float(value) - self.last_value) / normalization))
                self.last_value = value


            self.progress = 50.
            self.updateProgress.emit(int(self.progress))

            time.sleep(2.0 / sample_rate)

        # clean up APD tasks
        self.instruments['daq']['instance'].stop(task)

        # turn laser off
        self.instruments['PB']['instance'].update({'laser': {'status': False}})
        self.log('Laser is off.')

    def plot(self, figure_list):
        # COMMENT_ME
        super(Daq_Read_Counter, self).plot([figure_list[1]])

    def _plot(self, axes_list, data = None):
        # COMMENT_ME

        if data is None:
            data = self.data

        if data:
            plot_counts(axes_list[0], data['counts'], data['time'],'time [sec]')

if __name__ == '__main__':
    script = {}
    instr = {}
    script, failed, instr = Script.load_and_append({'Daq_Read_Cntr': 'Daq_Read_Cntr'}, script, instr)

    print(script)
    print(failed)
    print(instr)