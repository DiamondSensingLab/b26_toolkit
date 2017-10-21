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
from PyLabControl.src.core import Script, Parameter
from copy import deepcopy
from b26_toolkit.src.plotting.plots_1d import plot_BsweepESR
from set_magnet_distance import SetMagnetDistance

from esr import ESR

class SweepMagnetDistance_ESR(Script):
    """
    This script sets magnet azimuthal angle via rotation stage controlled by KDC101
    """

    _DEFAULT_SETTINGS = [
        Parameter('sweep_range', 1000, float, 'total number of pulses to apply'),
        Parameter('center_on_current', False, [True,False], 'sweep centered on current position'),
        Parameter('return_to_initial', False, [True, False], 'return to initial position'),
        Parameter('sweep_points', 10, float, 'number of points in sweep'),
        Parameter('move_speed_coarse', 2, [0,0.01,0.02,0.05,0.1,0.2,0.5,1,2], 'pulse rate in kHz'),
        Parameter('move_speed_fine', 0.2, [0,0.01,0.02,0.05,0.1,0.2,0.5,1,2], 'pulse rate in kHz'),
        Parameter('direction', 1, [0,1], 'direction to move the magnet (0)=towards sample, (1)=away from sample'),
        Parameter('hysteresis_adj', 1, float, 'scaling factor for actual distance travelled towards/away for the same number of pulses')
    ]

    _INSTRUMENTS = {}

    _SCRIPTS = {'esr':ESR, 'set_mag_d': SetMagnetDistance}


    def __init__(self, instruments = None, scripts = None, name = None, settings = None, log_function = None, data_path = None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts, log_function= log_function, data_path = data_path)

    def _function(self):

        self.sweep_array = np.linspace(0, self.settings['sweep_range'], self.settings['sweep_points'], endpoint=True)

        self.data = {'magnet_z': self.sweep_array,
                     'esr_data': [],
                     'esr_params': {'magnet_dist_plot': [], 'f0':[], 'contrast':[], 'mean_fluor':[],'fwhm':[],
                                    'magnet_dist_plot_2': [], 'f0_2': [], 'contrast_2': [], 'mean_fluor_2': [], 'fwhm_2': []}}

        # Move quickly to sweep_start:
        if self.settings['center_on_current']:
            # pulse in reverse direction from chosen for half of the sweep range to get to start point
            self.scripts['set_mag_d'].settings['direction'] = int(not self.settings['direction'])
            self.scripts['set_mag_d'].settings['pulse_rate'] = self.settings['move_speed_coarse']
            self.scripts['set_mag_d'].settings['n_pulses'] = int(np.power(self.settings['hysteresis_adj'],int(not self.settings['direction']))*self.settings['sweep_range']/2)
            self.scripts['set_mag_d'].run()

        self.scripts['set_mag_d'].settings['direction'] = self.settings['direction']
        self.scripts['set_mag_d'].settings['pulse_rate'] = self.settings['move_speed_fine']
        self.scripts['set_mag_d'].settings['n_pulses'] = int(np.power(self.settings['hysteresis_adj'],int(self.settings['direction']))*self.settings['sweep_range'] / (self.settings['sweep_points']-1))

        self.log('magnet distance sweep started')

        # Perform sweep over magnet z taking CW ESR at each point
        for sweep_index in range(len(self.sweep_array)):
            if sweep_index > 0:
                self.scripts['set_mag_d'].run()

            print('doing ESR at mag distance {:}'.format(sweep_index))
            self.scripts['esr'].run()

            # copy data from ESR script after it finishes:
            esr_data = deepcopy(self.scripts['esr'].data)
            self.data['esr_data'].append(esr_data)

            # compose vectors of f0 and contrast esr parameters vs sweep for esr traces where fit succeeded:
            if esr_data['fit_params'] is not None:
                print('esr fit params:')
                print(esr_data['fit_params'])
                self.data['esr_params']['magnet_dist_plot'].append(self.sweep_array[sweep_index])
                if len(esr_data['fit_params'])==4:
                    self.data['esr_params']['f0'].append(esr_data['fit_params'][2])
                    self.data['esr_params']['contrast'].append(-esr_data['fit_params'][1])
                elif len(esr_data['fit_params'])==6:
                    self.data['esr_params']['magnet_dist_plot_2'].append(self.sweep_array[sweep_index])
                    self.data['esr_params']['f0'].append(esr_data['fit_params'][4])
                    self.data['esr_params']['contrast'].append(-esr_data['fit_params'][2])
                    self.data['esr_params']['f0_2'].append(esr_data['fit_params'][5])
                    self.data['esr_params']['contrast_2'].append(-esr_data['fit_params'][3])
            self.updateProgress.emit(float(sweep_index)/(len(self.sweep_array)-1)*100)
            if self._abort:
                break

        # Move quickly back to initial position:
        if self.settings['return_to_initial']:
            self.scripts['set_mag_d'].settings['direction'] = int(not self.settings['direction'])
            self.scripts['set_mag_d'].settings['pulse_rate'] = self.settings['move_speed_coarse']
            if self.settings['center_on_current']:
                # pulse in reverse direction from chosen for half of the sweep range to get to initial point
                self.scripts['set_mag_d'].settings['n_pulses'] = int(np.power(self.settings['hysteresis_adj'],int(not self.settings['direction']))*self.settings['sweep_range']/2)
            else:
                # pulse in reverse direction from chosen for full range to get to initial point
                self.scripts['set_mag_d'].settings['n_pulses'] = int(np.power(self.settings['hysteresis_adj'],int(not self.settings['direction']))*self.settings['sweep_range'])
            self.scripts['set_mag_d'].run()

            self.log('magnet distance brought back to initial')

    def _plot(self, axes_list):
        """
        Args:
            axes_list: list of axes objects on which to plot plots the esr on the first axes object
            data: data (dictionary that contains keys image_data, extent, initial_point, maximum_point) if not provided use self.data
        """

        if self._current_subscript_stage['current_subscript'] is self.scripts['esr'] and self.scripts['esr'].is_running:
            self.scripts['esr']._plot([axes_list[1]])
        else:
            if self.data is not None:
                lbls = ['magnet distance moved [pulses]', 'f0 [Hz]', 'contrast']
                plot_BsweepESR([axes_list[0],axes_list[2]],
                               [self.data['esr_params']['magnet_dist_plot'],self.data['esr_params']['magnet_dist_plot_2']],
                               [self.data['esr_params']['f0'],self.data['esr_params']['f0_2']],
                               [self.data['esr_params']['contrast'],self.data['esr_params']['contrast_2']],
                               lbls)
            else:
                print('no fitted ESR parameters to plot')

    def _update_plot(self, axes_list):
        """
        Args:
            axes_list: list of axes objects on which to plot plots the esr on the first axes object
        """

        if self._current_subscript_stage['current_subscript'] is self.scripts['esr'] and self.scripts['esr'].is_running:
            self.scripts['esr']._update_plot([axes_list[1]])
        else:
            if self.data is not None and self.data['esr_params']['magnet_dist_plot'] is not None:
                lbls = ['magnet distance moved [pulses]', 'f0 [Hz]', 'contrast']
                plot_BsweepESR([axes_list[0],axes_list[2]],
                               [self.data['esr_params']['magnet_dist_plot'],self.data['esr_params']['magnet_dist_plot_2']],
                               [self.data['esr_params']['f0'],self.data['esr_params']['f0_2']],
                               [self.data['esr_params']['contrast'],self.data['esr_params']['contrast_2']],
                               lbls)
            else:
                print('no fitted ESR parameters to plot')

    def get_axes_layout(self, figure_list):
        """
        returns the axes objects the script needs to plot its data
        this overwrites the default get_axis_layout in PyLabControl.src.core.scripts
        Args:
            figure_list: a list of figure objects
        Returns:
            axes_list: a list of axes objects

        """
        axes_list = []
        if self._plot_refresh is True:
            for fig in figure_list:
                fig.clf()

            axes_list.append(figure_list[0].add_subplot(121))
            axes_list.append(figure_list[1].add_subplot(111))
            axes_list.append(figure_list[0].add_subplot(122))

        else:
            axes_list.append(figure_list[0].axes[0])
            axes_list.append(figure_list[1].axes[0])
            axes_list.append(figure_list[0].axes[1])


        return axes_list