import serial

from src.core.instruments import Instrument, Parameter


class PiezoController(Instrument):
    '''
    Code for a Thorlabs MDT693B piezo controller
    '''

    _DEFAULT_SETTINGS = Parameter([
        Parameter('axis', 'x', ['x', 'y', 'z'], '"x", "y", or "z" axis'),
        Parameter('port', 'COM3', str, 'serial port on which to connect'),
        Parameter('baudrate', 115200, int, 'baudrate of connection'),
        Parameter('timeout', .1, float, 'connection timeout'),
        Parameter('voltage', 0.0, float, 'current voltage')
    ])

    def __init__(self, name = None, settings = None):
        '''
        Initializes connection to piezo controller. If none found, raises exception.
        Args:
            name: instrument name
            settings: dictionary of settings to override defaults
        '''
        super(PiezoController, self).__init__(name, settings)
        self._is_connected = False
        try:
            self.connect(port = self.settings['port'], baudrate = self.settings['baudrate'], timeout = self.settings['timeout'])
        except Exception:
            print('No Piezo Controller Detected')
            raise

    def connect(self, port, baudrate, timeout):
        '''
        Connects to piezo controller
        Args:
            port: COM port on which to connect
            baudrate: baud rate of connection. Check value required by device
            timeout: time to wait before abandoning communication

        Poststate: self._is_connected is True

        '''
        self.ser = serial.Serial(port = port, baudrate = baudrate, timeout = timeout)
        self.ser.write('echo=0\r') #disables repetition of input commands in output
        self.ser.readlines()
        self._is_connected = True

    def update(self, settings):
        '''
        Updates internal settings, and sets piezo voltage on hardware if that is changed
        Args:
            settings: dictionary of settings to update

        Poststate: changes voltage on piezo controller if it is updated

        '''
        super(PiezoController, self).update(settings)
        for key, value in settings.iteritems():
            if key == 'voltage':
                self.set_voltage(value)
            elif key == 'voltage_limit':
                raise EnvironmentError('Voltage limit cannot be set in software. Change physical switch on back of device')

    @property
    def _PROBES(self):
        '''

        Returns: a dictionary that contains the values that can be read from the instrument
        the key is the name of the value and the value of the dictionary is an info

        '''
        return {
            'voltage': 'the voltage on the current channel',
            'voltage_limit': 'the maximum voltage that can be applied to the channel. must be physically switched on the back of the controller.',
        }

    def read_probes(self, key):
        '''
        requestes value from the instrument and returns it
        Args:
            key: name of requested value

        Returns: reads values from instrument

        '''
        assert key in self._PROBES.keys()
        assert isinstance(key, str)

        if key in ['voltage']:
            self.ser.write(self.settings['axis'] + 'voltage?\r')
            xVoltage = self.ser.readline()
            return(float(xVoltage[2:-2].strip()))
        elif key in ['voltage_limit']:
            self.ser.write('vlimit?\r')
            vlimit = self.ser.readline()
            return vlimit[2:-3].strip()

    @property
    def is_connected(self):
        '''

        Returns: True if currently connected to piezo controller, False otherwise

        '''
        try:
            self.voltage
            return True
        except serial.serialutil.SerialTimeoutException:
            return False

    def __del__(self):
        '''
        Ensures that connection to hardware is closed on deletion of PiezoController object, to prevent a stale
        connection from a closed object from blocking further connections from new objects
        '''
        if self._is_connected:
            self.ser.close()

    def set_voltage(self, voltage):
        '''
        Sets the voltage on the piezo.
        Args:
            voltage: voltage (in V) to set

        '''
        self.ser.write(self.settings['axis'] + 'voltage=' + str(voltage) + '\r')
        successCheck = self.ser.readlines()
        # print(successCheck)
        # * and ! are values returned by controller on success or failure respectively
        #if(successCheck[0] == '*'):
        #    print('Voltage set')
        if successCheck[0] == '!':
            message = 'Setting voltage failed. Confirm that device is properly connected and a valid voltage was entered'
            raise ValueError(message)

if __name__ == '__main__':
    a = PiezoController('hi')