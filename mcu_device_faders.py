import midi
import mixer
import device
import mcu_pages
import ui
import mcu_device_fader_conversion
import mcu_track

class McuDeviceFaders:
    def __init__(self, messages) -> None:
        self.McuDeviceMessages = messages

    def Handle(self, event, Tracks: list[mcu_track.McuTrack], Page, FreeCtrlT, SmoothSpeed):
        if event.midiId == midi.MIDI_PITCHBEND: # pitch bend (faders)
            
            if event.midiChan <= 8: #midiChan is the number of the fader (0-8)
                event.inEv = event.data1 + (event.data2 << 7)
                event.outEv = (event.inEv << 16) // 16383
                event.inEv -= 0x2000
                if Tracks[event.midiChan].SliderEventID >= 0:
                    # slider (mixer track volume)
                    event.handled = True
                    mixer.automateEvent(Tracks[event.midiChan].SliderEventID, mcu_device_fader_conversion.McuFaderToFlFader(event.inEv + 0x2000), midi.REC_MIDIController, SmoothSpeed)
                    # hint
                    n = mixer.getAutoSmoothEventValue(Tracks[event.midiChan].SliderEventID)
                    s = mixer.getEventIDValueString(Tracks[event.midiChan].SliderEventID, n)
                    if s != '':
                        s = ': ' + s
                    self.McuDeviceMessages.SendMsg(Tracks[event.midiChan].SliderName + s)
        event.handled = True