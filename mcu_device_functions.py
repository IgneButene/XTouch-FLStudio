import midi
import mcu_buttons
import transport
import ui
import time

class McuDeviceFunctions:
    def __init__(self, modifiers, messages) -> None:
        self.McuDeviceModifiers = modifiers
        self.McuDeviceMessages = messages

    def Handle(self, event):
        if event.midiId != midi.MIDI_NOTEON:
            return

        # F1..F8
        if self.McuDeviceModifiers.Shift & (event.data1 in [mcu_buttons.F1_Cut, mcu_buttons.F2_Copy, mcu_buttons.F3_Paste, mcu_buttons.F4_Insert, mcu_buttons.F5_Delete, mcu_buttons.F6_ItemMenu, mcu_buttons.F7_Undo, mcu_buttons.F8_UndoRedo]):
            transport.globalTransport(midi.FPT_F1 - mcu_buttons.F1_Cut + event.data1, int(event.data2 > 0) * 2, event.pmeFlags)
            event.data1 = 0xFF

        elif self.McuDeviceModifiers.Control & (event.data1 in [mcu_buttons.F1_Cut, mcu_buttons.F2_Copy, mcu_buttons.F3_Paste, mcu_buttons.F4_Insert, mcu_buttons.F5_Delete, mcu_buttons.F6_ItemMenu, mcu_buttons.F7_Undo, mcu_buttons.F8_UndoRedo]):
            ui.showWindow(midi.widPlaylist)
            ui.setFocused(midi.widPlaylist)
            transport.globalTransport(midi.FPT_Menu, int(event.data2 > 0) * 2, event.pmeFlags)
            time.sleep(0.1)
            f = int(1 + event.data1 - mcu_buttons.F1_Cut)
            for x in range(0, f):
                transport.globalTransport(midi.FPT_Down, int(event.data2 > 0) * 2, event.pmeFlags)
                time.sleep(0.01)
            time.sleep(0.1)
            transport.globalTransport(midi.FPT_Enter, int(event.data2 > 0) * 2, event.pmeFlags)
            event.data1 = 0xFF

        elif event.data1 in [mcu_buttons.F1_Cut, mcu_buttons.F2_Copy, mcu_buttons.F3_Paste, mcu_buttons.F4_Insert, mcu_buttons.F5_Delete]: # cut/copy/paste/insert/delete
            transport.globalTransport(midi.FPT_Cut + event.data1 - mcu_buttons.F1_Cut, int(event.data2 > 0) * 2, event.pmeFlags)
            if event.data2 > 0:
                CutCopyMsgT = ('Cut', 'Copy', 'Paste', 'Insert', 'Delete') #FPT_Cut..FPT_Delete
                self.McuDeviceMessages.SendMsg(CutCopyMsgT[midi.FPT_Cut + event.data1 - mcu_buttons.F1_Cut - 50])

        elif event.data1 == mcu_buttons.F8_UndoRedo: # menu
            transport.globalTransport(midi.FPT_Menu, int(event.data2 > 0) * 2, event.pmeFlags)
            if event.data2 > 0:
                self.McuDeviceMessages.SendMsg('Menu')

        elif event.data1 == mcu_buttons.F6_ItemMenu: # tools
            transport.globalTransport(midi.FPT_ItemMenu, int(event.data2 > 0) * 2, event.pmeFlags)
            if event.data2 > 0:
                self.McuDeviceMessages.SendMsg('Tools')
                
        event.handled = True