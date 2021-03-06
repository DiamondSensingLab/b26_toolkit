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

from PyLabControl.src.core import Script
from b26_toolkit.src.scripts import ESR
from b26_toolkit.src.scripts.pulse_blaster_scripts_CN041 import Rabi


class ESRAndRabi(Script):
    """
    Does both an ESR experiment and a Rabi experiment on an NV, using the reference frequency from the esr data.
    """

    _DEFAULT_SETTINGS = []

    _INSTRUMENTS = {}

    _SCRIPTS = {'esr': ESR, 'rabi': Rabi}

    def __init__(self, scripts, name = None, settings = None, log_function = None, timeout = 1000000000, data_path = None):

        Script.__init__(self, name, scripts = scripts, settings=settings, log_function=log_function, data_path = data_path)


    def _function(self):

        self.scripts['esr'].run()

        if self.scripts['esr'].data['fit_params'] is not None:
            if len(self.scripts['esr'].data['fit_params']) == 4:
                self.rabi_frequency = self.scripts['esr'].data['fit_params'][2]
            elif len(self.scripts['esr'].data['fit_params']) == 6:
                self.rabi_frequency = self.scripts['esr'].data['fit_params'][4]
            else:
                raise RuntimeError('Could not get fit parameters from esr script')

            if self.rabi_frequency < self.scripts['esr'].settings['freq_start']:
                self.log('Resonance frequency found ({:0.2e}) was below esr sweep range, aborting rabi attempt'.format(self.rabi_frequency))
            elif self.rabi_frequency > self.scripts['esr'].settings['freq_stop']:
                self.log('Resonance frequency found ({:0.2e}) was above esr sweep range, aborting rabi attempt'.format(self.rabi_frequency))
            else:
                self.log('Starting rabi with frequency {:.4e} Hz'.format(self.rabi_frequency))
                self.scripts['rabi'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                self.scripts['rabi'].run()
        else:
            self.log('No resonance frequency found skipping rabi attempt')

