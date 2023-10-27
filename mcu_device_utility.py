import midi
import mcu_buttons
import transport
import general
import ui

class McuDeviceUtility:
    def __init__(self, modifiers, messages) -> None:
        self.McuDeviceModifiers = modifiers
        self.McuDeviceMessages = messages

    def Handle(self, event):
        if event.midiId != midi.MIDI_NOTEON:
            return
        
        if event.data1 == mcu_buttons.Cancel: # ESC
            transport.globalTransport(midi.FPT_Escape + int(self.McuDeviceModifiers.Shift) * 2, int(event.data2 > 0) * 2, event.pmeFlags)
        elif event.data1 == mcu_buttons.Enter: # ENTER
            transport.globalTransport(midi.FPT_Enter + int(self.McuDeviceModifiers.Shift) * 2, int(event.data2 > 0) * 2, event.pmeFlags)
        # save/save new
        elif event.data1 == mcu_buttons.Save:
            transport.globalTransport(midi.FPT_Save + int(self.McuDeviceModifiers.Shift), int(event.data2 > 0) * 2, event.pmeFlags)

        elif event.data1 == mcu_buttons.Undo: # undo/redo
            if (transport.globalTransport(midi.FPT_Undo, int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global) & (event.data2 > 0):
                self.McuDeviceMessages.SendMsg(ui.getHintMsg() + ' (level ' + general.getUndoLevelHint() + ')')
                
        event.handled = True