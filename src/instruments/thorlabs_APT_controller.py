import thorlabs_apt as apt
import os
import numpy as np
import warnings
from PyLabControl.src.core.read_write_functions import get_config_value
from PyLabControl.src.core import Instrument, Parameter

# Constants APT interface constants for this controller:
# EncCnt_KDC101 = 12288
# T_KDC101 = 2048 / (6e6)
EncCnt_KDC101 = 1638.4
T_KDC101 = 2048 / (6e6)

class KDC101(Instrument):
    '''
    Class to control the thorlabs TDC001 servo. Note that ALL DLL FUNCTIONS TAKING NUMERIC INPUT REQUIRE A SYSTEM.DECIMAL
    VALUE. Check help doc at C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DotNet_API for the DLL api.
    The class communicates with the device over USB.
    '''

    _DEFAULT_SETTINGS = Parameter([
        Parameter('serial_number', 27001615, int, 'serial number written on device'),
        Parameter('position', 0, float, 'servo position (from 0 to 6 in mm)'),
        Parameter('velocity', 0, float, 'servo maximum velocity in mm/s')
    ])

    def __init__(self, name=None, settings=None):
        super(KDC101, self).__init__(name, settings)
        list_apt_devices = apt.list_available_devices()

        if self.settings['serial_number'] in [list_apt_devices[l][1] for l in range(len(list_apt_devices))]:
            print('KDC101 harware info:')
            print(apt.hardware_info(self.settings['serial_number']))

            self.azimuth = apt.Motor(self.settings['serial_number'])

            self.azimuth.set_stage_axis_info(0, 360, 2, 7.5)
            print('stage info:')
            print(self.azimuth.get_stage_axis_info())

            self.azimuth.set_hardware_limit_switches(1,1)
            print("hardware limit switches")
            print(self.azimuth.get_hardware_limit_switches())

        else:
            print('apt devices available:')
            print(list_apt_devices)
            raise EnvironmentError("Device with serial=" + str(self.settings['serial_number']) + ' not found')
            # warnings.warn("Device with serial=" + str(self.settings['serial_number']) + ' not found')

    def set_angle(self, angle):

        # temp = self._angle_to_apt(angle)
        print('forw lim switch')
        print(self.azimuth.is_forward_hardware_limit_switch_active)
        print('rev lim switch')
        print(self.azimuth.is_reverse_hardware_limit_switch_active)
        # 12.207056045532227, 122.07028198242188, 244.2490692138672, 244.2490692138672, 1
        # self.azimuth.set_dc_joystick_parameters(float(12), float(122), float(244), float(244), int(1))
        print("joystick params")
        print(self.azimuth.get_dc_joystick_parameters())

        print("velocity params")
        print(self.azimuth.get_vel_params())

        print("velocity param limits")
        print(self.azimuth.get_vel_param_limits())

        print("new velocity params")
        self.azimuth.set_vel_params(0.0,0.56,0.6)
        print(self.azimuth.get_vel_params())

        self.azimuth.set_dc_profile_mode_parameters(2, 1)
        print("profile params")
        print(self.azimuth.get_dc_profile_mode_parameters())


        temp = angle
        print('moving to '+ str(angle) + 'deg ('+ str(temp) + 'apt units)')
        self.azimuth.move_to(temp)


    def _angle_to_apt(self, angle):
        return int(EncCnt_KDC101*angle)

    def _vel_to_apt(self, vel):
        return int(EncCnt_KDC101*vel*65536*T_KDC101)

    def _acc_to_apt(self, acc):
        return int(EncCnt_KDC101*acc*65536*T_KDC101*T_KDC101)


