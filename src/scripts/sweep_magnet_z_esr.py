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
from b26_toolkit.src.instruments.dcservo_kinesis_dll import TDC001
from PyLabControl.src.core import Script, Parameter
from copy import deepcopy
from b26_toolkit.src.plotting.plots_1d import plot_BsweepESR

from esr import ESR

class SweepMagnetZ_ESR(Script):
    """
    This script sweeps magnet azimuthal angle via rotation stage controlled by KDC101, and takes ESR at each step
    """

    _DEFAULT_SETTINGS = [
        Parameter('sweep_center', 20, float, 'magnet Z - sweep center [mm]'),
        Parameter('sweep_range', 10, float, 'magnet Z - sweep range [mm]'),
        Parameter('sweep_points', 10, float, 'number of points in sweep'),
        Parameter('move_speed_coarse', 1, float, 'mm/sec'),
        Parameter('move_speed_fine', 0.2, float, 'mm/sec')
    ]

    _INSTRUMENTS = {'TDC001':  TDC001}

    _SCRIPTS = {'esr':ESR}


    def __init__(self, instruments = None, scripts = None, name = None, settings = None, log_function = None, data_path = None):
        """
        Example of a script that emits a QT signal for the gui
        Args:
            name (optional): name of script, if empty same as class name
            settings (optional): settings for this script, if empty same as default settings
        """
        Script.__init__(self, name, settings = settings, instruments = instruments, scripts = scripts, log_function= log_function, data_path = data_path)
        self.z_mag_controller = self.instruments['TDC001']['instance']

    def _function(self):

        self.initial_before_sweep =  self.z_mag_controller._get_position()
        self.sweep_start = self.settings['sweep_center'] - self.settings['sweep_range'] / 2.
        self.sweep_stop = self.settings['sweep_center'] + self.settings['sweep_range'] / 2.
        self.sweep_array = np.linspace(self.sweep_start, self.sweep_stop, self.settings['sweep_points'], endpoint=True)

        self.data = {'magnet_z': self.sweep_array,
                     'esr_data': [],
                     'esr_params': {'magnet_z_plot': [], 'f0':[], 'contrast':[], 'mean_fluor':[],'fwhm':[],
                                    'magnet_z_plot_2': [], 'f0_2': [], 'contrast_2': [], 'mean_fluor_2': [], 'fwhm_2': []}}

        # Move quickly to sweep_start:
        self.z_mag_controller._move_servo(self.sweep_start, self.settings['move_speed_coarse'])
        self.log('magnet Z sweep started at {:}mm from bottom'.format(self.sweep_start))

        # Perform sweep over magnet z taking CW ESR at each point
        for sweep_index in range(len(self.sweep_array)):
            self.z_mag_controller._move_servo(self.sweep_array[sweep_index], self.settings['move_speed_fine'])
            print('doing ESR at magnet Z={:}'.format(self.sweep_array[sweep_index]))
            self.scripts['esr'].run()

            # copy data from ESR script after it finishes:
            esr_data = deepcopy(self.scripts['esr'].data)
            self.data['esr_data'].append(esr_data)

            # compose vectors of f0 and contrast esr parameters vs sweep for esr traces where fit succeeded:
            if esr_data['fit_params'] is not None:
                print('esr fit params:')
                print(esr_data['fit_params'])
                self.data['esr_params']['magnet_z_plot'].append(self.sweep_array[sweep_index])
                if len(esr_data['fit_params'])==4:
                    self.data['esr_params']['f0'].append(esr_data['fit_params'][2])
                    self.data['esr_params']['contrast'].append(-esr_data['fit_params'][1])
                elif len(esr_data['fit_params'])==6:
                    self.data['esr_params']['magnet_z_plot_2'].append(self.sweep_array[sweep_index])
                    self.data['esr_params']['f0'].append(esr_data['fit_params'][4])
                    self.data['esr_params']['contrast'].append(-esr_data['fit_params'][2])
                    self.data['esr_params']['f0_2'].append(esr_data['fit_params'][5])
                    self.data['esr_params']['contrast_2'].append(-esr_data['fit_params'][3])
            self.updateProgress.emit(float(sweep_index)/(len(self.sweep_array)-1)*100)
            if self._abort:
                break

        # Move quickly then slowly back to initial position:
        self.z_mag_controller._move_servo(self.initial_before_sweep, self.settings['move_speed_coarse'])
        self.z_mag_controller._move_servo(self.initial_before_sweep, self.settings['move_speed_fine'])
        self.log('magnet Z brought back to {:}mm from bottom'.format(self.initial_before_sweep))

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
                lbls = ['magnet Z [mm]', 'f0 [Hz]', 'contrast']
                plot_BsweepESR([axes_list[0],axes_list[2]],
                               [self.data['esr_params']['magnet_z_plot'],self.data['esr_params']['magnet_z_plot_2']],
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
            if self.data is not None and self.data['esr_params']['magnet_z_plot'] is not None:
                lbls = ['magnet Z [mm]', 'f0 [Hz]', 'contrast']
                plot_BsweepESR([axes_list[0],axes_list[2]],
                               [self.data['esr_params']['magnet_z_plot'],self.data['esr_params']['magnet_z_plot_2']],
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