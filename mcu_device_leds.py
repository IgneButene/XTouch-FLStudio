import midi
import transport
import ui
import mixer
import general
import device

import mcu_buttons
import mcu_device
import mcu_track

class McuDeviceLeds:
    def __init__(self, McuDeviceJog, McuDevice: mcu_device.McuDevice):
        self.McuDeviceJog = McuDeviceJog
        self.McuDevice = McuDevice

    def UpdateMasterSectionLEDs(self, Page, Flip, SmoothSpeed, Tracks: list[mcu_track.McuTrack]):
        """
        Updates the LEDs on the Master Section
        """

        if device.isAssigned():
            # stop
            self.McuDevice.SetButton(mcu_buttons.Stop, midi.TranzPort_OffOnT[transport.isPlaying() == midi.PM_Stopped], 0, skipIsAssignedCheck=True)
            # loop
            self.McuDevice.SetButton(mcu_buttons.Solo, midi.TranzPort_OffOnT[transport.getLoopMode() == midi.SM_Pat], 1, skipIsAssignedCheck=True)
            # record
            isRecording = transport.isRecording()
            self.McuDevice.SetButton(mcu_buttons.Record, midi.TranzPort_OffOnT[isRecording], 2, skipIsAssignedCheck=True)
            # SMPTE/BEATS
            isTimeDisp = ui.getTimeDispMin()
            self.McuDevice.SetButton(mcu_buttons.Smpte_Led, midi.TranzPort_OffOnT[isTimeDisp], 3, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.Beats_Led, midi.TranzPort_OffOnT[not isTimeDisp], 4, skipIsAssignedCheck=True)
            # self.Page
            for i in range(0,  6):
                self.McuDevice.SetButton(mcu_buttons.Pan + i, midi.TranzPort_OffOnT[i == Page], 5 + i, skipIsAssignedCheck=True)
            # changed flag
            self.McuDevice.SetButton(mcu_buttons.Save, midi.TranzPort_OffOnT[general.getChangedFlag() > 0], 11, skipIsAssignedCheck=True)
            # metronome
            self.McuDevice.SetButton(mcu_buttons.Click, midi.TranzPort_OffOnT[general.getUseMetronome()], 12, skipIsAssignedCheck=True)
            # rec precount
            self.McuDevice.SetButton(mcu_buttons.Replace, midi.TranzPort_OffOnT[general.getPrecount()], 13, skipIsAssignedCheck=True)
            # self.Scrub
            self.McuDevice.SetButton(mcu_buttons.Scrub, midi.TranzPort_OffOnT[self.McuDeviceJog.Scrub], 15, skipIsAssignedCheck=True)
            # use RUDE SOLO to show if any track is armed for recording
            b = 0 # 0 = off, 1 = on, 2 = blinking
            for m in range(0,  mixer.trackCount()):
                if mixer.isTrackArmed(m):
                    b = 1 + int(isRecording)
                    break
            self.McuDevice.SetButton(mcu_buttons.Rude_Solo_Led, midi.TranzPort_OffOnBlinkT[b], 16, skipIsAssignedCheck=True)
            
            # smoothing
            self.McuDevice.SetButton(mcu_buttons.Smooth, midi.TranzPort_OffOnT[SmoothSpeed > 0], 17, skipIsAssignedCheck=True)
            # self.Flip
            self.McuDevice.SetButton(mcu_buttons.Flip, midi.TranzPort_OffOnT[Flip], 18, skipIsAssignedCheck=True)
            # snap
            self.McuDevice.SetButton(mcu_buttons.Cycle, midi.TranzPort_OffOnT[ui.getSnapMode() != 3], 19, skipIsAssignedCheck=True)
            # focused windows
            BusLed = ui.getFocused(midi.widMixer) & (Tracks[0].TrackNum >= 100)
            OutputLed = ui.getFocused(midi.widMixer) & (Tracks[0].TrackNum >= 0) & (Tracks[0].TrackNum <= 1)
            InputLed = ui.getFocused(midi.widMixer) & (not OutputLed) & (not BusLed)
            self.McuDevice.SetButton(mcu_buttons.MidiTracks, midi.TranzPort_OffOnT[ui.getFocused(midi.widPlaylist)], 20, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.Inputs, midi.TranzPort_OffOnT[InputLed], 21, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.AudioTracks, midi.TranzPort_OffOnT[ui.getFocused(midi.widPlaylist)], 22, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.AudioInst, midi.TranzPort_OffOnT[ui.getFocused(midi.widChannelRack)], 23, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.Buses, midi.TranzPort_OffOnT[BusLed], 24, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.Outputs, midi.TranzPort_OffOnT[OutputLed], 25, skipIsAssignedCheck=True)
            self.McuDevice.SetButton(mcu_buttons.User, midi.TranzPort_OffOnT[ui.getFocused(midi.widBrowser)], 26, skipIsAssignedCheck=True)

