import general
import ui
import transport
import midi
import channels
import device
import mixer
import patterns
import tracknames
import playlist

import mcu_buttons
import mcu_constants

Jog_Wheel = 0x3C

class McuDeviceJog:
    def __init__(self, McuDeviceModifiers, McuDeviceMessages, McuDevice, TMackieCU):
        self.JogSource = 0
        self._Scrub = False
        self.McuDeviceModifiers = McuDeviceModifiers
        self.McuDeviceMessages = McuDeviceMessages
        self.McuDevice = McuDevice
        self.TMackieCU = TMackieCU

    def Handle(self, event):
        if (event.midiId == midi.MIDI_CONTROLCHANGE) & (event.midiChan == 0):
            event.inEv = event.data2
            if event.inEv >= 0x40:
                event.outEv = -(event.inEv - 0x40)
            else:
                event.outEv = event.inEv
            if event.data1 == Jog_Wheel: # jog wheel
                self.Jog(event)
                event.handled = True

        if (event.midiId == midi.MIDI_NOTEON):  # NOTEON / NOTEOFF
            if event.data1 == mcu_buttons.Scrub: # self.Scrub
                if event.data2 > 0:
                    self._Scrub = not self._Scrub
                    self.McuDevice.SetButton(mcu_buttons.Scrub, midi.TranzPort_OffOnT[self._Scrub], 15, skipIsAssignedCheck=True)
            # jog sources
            elif event.data1 in [mcu_buttons.Undo, mcu_buttons.MidiTracks, mcu_buttons.Inputs, mcu_buttons.AudioTracks, mcu_buttons.AudioInst, mcu_buttons.Aux, 
                                 mcu_buttons.Buses, mcu_buttons.Outputs, mcu_buttons.User, mcu_buttons.Control, mcu_buttons.Zoom, mcu_buttons.Shift, mcu_buttons.Trim, mcu_buttons.Marker,
                                 mcu_buttons.Nudge, mcu_buttons.Group]:
                # extra function to select browser menu item with zoom button
                if event.data1 == mcu_buttons.Zoom and ui.getFocused(midi.widBrowser):
                    ui.selectBrowserMenuItem()
                # update jog source
                if event.data1 in [mcu_buttons.Zoom, mcu_buttons.Trim]:
                    device.directFeedback(event)
                if event.data2 == 0:
                    if self.JogSource == event.data1:
                        self.JogSource = 0
                else:
                    self.JogSource = event.data1
                    event.outEv = 0
                    self.Jog(event) # for visual feedback

            elif event.data1 in [mcu_buttons.Up, mcu_buttons.Down, mcu_buttons.Left, mcu_buttons.Right]: # arrows
                if self.JogSource == mcu_buttons.Zoom:
                    if event.data1 == mcu_buttons.Up:
                        transport.globalTransport(midi.FPT_VZoomJog + int(self.McuDeviceModifiers.Shift), -1, event.pmeFlags)
                    elif event.data1 == mcu_buttons.Down:
                        transport.globalTransport(midi.FPT_VZoomJog + int(self.McuDeviceModifiers.Shift), 1, event.pmeFlags)
                    elif event.data1 == mcu_buttons.Left:
                        transport.globalTransport(midi.FPT_HZoomJog + int(self.McuDeviceModifiers.Shift), -1, event.pmeFlags)
                    elif event.data1 == mcu_buttons.Right:
                        transport.globalTransport(midi.FPT_HZoomJog + int(self.McuDeviceModifiers.Shift), 1, event.pmeFlags)

                elif self.JogSource == 0:
                    transport.globalTransport(midi.FPT_Up - mcu_buttons.Up + event.data1, int(event.data2 > 0) * 2, event.pmeFlags)
                else:
                    if event.data2 > 0:
                        event.inEv = event.data1 - mcu_buttons.Up-1
                        event.outEv = event.inEv
                        self.Jog(event)
        event.handled = True

    def Jog(self, event):
        if self.JogSource == 0: # default
            if (ui.getFocused(midi.widBrowser)):
                transport.globalTransport(midi.FPT_Jog, event.outEv, event.pmeFlags) # go up/down in browser
            else:
                ui.showWindow(midi.widPlaylist)
                ui.setFocused(midi.widPlaylist)
                if (self._Scrub):
                    oldSongPos = transport.getSongPos(midi.SONGLENGTH_ABSTICKS)
                    transport.setSongPos(oldSongPos + event.outEv * (1 + 9 * (not self.McuDeviceModifiers.Shift)), midi.SONGLENGTH_ABSTICKS)
                else:
                    transport.globalTransport(midi.FPT_Jog, event.outEv, event.pmeFlags) # relocate
        elif self.JogSource == mcu_buttons.Shift:
            transport.globalTransport(midi.FPT_MoveJog, event.outEv, event.pmeFlags)
        elif self.JogSource == mcu_buttons.Marker:
            ui.showWindow(midi.widPlaylist)
            ui.setFocused(midi.widPlaylist)
            if self.McuDeviceModifiers.Shift:
                s = 'Marker selection'
            else:
                s = 'Marker jump'
            if event.outEv != 0:
                if transport.globalTransport(midi.FPT_MarkerJumpJog + int(self.McuDeviceModifiers.Shift), event.outEv, event.pmeFlags) == midi.GT_Global:
                    s = ui.getHintMsg()
            self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + s)

        elif self.JogSource == mcu_buttons.Undo:
            if event.outEv == 0:
                s = 'Undo history'
            elif transport.globalTransport(midi.FPT_UndoJog, event.outEv, event.pmeFlags) == midi.GT_Global:
                s = ui.getHintMsg()
            self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + s + ' (level ' + general.getUndoLevelHint() + ')')

        elif self.JogSource == mcu_buttons.Zoom:
            if event.outEv != 0:
                transport.globalTransport(midi.FPT_HZoomJog + int(self.McuDeviceModifiers.Shift), event.outEv, event.pmeFlags)

        elif self.JogSource == mcu_buttons.Trim:
            if event.outEv != 0:
                transport.globalTransport(midi.FPT_WindowJog, event.outEv, event.pmeFlags)
            s = ui.getFocusedFormCaption()
            if s != "":
                self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + 'Current window: ' + s)

        elif self.JogSource == mcu_buttons.Group:
            if event.outEv != 0:
                transport.globalTransport(midi.FPT_MixerWindowJog, event.outEv, event.pmeFlags)

        elif (self.JogSource == mcu_buttons.Inputs) & (event.outEv == 0):
            self.TMackieCU.SetFirstTrack(mixer.trackNumber())
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)

        elif (self.JogSource == mcu_buttons.MidiTracks) | (self.JogSource == mcu_buttons.Inputs):
            self.TrackSel(self.JogSource - mcu_buttons.MidiTracks, event.outEv)
            if self.JogSource == mcu_buttons.MidiTracks:
                ui.showWindow(midi.widPlaylist)
                ui.setFocused(midi.widPlaylist)
            elif self.JogSource == mcu_buttons.Inputs:
                ui.showWindow(midi.widMixer)
                ui.setFocused(midi.widMixer)
        elif self.JogSource == mcu_buttons.AudioInst:
            ui.showWindow(midi.widChannelRack)
            ui.setFocused(midi.widChannelRack)
            self.TrackSel(2, event.outEv)

        elif (self.JogSource == mcu_buttons.Outputs):
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)
            self.TMackieCU.SetFirstTrack(0 + event.outEv)

        elif (self.JogSource == mcu_buttons.Buses or self.JogSource == mcu_buttons.Aux):
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)
            step = event.outEv
            if step != 0:
                CurTrackNumber = self.TMackieCU.Tracks[0].TrackNum
                x = self.normaliseTrackNumber(CurTrackNumber + step)
                while (x != CurTrackNumber):
                    trackName = mixer.getTrackName(x)
                    dockSide = mixer.getTrackDockSide(x)
                    x = self.normaliseTrackNumber(x + step)
                    
                    if (self.JogSource == mcu_buttons.Buses and (trackName.lower().endswith('bus') or trackName.lower().endswith('mix'))) or ((self.JogSource == mcu_buttons.Aux) and dockSide != 1):
                        newTrack = self.normaliseTrackNumber(x-step)
                        self.TMackieCU.SetFirstTrack(newTrack)
                        break

        elif (self.JogSource == mcu_buttons.User) & (event.outEv == 0):
            ui.showWindow(midi.widBrowser)
            ui.setFocused(midi.widBrowser)

        elif self.JogSource == mcu_buttons.AudioTracks & (event.outEv == 0):
            ui.showWindow(midi.widPlaylist)
            ui.setFocused(midi.widPlaylist)
            
        elif self.JogSource == mcu_buttons.AudioTracks:
            ui.showWindow(midi.widPlaylist)
            ui.setFocused(midi.widPlaylist)
            if event.outEv != 0:
                found = False
                for x in range(1, playlist.trackCount()-1):
                    if playlist.isTrackSelected(x):
                        playlist.deselectAll()
                        if (x + event.outEv) < 1:
                            playlist.selectTrack(1)
                        elif (x + event.outEv) >= playlist.trackCount():
                            playlist.selectTrack(playlist.trackCount()-1)
                        else:
                            playlist.selectTrack(x + event.outEv)
                        found = True
                        break
                if not found:
                    playlist.selectTrack(1)
        elif self.JogSource == mcu_buttons.Control: # Next/Previous
            if event.outEv > 0:
                ui.next()
            elif event.outEv < 0:
                ui.previous()


    def TrackSel(self, Index, Step):

        Index = 2 - Index
        device.baseTrackSelect(Index, Step)
        if Index == 0:
            s = channels.getChannelName(channels.channelNumber())
            self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + 'Channel: ' + s)
        elif Index == 1:
            self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + 'Mixer track: ' + tracknames.GetAsciiSafeTrackName(mixer.trackNumber(), False))
        elif Index == 2:
            s = patterns.getPatternName(patterns.patternNumber())
            self.McuDeviceMessages.SendMsg(mcu_constants.ArrowsStr + 'Pattern: ' + s)

    @property
    def Scrub(self):
        return self._Scrub
    
    @Scrub.setter
    def Scrub(self, value):
        self._Scrub = value

    def normaliseTrackNumber(self, trackNumber):
        if trackNumber < 0:
            trackNumber = mixer.trackCount() - 1
        elif trackNumber >= mixer.trackCount():
            trackNumber = 0
        return trackNumber