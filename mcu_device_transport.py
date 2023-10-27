import midi
import mcu_buttons
import transport
import device
import ui
import mixer
import mcu_constants

class McuDeviceTransport:
    def __init__(self, modifiers, messages, device) -> None:
        self.McuDeviceModifiers = modifiers
        self.McuDeviceMessages = messages
        self.McuDevice = device
        self.Clicking = False

    def Handle(self, event):
        if event.midiId != midi.MIDI_NOTEON:
            return

        if (event.data1 == mcu_buttons.Rewind) | (event.data1 == mcu_buttons.FastForward) : # << >>
            if self.McuDeviceModifiers.Shift:
                if event.data2 == 0:
                    v2 = 1
                elif event.data1 == mcu_buttons.Rewind:
                    v2 = 0.5
                else:
                    v2 = 2
                transport.setPlaybackSpeed(v2)
            else:
                transport.globalTransport(midi.FPT_Rewind + int(event.data1 == 0x5C), int(event.data2 > 0) * 2, event.pmeFlags)
            device.directFeedback(event)

        elif event.data1 == mcu_buttons.Stop: # stop
            transport.globalTransport(midi.FPT_Stop, int(event.data2 > 0) * 2, event.pmeFlags)
        elif event.data1 == mcu_buttons.Play: # play
            transport.globalTransport(midi.FPT_Play, int(event.data2 > 0) * 2, event.pmeFlags)
        elif event.data1 == mcu_buttons.Record: # record
            transport.globalTransport(midi.FPT_Record, int(event.data2 > 0) * 2, event.pmeFlags)
        elif event.data1 == mcu_buttons.Solo: # song/loop
            transport.globalTransport(midi.FPT_Loop, int(event.data2 > 0) * 2, event.pmeFlags)

        elif event.data1 in [mcu_buttons.Cycle, mcu_buttons.Drop, mcu_buttons.Replace]: # punch in/punch out/punch
            if event.data1 == mcu_buttons.Cycle:
                n = midi.FPT_Punch
            else:
                n = midi.FPT_PunchIn + event.data1 - mcu_buttons.Drop
                
            if not ((event.data1 == mcu_buttons.Drop) & (event.data2 == 0)):
                device.directFeedback(event)
            if (event.data1 >= mcu_buttons.Replace) & (event.data2 >= int(event.data1 == mcu_buttons.Replace)):
                if device.isAssigned():
                    device.midiOutMsg((mcu_buttons.Drop << 8) + midi.TranzPort_OffOnT[False])
            if transport.globalTransport(n, int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global:
                t = -1
                if n == midi.FPT_Punch:
                    if event.data2 != 1:
                        t = int(event.data2 != 2)
                elif event.data2 > 0:
                    t = int(n == midi.FPT_PunchOut)
                if t >= 0:
                    self.McuDeviceMessages.SendMsg(ui.getHintMsg())

        elif (event.data1 == mcu_buttons.Marker) & self.McuDeviceModifiers.Control: # marker add
            if (transport.globalTransport(midi.FPT_AddMarker + int(self.McuDeviceModifiers.Shift), int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global) & (event.data2 > 0):
                self.McuDeviceMessages.SendMsg(ui.getHintMsg())

        elif event.data1 == mcu_buttons.Nudge: # open audio editor in current mixer track
            device.directFeedback(event)

        elif event.data1 == mcu_buttons.Click: # metronome/button self.Clicking
            if event.data2 > 0:
                if self.McuDeviceModifiers.Shift:
                    self.Clicking = not self.Clicking
                    self.McuDevice.SetClicking(self.Clicking)
                    self.McuDeviceMessages.SendMsg('Clicking ' + mcu_constants.OffOnStr[self.Clicking])
                else:
                    transport.globalTransport(midi.FPT_Metronome, 1, event.pmeFlags)

        event.handled = True