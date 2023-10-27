import midi
import mcu_buttons
import transport


class McuDeviceAutomation:
    def __init__(self, modifiers) -> None:
        self.McuDeviceModifers = modifiers

    def Handle(self, event):
        if event.data1 == mcu_buttons.Latch: # snap
            if self.McuDeviceModifers.Shift:
                if event.data2 > 0:
                    transport.globalTransport(midi.FPT_SnapMode, 1, event.pmeFlags)
                else:
                    transport.globalTransport(midi.FPT_Snap, int(event.data2 > 0) * 2, event.pmeFlags)
                    
        elif event.data1 == mcu_buttons.Touch: # touch
            if event.data2 > 0:
                transport.globalTransport(midi.FPT_Overdub, 1, event.pmeFlags)
            else:
                transport.globalTransport(midi.FPT_Overdub, 0, event.pmeFlags)