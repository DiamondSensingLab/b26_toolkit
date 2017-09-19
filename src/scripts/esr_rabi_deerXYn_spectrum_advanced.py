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

from PyLabControl.src.core import Script, Parameter
from b26_toolkit.src.scripts import ESR
from b26_toolkit.src.scripts.pulse_blaster_scripts_CN041 import Rabi, DEER_XYn, DEER_XYn_RFpwrsw, DEER_XYn_RFfreqsw, DEER_XYn_RFpitimesw
import numpy as np


class EsrRabiDeerXYnSpectrumAdvanced(Script):
    """
    Does an ESR experiment, a Rabi experiment and a DEER experiment on an NV. Can scan over RF power, 
    """

    _DEFAULT_SETTINGS = [
        Parameter('decoupling_seq', [
            Parameter('type', 'XY4', ['spin_echo', 'CPMG', 'XY4', 'XY8'],
                      'type of dynamical decoupling sequences'),
            Parameter('num_of_pulse_blocks', 1, int, 'number of pulse blocks.')
        ]),
        Parameter('DEER_spectrum', [
            Parameter('scan_tau', [
                Parameter('do_scan_tau',True, bool,'check if doing DEER scanning over tau'),
                Parameter('DEER_freq_sweep', [
                    Parameter('RF_center_freq', 224e6, float, 'RF carrier frequency for dark spin [Hz]'),
                    Parameter('do_RF_freq_sweep', False, bool,
                              'check if taking a DEER spectrum by varying RF carrier frequency'),
                    Parameter('RF_freq_sweep_range', 100e6, float, 'RF frequency sweep range [Hz]'),
                    Parameter('RF_freq_sweep_npoints', 11, float, 'RF frequency sweep number of points'),
                ]),
                Parameter('DEER_power_sweep', [
                    Parameter('RF_pwr', -7, float, 'RF pulse power for dark spin [dBm]'),
                    Parameter('do_RF_pwr_sweep', False, bool, 'check if sweeping RF power when doing '),
                    Parameter('RF_pwr_sweep_range', 10, float, 'RF power sweep range [dBm]'),
                    Parameter('RF_pwr_sweep_npoints', 11, float, 'RF power sweep number of points'),
                ])
            ]),
            Parameter('tau_auto_range',[
                Parameter('min_tau_auto',500,float, 'minimum accepted tau_auto'),
                Parameter('max_tau_auto',8000,float, 'maximum accepted tau_auto')
            ]),
            Parameter('scan_RF_freq',[
                Parameter('do_scan_RF_freq', False, bool,'check if doing DEER scanning over RF frequency'),
                Parameter('set_tau','manual',['auto','manual'],
                          'find tau automatically from deer_tau experiment or manually type in tau in the deer_freq subscript')
                ]),

            Parameter('scan_RF_power', [
                Parameter('do_scan_RF_power', False, bool, 'check if doing DEER scanning over RF frequency'),
                Parameter('set_tau', 'manual', ['auto', 'manual'],
                          'find tau automatically from deer_tau experiment or manually type in tau in the deer_pwr subscript')
            ]),

            Parameter('scan_RF_pi_time', [
                Parameter('do_scan_RF_pi_time', False, bool, 'check if doing DEER scanning over RF frequency'),
                Parameter('set_tau', 'manual', ['auto', 'manual'],
                          'find tau automatically from deer_tau experiment or manually type in tau in the deer_RFpitime subscript')
            ])

            # Parameter('scan_RF_freq',True, bool,'check if doing DEER scanning over RF frequency'),
            # Parameter('scan_RF_power', False, bool, 'check if doing DEER scanning over RF power'),
            # Parameter('scan_RF_pi_time', False, bool, 'check if doing DEER scanning over RF pi time')
        ])

    ]

    _INSTRUMENTS = {}

    _SCRIPTS = {'esr': ESR, 'rabi': Rabi, 'deer_tau':DEER_XYn, 'deer_freq': DEER_XYn_RFfreqsw, 'deer_pwr': DEER_XYn_RFpwrsw, 'deer_RFpitime':  DEER_XYn_RFpitimesw}

    def __init__(self, scripts, name = None, settings = None, log_function = None, timeout = 1000000000, data_path = None):

        Script.__init__(self, name, settings = settings, scripts = scripts, log_function= log_function, data_path = data_path)


    def _function(self):

        self.data = {'dummy': 'placeholder'}

        if (self.settings['DEER_spectrum']['scan_RF_power']['do_scan_RF_power'] and ['DEER_spectrum']['scan_RF_power']['set_tau'] == 'auto')  or (self.settings['DEER_spectrum']['scan_RF_freq']['do_scan_RF_freq'] and ['DEER_spectrum']['scan_RF_freq']['set_tau'] == 'auto') or (self.settings['DEER_spectrum']['scan_RF_pi_time']['do_scan_RF_pi_time'] and ['DEER_spectrum']['scan_RF_pi_time']['set_tau'] == 'auto'):
            assert ['DEER_spectrum']['scan_tau']['do_scan_tau'], "run scan_tau to set tau automatically"



        ####### run ESR script
        self.scripts['esr'].run()

        if self.scripts['esr'].data['fit_params'] is not None:
            if len(self.scripts['esr'].data['fit_params']) == 4:
                self.rabi_frequency = self.scripts['esr'].data['fit_params'][2]
            elif len(self.scripts['esr'].data['fit_params']) == 6:
                self.rabi_frequency = self.scripts['esr'].data['fit_params'][4]
            else:
                raise RuntimeError('Could not get fit parameters from esr script')

            centerfreq = self.scripts['esr'].settings['freq_start']
            freqrange = self.scripts['esr'].settings['freq_stop']
            if self.rabi_frequency < centerfreq-freqrange/3:
                self.log('Resonance frequency found ({:0.2e}) was below esr sweep range, aborting rabi attempt'.format(self.rabi_frequency))
            elif self.rabi_frequency > centerfreq+freqrange/3:
                self.log('Resonance frequency found ({:0.2e}) was above esr sweep range, aborting rabi attempt'.format(self.rabi_frequency))
            else:
                ####### run Rabi script
                self.log('Starting RABI with frequency {:.4e} Hz'.format(self.rabi_frequency))
                self.scripts['rabi'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                self.scripts['rabi'].run()

                if self.scripts['rabi'].data['pi_time'] is not None and self.scripts['rabi'].data['pi_half_time'] is not None and self.scripts['rabi'].data['three_pi_half_time'] is not None:
                    #self.scripts['deer'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                    self.pi_time = self.scripts['rabi'].data['pi_time']
                    self.pi_half_time = self.scripts['rabi'].data['pi_half_time']
                    self.three_pi_half_time = self.scripts['rabi'].data['three_pi_half_time']

                    if not (self.pi_half_time>15 and self.pi_time>self.pi_half_time and self.three_pi_half_time>self.pi_time):
                        self.log('Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e}) do not make sense, aborting DEER for this NV'.format(self.pi_half_time,self.pi_time,self.three_pi_half_time))
                    else:
                        ####### run DEER script
                        run_deer = 0


                        if self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']:
                            run_deer = 1
                            self.log('Starting DEER scanning over tau with Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e})'.format(
                                self.pi_half_time, self.pi_time, self.three_pi_half_time))
                            self.scripts['deer_tau'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                            self.scripts['deer_tau'].settings['mw_pulses']['pi_half_pulse_time'] = float(self.pi_half_time)
                            self.scripts['deer_tau'].settings['mw_pulses']['pi_pulse_time'] = float(self.pi_time)
                            self.scripts['deer_tau'].settings['RF_pulses']['RF_pi_pulse_time'] = float(
                                self.pi_time)  # otherwise short pulse
                            self.scripts['deer_tau'].settings['mw_pulses']['3pi_half_pulse_time'] = float(
                                self.three_pi_half_time)
                            self.scripts['deer_tau'].settings['decoupling_seq']['type'] = \
                            self.settings['decoupling_seq']['type']
                            self.scripts['deer_tau'].settings['decoupling_seq']['num_of_pulse_blocks'] = \
                            self.settings['decoupling_seq']['num_of_pulse_blocks']

                            # tag before starting deer sweeps:
                            base_tag_deer = self.scripts['deer_tau'].settings['tag']

                            if self.settings['DEER_spectrum']['scan_tau']['DEER_freq_sweep']['do_RF_freq_sweep']:
                                self.do_deer_freq_sweep()
                            elif self.settings['DEER_spectrum']['scan_tau']['DEER_power_sweep']['do_RF_pwr_sweep']:
                                self.do_deer_pwr_sweep()
                            else:
                                self.scripts['deer_tau'].run()

                            if self.scripts['deer_tau'].data['tau_auto'] is not None:
                                if self.scripts['deer_tau'].data['tau_auto'] < self.settings['DEER_spectrum']['tau_auto_range']['min_tau_auto'] or self.scripts['deer_tau'].data['tau_auto'] > self.settings['DEER_spectrum']['tau_auto_range']['max_tau_auto']:
                                    self.tau_auto = None
                                    self.log('tau_auto is outside acceptable tau_auto_range. use manually set tau instead in subsequent experiments')
                                else:
                                    self.tau_auto = self.scripts['deer_tau'].data['tau_auto']
                            else:
                                self.tau_auto = None
                                self.log('no tau found for good contrast between deer and echo. use manually set tau instead in subsequent experiments')

                            # return to original tag:
                            self.scripts['deer_tau'].settings['tag'] = base_tag_deer

                        if self.settings['DEER_spectrum']['scan_RF_power']['do_scan_RF_power']:
                            run_deer = 1
                            self.log('Starting DEER scanning over RF power with Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e})'.format(
                                    self.pi_half_time, self.pi_time, self.three_pi_half_time))
                            self.scripts['deer_pwr'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                            self.scripts['deer_pwr'].settings['mw_pulses']['pi_half_pulse_time'] = float(
                                self.pi_half_time)
                            self.scripts['deer_pwr'].settings['mw_pulses']['pi_pulse_time'] = float(self.pi_time)
                            self.scripts['deer_pwr'].settings['RF_pulses']['RF_pi_pulse_time'] = float(self.pi_time) # otherwise short pulse
                            self.scripts['deer_pwr'].settings['mw_pulses']['3pi_half_pulse_time'] = float(
                                self.three_pi_half_time)

                            self.scripts['deer_pwr'].settings['decoupling_seq']['type'] = \
                                self.settings['decoupling_seq']['type']
                            self.scripts['deer_pwr'].settings['decoupling_seq']['num_of_pulse_blocks'] = \
                                self.settings['decoupling_seq']['num_of_pulse_blocks']

                            if ['DEER_spectrum']['scan_RF_power']['set_tau'] == 'auto':
                                if self.tau_auto is not None:
                                    self.scripts['deer_pwr'].settings['tau_time'] = float(self.auto)
                                    self.log(
                                        'use tau_auto = ({:0.2e})ns for DEER scan_RF_power'.format(self.tau_auto))
                                else:
                                    self.log('set_tau auto failed, use manually set tau instead')

                            self.scripts['deer_pwr'].run()



                        if self.settings['DEER_spectrum']['scan_RF_freq']['do_scan_RF_freq']:
                            run_deer = 1
                            self.log('Starting DEER scanning over RF frequency with Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e})'.format(
                                    self.pi_half_time, self.pi_time, self.three_pi_half_time))
                            self.scripts['deer_freq'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                            self.scripts['deer_freq'].settings['mw_pulses']['pi_half_pulse_time'] = float(
                                self.pi_half_time)
                            self.scripts['deer_freq'].settings['mw_pulses']['pi_pulse_time'] = float(self.pi_time)
                            self.scripts['deer_freq'].settings['RF_pulses']['RF_pi_pulse_time'] = float(self.pi_time)
                            print('here we are')# otherwise short pulse

                            # if self.scripts['deer_freq'].settings['mw_pulses']['pi_pulse_time'] == self.scripts['deer_freq'].settings['RF_pulses']['RF_pi_pulse_time']:
                            #     print ('same pi time')
                            # else:
                            #     print ('different pi time')


                            self.scripts['deer_freq'].settings['mw_pulses']['3pi_half_pulse_time'] = float(
                                self.three_pi_half_time)
                            self.scripts['deer_freq'].settings['decoupling_seq']['type'] = \
                                self.settings['decoupling_seq']['type']
                            self.scripts['deer_freq'].settings['decoupling_seq']['num_of_pulse_blocks'] = \
                                self.settings['decoupling_seq']['num_of_pulse_blocks']
                            # print('before running')
                            if ['DEER_spectrum']['scan_RF_freq']['set_tau'] == 'auto':
                                if self.tau_auto is not None:
                                    self.scripts['deer_freq'].settings['tau_time'] = float(self.auto)
                                    self.log(
                                        'use tau_auto = ({:0.2e})ns for DEER scan_RF_freq'.format(self.tau_auto))
                                else:
                                    self.log('set_tau auto failed, use manually set tau instead')

                            self.scripts['deer_freq'].run()

                        if self.settings['DEER_spectrum']['scan_RF_pi_time']['do_scan_RF_pi_time']:
                            run_deer = 1
                            self.log('Starting DEER scanning over RF pi time with Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e})'.format(
                                    self.pi_half_time, self.pi_time, self.three_pi_half_time))
                            self.scripts['deer_RFpitime'].settings['mw_pulses']['mw_frequency'] = float(self.rabi_frequency)
                            self.scripts['deer_RFpitime'].settings['mw_pulses']['pi_half_pulse_time'] = float(
                                self.pi_half_time)
                            self.scripts['deer_RFpitime'].settings['mw_pulses']['pi_pulse_time'] = float(self.pi_time)
                            self.scripts['deer_RFpitime'].settings['RF_pulses']['RF_pi_pulse_time'] = float(
                                self.pi_time)  # otherwise short pulse
                            self.scripts['deer_RFpitime'].settings['mw_pulses']['3pi_half_pulse_time'] = float(
                                self.three_pi_half_time)
                            self.scripts['deer_RFpitime'].settings['decoupling_seq']['type'] = \
                                self.settings['decoupling_seq']['type']
                            self.scripts['deer_RFpitime'].settings['decoupling_seq']['num_of_pulse_blocks'] = \
                                self.settings['decoupling_seq']['num_of_pulse_blocks']

                            if ['DEER_spectrum']['scan_RF_pi_time']['set_tau'] == 'auto':
                                if self.tau_auto is not None:
                                    self.scripts['deer_RFpitime'].settings['tau_time'] = float(self.tau_auto)
                                    self.log('use tau_auto = ({:0.2e})ns for DEER scan_RF_pi_time'.format(self.tau_auto))
                                else:
                                    self.log('set_tau auto failed, use manually set tau instead')

                            self.scripts['deer_RFpitime'].run()

                        if run_deer == 0:
                            self.log('No DEER measurement selected.')
                            ####### run DEER script
                        # self.log('Starting DEER sweeps with Pi/2=({:0.2e}), Pi=({:0.2e}), 3Pi/2=({:0.2e})'.format(self.pi_half_time, self.pi_time, self.three_pi_half_time))
                        # self.scripts['deer'].settings['mw_pulses']['pi_half_pulse_time'] = float(self.pi_half_time)
                        # self.scripts['deer'].settings['mw_pulses']['pi_pulse_time'] = float(self.pi_time)
                        # self.scripts['deer'].settings['mw_pulses']['3pi_half_pulse_time'] = float(self.three_pi_half_time)
                        # self.scripts['deer'].settings['decoupling_seq']['type'] = self.settings['DEER_decoupling_seq']['type']
                        # self.scripts['deer'].settings['decoupling_seq']['num_of_pulse_blocks'] = self.settings['DEER_decoupling_seq']['num_of_pulse_blocks']
                        # self.scripts['deer'].run()
                        # tag before starting deer sweeps:
                        # base_tag_deer = self.scripts['deer'].settings['tag']

                        # if self.settings['DEER_spectrum']['do_RF_freq_sweep']:
                        #     self.do_deer_freq_sweep()
                        # elif self.settings['DEER_power_sweep']['do_RF_pwr_sweep']:
                        #     self.do_deer_pwr_sweep()
                        # else:
                        #     self.scripts['deer'].run()

                        # return to original tag:
                        # self.scripts['deer'].settings['tag'] = base_tag_deer

        else:
            self.log('No resonance frequency found skipping rabi attempt')

    def do_deer_freq_sweep(self):
        deerfldrlblb1 = self.scripts['deer_tau'].settings['tag']
        for freq in np.linspace(self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_freq_sweep']['RF_center_freq'] - self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_freq_sweep']['RF_freq_sweep_range'] / 2,
                                self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_freq_sweep']['RF_center_freq'] + self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_freq_sweep']['RF_freq_sweep_range'] / 2,
                                self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_freq_sweep']['RF_freq_sweep_npoints']):
            self.scripts['deer_tau'].settings['RF_pulses']['RF_frequency'] = freq.tolist()
            self.log('RF frequency set to ({:0.2e})MHz'.format(freq/1e6))
            self.scripts['deer_tau'].settings['tag'] = deerfldrlblb1 + '_freq{:.0f}MHz'.format(freq/1e6)
            ### inner loop does power sweeps:
            if self.settings['DEER_power_sweep']['do_RF_pwr_sweep']:
                self.do_deer_pwr_sweep()
            else:
                self.scripts['deer_tau'].run()

    def do_deer_pwr_sweep(self):
        deerfldrlblb2 = self.scripts['deer_tau'].settings['tag']
        for pwr in np.linspace(self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_power_sweep']['RF_pwr'] - self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_power_sweep']['RF_pwr_sweep_range'] / 2,
                               self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_power_sweep']['RF_pwr'] + self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_power_sweep']['RF_pwr_sweep_range'] / 2,
                               self.settings['DEER_spectrum']['scan_tau']['do_scan_tau']['DEER_power_sweep']['RF_pwr_sweep_npoints']):
            self.scripts['deer_tau'].settings['RF_pulses']['RF_power'] = pwr.tolist()
            self.log('RF power set to ({:0.2e})'.format(pwr))
            self.scripts['deer_tau'].settings['tag'] = deerfldrlblb2 + '_pwr{:.0f}dBm'.format(pwr)
            self.scripts['deer_tau'].run()

    def _plot(self, axes_list):
        """
        Args:
            axes_list: list of axes objects on which to plot plots the esr on the first axes object
            data: data (dictionary that contains keys image_data, extent, initial_point, maximum_point) if not provided use self.data
        """

        # if self.scripts['esr'].is_running:
        #     self.scripts['esr']._plot([axes_list[1]])
        # elif self.scripts['rabi'].is_running:
        #     self.scripts['rabi']._plot(axes_list)
        # elif self.scripts['deer'].is_running:
        #     self.scripts['deer']._plot(axes_list)

        if self._current_subscript_stage['current_subscript'] is self.scripts['esr'] and self.scripts['esr'].is_running:
            self.scripts['esr']._plot([axes_list[1]])
        elif self._current_subscript_stage['current_subscript'] is self.scripts['rabi'] and self.scripts['rabi'].is_running:
            self.scripts['rabi']._plot(axes_list)
        elif self.scripts['deer_tau'].is_running:
            self.scripts['deer_tau']._plot(axes_list)
        elif self.scripts['deer_freq'].is_running:
            self.scripts['deer_freq']._plot(axes_list)
        elif self.scripts['deer_pwr'].is_running:
            self.scripts['deer_pwr']._plot(axes_list)
        elif self.scripts['deer_RFpitime'].is_running:
            self.scripts['deer_RFpitime']._plot(axes_list)

    def _update_plot(self, axes_list):
        """
        Args:
            axes_list: list of axes objects on which to plot plots the esr on the first axes object
        """

        # if self.scripts['esr'].is_running:
        #     self.scripts['esr']._update_plot([axes_list[1]])
        # elif self.scripts['rabi'].is_running:
        #     self.scripts['rabi']._update_plot(axes_list)
        # elif self.scripts['deer'].is_running:
        #     self.scripts['deer']._update_plot(axes_list)

        if self._current_subscript_stage['current_subscript'] is self.scripts['esr'] and self.scripts['esr'].is_running:
            self.scripts['esr']._update_plot([axes_list[1]])
        elif self._current_subscript_stage['current_subscript'] is self.scripts['rabi'] and self.scripts['rabi'].is_running:
            self.scripts['rabi']._update_plot(axes_list)
        elif self.scripts['deer_tau'].is_running:
            self.scripts['deer_tau']._update_plot(axes_list)
        elif self.scripts['deer_freq'].is_running:
            self.scripts['deer_freq']._update_plot(axes_list)
        elif self.scripts['deer_pwr'].is_running:
            self.scripts['deer_pwr']._update_plot(axes_list)
        elif self.scripts['deer_RFpitime'].is_running:
            self.scripts['deer_RFpitime']._update_plot(axes_list)


    # def get_axes_layout(self, figure_list):
    #     """
    #     returns the axes objects the script needs to plot its data
    #     the default creates a single axes object on each figure
    #     This can/should be overwritten in a child script if more axes objects are needed
    #     Args:
    #         figure_list: a list of figure objects
    #     Returns:
    #         axes_list: a list of axes objects
    #
    #     """
    #
    #     # create a new figure list that contains only figure 1, this assures that the super.get_axes_layout doesn't
    #     # empty the plot contained on figure 2
    #     # return super(EsrRabiDeer, self).get_axes_layout([figure_list[0]])
    #
    #     return super(EsrRabiDeer, self).get_axes_layout(figure_list)

if __name__ == '__main__':
    script, failed, instr = Script.load_and_append({'EsrRabiDeerXYnSpectrumAdvanced': EsrRabiDeerXYnSpectrumAdvanced})

    print(script)
    print(failed)
    print(instr)