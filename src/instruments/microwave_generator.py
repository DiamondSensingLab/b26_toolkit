import visa
import pyvisa.errors

from src.core import Parameter, Instrument

RANGE_MIN = 2025000000 #2.025 GHz
RANGE_MAX = 4050000000 #4.050 GHZ

class MicrowaveGenerator(Instrument):

    _DEFAULT_SETTINGS = Parameter([
        Parameter('port', 27, range(0,31), 'GPIB port on which to connect'),
        Parameter('GPIB_num', 0, int, 'GPIB device on which to connect'),
        Parameter('enable_output', False, bool, 'Type-N output enabled'),
        Parameter('frequency', 3e9, float, 'frequency in Hz, or with label in other units ex 300 MHz'),
        Parameter('amplitude', -60, float, 'Type-N amplitude in dBm'),
        Parameter('phase', 0, float, 'output phase'),
        Parameter('enable_modulation', True, bool, 'enable modulation'),
        Parameter('modulation_type', 'FM', ['AM', 'FM', 'PhaseM', 'Freq sweep', 'Pulse', 'Blank', 'IQ'],
                  'Modulation Type: 0= AM, 1=FM, 2= PhaseM, 3= Freq sweep, 4= Pulse, 5 = Blank, 6=IQ'),
        Parameter('modulation_function', 'External', ['Sine', 'Ramp', 'Triangle', 'Square', 'Noise', 'External'],
                  'Modulation Function: 0=Sine, 1=Ramp, 2=Triangle, 3=Square, 4=Noise, 5=External'),
        Parameter('pulse_modulation_function', 'External', ['Square', 'Noise(PRBS)', 'External'], 'Pulse Modulation Function: 3=Square, 4=Noise(PRBS), 5=External'),
        Parameter('dev_width', 32e6, float, 'Width of deviation from center frequency in FM')
    ])

    def __init__(self, name = None, settings = None):

        super(MicrowaveGenerator, self).__init__(name, settings)
        # XXXXX MW ISSUE = START
        #===========================================
        # Issue where visa.ResourceManager() takes 4 minutes no longer happens after using pdb to debug (??? not sure why???)
        try:
            rm = visa.ResourceManager()
            self.srs = rm.open_resource(u'GPIB' + str(self.settings['GPIB_num']) + '::' + str(self.settings['port']) + '::INSTR')
            self.srs.query('*IDN?') # simple call to check connection
        except pyvisa.errors.VisaIOError:
            print('No Microwave Controller Detected!!')
            raise
        #XXXXX MW ISSUE = END
        #===========================================

    #Doesn't appear to be necessary, can't manually make two sessions conflict, rms may share well
    # def __del__(self):
    #     self.srs.close()

    def update(self, settings):
        #COMMENT_ME
        super(MicrowaveGenerator, self).update(settings)
        # XXXXX MW ISSUE = START
        # ===========================================
        for key, value in settings.iteritems():
            if not (key == 'port' or key == 'GPIB_num'):
                if self.settings.valid_values[key] == bool: #converts booleans, which are more natural to store for on/off, to
                    value = int(value)                #the integers used internally in the SRS
                elif key == 'modulation_type':
                    value = self._mod_type_to_internal(value)
                elif key == 'modulation_function':
                    value = self._mod_func_to_internal(value)
                elif key == 'pulse_modulation_function':
                    value = self._pulse_mod_func_to_internal
                elif key == 'frequency':
                    if value > RANGE_MAX or value < RANGE_MIN:
                        raise ValueError("Invalid frequency. All frequencies must be between 2.025 GHz and 4.050 GHz.")
                key = self._param_to_internal(key)

                # only send update to instrument if connection to instrument has been established
                if self._initialized:
                    self.srs.write(key + ' ' + str(value))
        # XXXXX MW ISSUE = END
        # ===========================================

    @property
    def _PROBES(self):
        return{
            'enable_output': 'if type-N output is enabled',
            'frequency': 'frequency of output in Hz',
            'amplitude': 'type-N amplitude in dBm',
            'phase': 'phase',
            'enable_modulation': 'is modulation enabled',
            'modulation_type': 'Modulation Type: 0= AM, 1=FM, 2= PhaseM, 3= Freq sweep, 4= Pulse, 5 = Blank, 6=IQ',
            'modulation_function': 'Modulation Function: 0=Sine, 1=Ramp, 2=Triangle, 3=Square, 4=Noise, 5=External',
            'pulse_modulation_function': 'Pulse Modulation Function: 3=Square, 4=Noise(PRBS), 5=External',
            'dev_width': 'Width of deviation from center frequency in FM'
        }

    def read_probes(self, key):
        #COMMENT_ME
        assert key in self._PROBES.keys()

        #query always returns string, need to cast to proper return type
        if key in ['enable_output', 'enable_modulation']:
            key = self._param_to_internal(key)
            value = self.srs.query(key + '?')
            if value == 1:
                value = True
            elif value == 0:
                value = False
        elif key in ['modulation_type','modulation_function','pulse_modulation_function']:
            key = self._param_to_internal(key)
            value = int(self.srs.query(key + '?'))
        else:
            key = self._param_to_internal(key)
            value = float(self.srs.query(key + '?'))

        return value

    @property
    def is_connected(self):
        #COMMENT_ME
        try:
            self.srs.query('*IDN?') # simple call to check connection
            return True
        except pyvisa.errors.VisaIOError:
            return False

    def _param_to_internal(self, param):
        #COMMENT_ME
        if param == 'enable_output':
            return 'ENBR'
        elif param == 'frequency':
            return 'FREQ'
        elif param == 'amplitude':
            return 'AMPR'
        elif param == 'phase':
            return 'PHAS'
        elif param == 'enable_modulation':
            return 'MODL'
        elif param == 'modulation_type':
            return 'TYPE'
        elif param == 'modulation_function':
            return 'MFNC'
        elif param == 'pulse_modulation_function':
            return 'PFNC'
        elif param == 'dev_width':
            return 'FDEV'
        else:
            raise KeyError

    def _mod_type_to_internal(self, value):
        #COMMENT_ME
        if value == 'AM':
            return 0
        elif value == 'FM':
            return 1
        elif value == 'PhaseM':
            return 2
        elif value == 'Freq sweep':
            return 3
        elif value == 'Pulse':
            return 4
        elif value == 'Blank':
            return 5
        elif value == 'IQ':
            return 6
        else:
            raise KeyError

    def _mod_func_to_internal(self, value):
        #COMMENT_ME
        if value == 'Sine':
            return 0
        elif value == 'Ramp':
            return 1
        elif value == 'Triangle':
            return 2
        elif value == 'Square':
            return 3
        elif value == 'Noise':
            return 4
        elif value == 'External':
            return 5
        else:
            raise KeyError

    def _pulse_mod_func_to_internal(self, value):
        #COMMENT_ME
        if value == 'Square':
            return 3
        elif value == 'Noise(PRBS)':
            return 4
        elif value == 'External':
            return 5
        else:
            raise KeyError

if __name__ == '__main__':
    # from src.core import Instrument
    #
    # instruments =        {"MicrowaveGenerator": {
    #         "class": "MicrowaveGenerator",
    #         "settings": {
    #             "enable_output": False,
    #             "enable_modulation": True,
    #             "amplitude": -60,
    #             "GPIB_num": 0,
    #             "frequency": 3000000000.0,
    #             "dev_width": 32000000.0,
    #             "pulse_modulation_function": "External",
    #             "phase": 0,
    #             "modulation_function": "External",
    #             "port": 27,
    #             "modulation_type": "FM"
    #         }
    #     }}
    #
    # instr = {}
    #
    # instr, loaded_failed = Instrument.load_and_append(
    #     {name: instruments[name] for name in instruments.keys()}, instr)
    #
    # print(instr)
    # print(loaded_failed)
    # import src.instruments.microwave_generator MicrowaveGenerator

    mw = MicrowaveGenerator()
    # mw = MicrowaveGenerator(settings={'enable_modulation': True, 'frequency': 3000000000.0, 'dev_width': 32000000.0, 'pulse_modulation_function': 'External', 'phase': 0, 'port': 27, 'modulation_type': 'FM', 'enable_output': False, 'GPIB_num': 0, 'amplitude': -60, 'modulation_function': 'External'})

    print(mw.srs)

    # instrument_name= 'MicrowaveGenerator'
    # instrument_settings = {'enable_modulation': True, 'frequency': 3000000000.0, 'dev_width': 32000000.0, 'pulse_modulation_function': 'External', 'phase': 0, 'port': 27, 'modulation_type': 'FM', 'enable_output': False, 'GPIB_num': 0, 'amplitude': -60, 'modulation_function': 'External'}
    # class_of_instrument = MicrowaveGenerator
    # instrument_instance = class_of_instrument(name=instrument_name, settings=instrument_settings)
