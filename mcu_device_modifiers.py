import mcu_buttons
import device
import midi

class McuDeviceModifiers:
    def __init__(self):
        self._Shift = False
        self._Control = False
        self._Option = False
        self._Alt = False
    
    def Handle(self, event):       
        if (event.midiId != midi.MIDI_NOTEON) & (event.midiId != midi.MIDI_NOTEOFF):  # NOTEON / NOTEOFF
            return

        if event.data1 == mcu_buttons.Shift: # self.Shift
            self._Shift = event.data2 > 0
            device.directFeedback(event)

        elif event.data1 == mcu_buttons.Alt: # self.Alt
            self._Alt = event.data2 > 0
            device.directFeedback(event)

        elif event.data1 == mcu_buttons.Control: # self.Control
            self._Control = event.data2 > 0
            device.directFeedback(event)

        elif event.data1 == mcu_buttons.Option: # self.Option
            self._Option = event.data2 > 0
            device.directFeedback(event)
        
        event.handled = True

    @property
    def Shift(self):
        return self._Shift
    
    @property
    def Control(self):
        return self._Control
    
    @property
    def Option(self):
        return self._Option
    
    @property
    def Alt(self):
        return self._Alt