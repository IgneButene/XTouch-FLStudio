# name=Behringer X-Touch v2
# url=https://forum.image-line.com/viewtopic.php?f=1994&t=269919
# supportedDevices=X-Touch

import patterns
import mixer
import device
import transport
import general
import playlist
import ui
import channels
import plugins

import midi
import utils

import debug
import mcu_pages
import mcu_buttons
import mcu_knobs
import mcu_device
import mcu_device_fader_conversion
import mcu_track
import mcu_extender_location
import mcu_base_class
import mcu_constants
import tracknames

import mcu_device_jog
import mcu_device_modifiers
import mcu_device_leds
import mcu_device_messages
import mcu_device_transport
import mcu_device_faders
import mcu_device_utility
import mcu_device_functions
import mcu_device_automation
class TMackieCU(mcu_base_class.McuBaseClass):
    def __init__(self):
        device = mcu_device.McuDevice(False)
        modifiers = mcu_device_modifiers.McuDeviceModifiers()
        messages = mcu_device_messages.McuDeviceMessages(device)
        jog = mcu_device_jog.McuDeviceJog(modifiers, messages, device, self)
        leds = mcu_device_leds.McuDeviceLeds(jog, device)
        transport = mcu_device_transport.McuDeviceTransport(modifiers, messages, device)
        faders = mcu_device_faders.McuDeviceFaders(messages)
        utility = mcu_device_utility.McuDeviceUtility(modifiers, messages)
        functions = mcu_device_functions.McuDeviceFunctions(modifiers, messages)
        automation = mcu_device_automation.McuDeviceAutomation(modifiers)
        
        super().__init__(device, jog, modifiers, leds, messages, transport, faders, utility, functions, automation)

        self.Tracks = [mcu_track.McuTrack() for i in range(9)]

        self.MackieCU_ExtenderPosT = ('left', 'right')

        self.ExtenderPos = mcu_extender_location.Left

    def OnInit(self):
        super().OnInit()

        self.UpdateMeterMode()

        self.SetPage(self.Page)
        self.McuDeviceMessages.SendMsg('Linked to ' + ui.getProgTitle() + ' (' + ui.getVersion() + ')')
        print('OnInit ready')

    def OnDeInit(self):
        super().OnDeInit()

        if device.isAssigned():
            # clear time message
            self.McuDevice.TimeDisplay.SetMessage('', skipIsAssignedCheck = True)
            # clear assignment message
            self.McuDevice.SetAssignmentMessage(skipIsAssignedCheck = True)

        print('OnDeInit ready')

    def OnRefresh(self, flags):
        if flags & midi.HW_Dirty_Mixer_Sel or flags & midi.HW_ChannelEvent or flags & midi.HW_Dirty_LEDs:
            self.UpdateMixer_Sel()

        if flags & midi.HW_Dirty_Mixer_Display:
            self.UpdateTextDisplay()
            self.UpdateColT()
        
        if flags & midi.HW_Dirty_Mixer_Controls:
            for n in range(0, len(self.Tracks)):
                if self.Tracks[n].Dirty:
                    self.UpdateTrack(n)
        
        if flags & midi.HW_Dirty_ControlValues:
            if self.Page in [mcu_pages.Effects, mcu_pages.Instruments]:
                for n in range(0, len(self.Tracks)):
                    self.UpdateTrack(n)

        # LEDs
        if flags & midi.HW_Dirty_LEDs:
            self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)

    def OnMidiMsg(self, event):
        if (event.pmeFlags & midi.PME_System == 0):  # system message
            return
        
        self.McuDeviceModifiers.Handle(event)
        self.McuDeviceJog.Handle(event)
        self.McuDeviceTransport.Handle(event)
        self.McuDeviceFaders.Handle(event, self.Tracks, self.Page, self.FreeCtrlT, self.SmoothSpeed)
        self.McuDeviceUtility.Handle(event)
        self.McuDeviceFunctions.Handle(event)
        self.McuDeviceAutomation.Handle(event)

        if (event.midiId == midi.MIDI_CONTROLCHANGE):
            if (event.midiChan == 0):
                # knobs
                if event.data1 in [mcu_knobs.Knob_1, mcu_knobs.Knob_2, mcu_knobs.Knob_3, mcu_knobs.Knob_4, mcu_knobs.Knob_5, mcu_knobs.Knob_6, mcu_knobs.Knob_7, mcu_knobs.Knob_8]:
                    Res = 0.005 + ((abs(event.outEv)-1) / 2000)
                    super().SetKnobValue(event.data1 - mcu_knobs.Knob_1, event.outEv, Res)
                    event.handled = True
                else:
                    event.handled = False # for extra CCs in emulators
            else:
                event.handled = False # for extra CCs in emulators

        elif (event.midiId == midi.MIDI_NOTEON) | (event.midiId == midi.MIDI_NOTEOFF):  # NOTE
            if event.midiId == midi.MIDI_NOTEON:
                # slider hold
                if (event.data1 in [mcu_buttons.Slider_1, mcu_buttons.Slider_2, mcu_buttons.Slider_3, mcu_buttons.Slider_4, mcu_buttons.Slider_5, mcu_buttons.Slider_6, mcu_buttons.Slider_7, mcu_buttons.Slider_8, mcu_buttons.Slider_Main]):
                    # Auto select channel
                    if event.data1 != mcu_buttons.Slider_Main and event.data2 > 0 and (self.Page == mcu_pages.Pan or self.Page == mcu_pages.Stereo):
                        fader_index = event.data1 - mcu_buttons.Slider_1
                        if mixer.trackNumber != self.Tracks[fader_index].TrackNum:
                            mixer.setTrackNumber(self.Tracks[fader_index].TrackNum)
                    event.handled = True
                    return

                if (event.pmeFlags & midi.PME_System != 0):
                    if event.data1 == mcu_buttons.NameValue: # display mode
                        if event.data2 > 0:
                            if self.McuDeviceModifiers.Shift:
                                self.ExtenderPos = abs(self.ExtenderPos - 1)
                                self.FirstTrackT[self.FirstTrack] = 1
                                self.SetPage(self.Page)
                                self.McuDeviceMessages.SendMsg('Extender on ' + self.MackieCU_ExtenderPosT[self.ExtenderPos])
                            else:
                                transport.globalTransport(midi.FPT_F2, int(event.data2 > 0) * 2, event.pmeFlags, 8)
                    elif event.data1 == mcu_buttons.TimeFormat: # time format
                        if event.data2 > 0:
                            ui.setTimeDispMin()
                    elif (event.data1 == mcu_buttons.FaderBankLeft) | (event.data1 == mcu_buttons.FaderBankRight): # mixer bank
                        if event.data2 > 0:
                            self.SetFirstTrack(self.FirstTrackT[self.FirstTrack] - 8 + int(event.data1 == mcu_buttons.FaderBankRight) * 16)
                            self.McuDevice.SendMidiToExtenders(midi.MIDI_NOTEON + (event.data1 << 8) + (event.data2 << 16))

                            if self.Page == mcu_pages.Effects:
                                ParamCount = plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset)
                            elif self.Page == mcu_pages.Instruments:
                                ParamCount = plugins.getParamCount(self.CurPluginID + self.CurPluginOffset)

                            if (self.CurPluginID != -1): # Selected Plugin
                                if (event.data1 == mcu_buttons.FaderBankLeft) & (self.PluginParamOffset >= 8):
                                    self.PluginParamOffset -= 8
                                elif (event.data1 == mcu_buttons.FaderBankRight) & (self.PluginParamOffset + 8 < ParamCount - 8):
                                    self.PluginParamOffset += 8
                            else: # No Selected Plugin
                                if (event.data1 == mcu_buttons.FaderBankLeft) & (self.CurPluginOffset >= 2):
                                    self.CurPluginOffset -= 2
                                elif (event.data1 == mcu_buttons.FaderBankRight) & (self.CurPluginOffset < 2):
                                    self.CurPluginOffset += 2
                    elif (event.data1 == mcu_buttons.FaderChannelLeft) | (event.data1 == mcu_buttons.FaderChannelRight):
                        if event.data2 > 0:                         
                            self.SetFirstTrack(self.FirstTrackT[self.FirstTrack] - 1 + int(event.data1 == mcu_buttons.FaderChannelRight) * 2)
                            self.McuDevice.SendMidiToExtenders(midi.MIDI_NOTEON + (event.data1 << 8) + (event.data2 << 16))

                            if self.Page == mcu_pages.Effects:
                                ParamCount = plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset)
                            elif self.Page == mcu_pages.Instruments:
                                ParamCount = plugins.getParamCount(self.CurPluginID + self.CurPluginOffset)

                            if (self.CurPluginID != -1): # Selected Plugin
                                if (event.data1 == mcu_buttons.FaderChannelLeft) & (self.PluginParamOffset > 0):
                                    self.PluginParamOffset -= 1
                                elif (event.data1 == mcu_buttons.FaderChannelRight) & (self.PluginParamOffset < ParamCount - 8):
                                    self.PluginParamOffset += 1
                            else: # No Selected Plugin
                                if (event.data1 == mcu_buttons.FaderChannelLeft) & (self.CurPluginOffset > 0):
                                    self.CurPluginOffset -= 1
                                elif (event.data1 == mcu_buttons.FaderChannelRight) & (self.CurPluginOffset < 2):
                                    self.CurPluginOffset += 1
                    elif event.data1 == mcu_buttons.Flip: # self.Flip
                        if event.data2 > 0:
                            self.Flip = not self.Flip
                            self.McuDevice.SendMidiToExtenders(midi.MIDI_NOTEON + (event.data1 << 8) + (event.data2 << 16))
                            self.UpdateColT()
                            self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
                    elif event.data1 == mcu_buttons.Smooth: # smoothing
                        if event.data2 > 0:
                            self.SmoothSpeed = int(self.SmoothSpeed == 0) * 469
                            self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
                            self.McuDeviceMessages.SendMsg('Control smoothing ' + mcu_constants.OffOnStr[int(self.SmoothSpeed > 0)])

                    elif event.data1 in [mcu_buttons.Pan, mcu_buttons.Sends, mcu_buttons.Equalizer, mcu_buttons.Stereo, mcu_buttons.Effects, mcu_buttons.Free]: # self.Page
                        if event.data2 > 0:
                            n = event.data1 - mcu_buttons.Pan
                            self.McuDeviceMessages.SendMsg(mcu_constants.PageDescriptions[n])
                            self.SetPage(n)
                                
                            self.McuDevice.SendMidiToExtenders(midi.MIDI_NOTEON + (event.data1 << 8) + (event.data2 << 16))


                    elif event.data1 in [mcu_buttons.Encoder_1, mcu_buttons.Encoder_2, mcu_buttons.Encoder_3, mcu_buttons.Encoder_4, mcu_buttons.Encoder_5, mcu_buttons.Encoder_6, mcu_buttons.Encoder_7, mcu_buttons.Encoder_8]: # knob reset
                        if event.data2 > 0:
                            n = event.data1 - mcu_buttons.Encoder_1
                            if self.Page == mcu_pages.Sends:
                                if self.McuDeviceModifiers.Control: # Sidechain (toggle volume)
                                    if mixer.getRouteSendActive(mixer.trackNumber(), self.Tracks[n].TrackNum):
                                        m = mixer.getEventValue(self.Tracks[n].KnobEventID, midi.MaxInt, False)
                                        if m > 0:
                                            super().SetKnobValue(n, -midi.MaxInt) # 0%
                                        else:
                                            super().SetKnobValue(n, 20) # 100%

                                elif mixer.setRouteTo(mixer.trackNumber(), self.Tracks[n].TrackNum, -1) < 0:
                                    self.McuDeviceMessages.SendMsg('Cannot send to this track')
                                else:
                                    mixer.afterRoutingChanged()
                            else:
                                super().SetKnobValue(n, midi.MaxInt)

                    if (event.pmeFlags & midi.PME_System_Safe != 0):
                        if event.data1 == mcu_buttons.Read: # focus browser
                            if event.data2 > 0:
                                ui.showWindow(midi.widBrowser)

                        elif event.data1 == mcu_buttons.Write: # focus step seq
                            if event.data2 > 0:
                                ui.showWindow(midi.widChannelRack)

                        elif event.data1 in [mcu_buttons.Touch, mcu_buttons.Latch, mcu_buttons.Group]: # punch in/punch out/punch
                            if event.data1 == mcu_buttons.Group:
                                n = midi.FPT_Punch
                            else:
                                n = midi.FPT_PunchIn + event.data1 - mcu_buttons.Touch
                            if not ((event.data1 == mcu_buttons.Touch) & (event.data2 == 0)):
                                device.directFeedback(event)
                            if (event.data1 >= mcu_buttons.Latch) & (event.data2 >= int(event.data1 == mcu_buttons.Latch)):
                                if device.isAssigned():
                                    device.midiOutMsg((mcu_buttons.Touch << 8) + midi.TranzPort_OffOnT[False])
                            if transport.globalTransport(n, int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global:
                                t = -1
                                if n == midi.FPT_Punch:
                                    if event.data2 != 1:
                                        t = int(event.data2 != 2)
                                elif event.data2 > 0:
                                    t = int(n == midi.FPT_PunchOut)
                                if t >= 0:
                                    self.McuDeviceMessages.SendMsg(ui.getHintMsg())


                        
                        # select mixer track buttons
                        elif (event.data1 >= mcu_buttons.Select_1) & (event.data1 <= mcu_buttons.Select_8):
                            if event.data2 > 0:
                                i = event.data1 - mcu_buttons.Select_1
                                if self.Page == mcu_pages.Instruments:
                                    if self.Tracks[i].TrackNum < channels.channelCount():
                                        if not self.McuDeviceModifiers.Control and not self.McuDeviceModifiers.Shift:
                                            channels.deselectAll()
                                        if self.McuDeviceModifiers.Shift:
                                            selectedChannel = 0
                                            channelCount = channels.channelCount()
                                            for x in range(0, channelCount):
                                                if channels.isChannelSelected(x):
                                                    selectedChannel = x
                                                    break
                                            
                                            while(selectedChannel != self.Tracks[i].TrackNum):
                                                channels.selectChannel(selectedChannel, 1)
                                                if selectedChannel < self.Tracks[i].TrackNum:
                                                    selectedChannel += 1
                                                else:
                                                    selectedChannel -= 1
                                                if selectedChannel >= channelCount:
                                                    break
                                                elif selectedChannel < 0:
                                                    break
                                            channels.selectChannel(self.Tracks[i].TrackNum, 1)        
                                        else:
                                            channels.selectChannel(self.Tracks[i].TrackNum, -1)
                                else: # mixer
                                    ui.showWindow(midi.widMixer)
                                    ui.setFocused(midi.widMixer)
                                    if not self.McuDeviceModifiers.Control and not self.McuDeviceModifiers.Shift:
                                        mixer.deselectAll()
                                    if self.McuDeviceModifiers.Control:
                                        mixer.selectTrack(self.Tracks[i].TrackNum, -1)
                                    else:
                                        mixer.setTrackNumber(self.Tracks[i].TrackNum, midi.curfxScrollToMakeVisible | midi.curfxMinimalLatencyUpdate)

                                if self.McuDeviceModifiers.Option: # Link channel to track
                                    mixer.linkTrackToChannel(midi.ROUTE_ToThis)
                        
                        # solo buttons
                        elif (event.data1 >= mcu_buttons.Solo_1) & (event.data1 <= mcu_buttons.Solo_8):
                            if event.data2 > 0:
                                i = event.data1 - mcu_buttons.Solo_1
                                self.Tracks[i].solomode = midi.fxSoloModeWithDestTracks
                                if self.McuDeviceModifiers.Shift:
                                    pass #function does not exist: Include(self.Tracks[i].solomode, midi.fxSoloModeWithSourceTracks)
                                if self.Page == mcu_pages.Instruments:
                                    if self.Tracks[i].TrackNum < channels.channelCount():
                                        channels.soloChannel(self.Tracks[i].TrackNum)
                                else:
                                    mixer.soloTrack(self.Tracks[i].TrackNum, midi.fxSoloToggle, self.Tracks[i].solomode)
                                    mixer.setTrackNumber(self.Tracks[i].TrackNum, midi.curfxScrollToMakeVisible)

                        # mute buttons
                        elif (event.data1 >= mcu_buttons.Mute_1) & (event.data1 <= mcu_buttons.Mute_8):
                            if event.data2 > 0:
                                if self.Page == mcu_pages.Instruments:
                                    trackNum = self.Tracks[event.data1 - mcu_buttons.Mute_1].TrackNum
                                    if trackNum < channels.channelCount():
                                        channels.muteChannel(self.Tracks[event.data1 - mcu_buttons.Mute_1].TrackNum)
                                else:
                                    mixer.enableTrack(self.Tracks[event.data1 - mcu_buttons.Mute_1].TrackNum)

                        # record (arm) buttons
                        elif (event.data1 >= mcu_buttons.Record_1) & (event.data1 <= mcu_buttons.Record_8):
                            if event.data2 > 0:
                                if self.Page == mcu_pages.Instruments:
                                    if self.Tracks[event.data1].TrackNum < channels.channelCount():
                                        ui.openEventEditor(channels.getRecEventId(self.Tracks[event.data1].TrackNum) + midi.REC_Chan_PianoRoll, midi.EE_PR)
                                else:
                                    mixer.armTrack(self.Tracks[event.data1].TrackNum)
                                    if mixer.isTrackArmed(self.Tracks[event.data1].TrackNum):
                                        self.McuDeviceMessages.SendMsg(tracknames.GetAsciiSafeTrackName(self.Tracks[event.data1].TrackNum) + ' recording to ' + mixer.getTrackRecordingFileName(self.Tracks[event.data1].TrackNum))
                                    else:
                                        self.McuDeviceMessages.SendMsg(tracknames.GetAsciiSafeTrackName(self.Tracks[event.data1].TrackNum) + ' unarmed')

                        event.handled = True
                else:
                    event.handled = False
            else:
                event.handled = False

    def OnUpdateBeatIndicator(self, Value):

        SyncLEDMsg = [ midi.MIDI_NOTEON + (0x5E << 8), midi.MIDI_NOTEON + (0x5E << 8) + (0x7F << 16), midi.MIDI_NOTEON + (0x5E << 8) + (0x7F << 16)]

        if device.isAssigned():
            device.midiOutNewMsg(SyncLEDMsg[Value], 128)

    def SetPage(self, Value):
        self.CurPluginID = -1
        self.CurPluginOffset = 0

        oldPage = self.Page
        self.Page = Value

        self.FirstTrack = int(self.Page == mcu_pages.Instruments)
        receiverCount = device.dispatchReceiverCount()

        if receiverCount == 0 or self.Page != oldPage:
            self.SetFirstTrack(self.FirstTrackT[self.FirstTrack])
        else: # first time
            if self.ExtenderPos == mcu_extender_location.Left:
                for n in range(0, receiverCount):
                    self.McuDevice.SetFirstTrackOnExtender(n, self.FirstTrackT[self.FirstTrack] + (n * 8))
                self.SetFirstTrack(self.FirstTrackT[self.FirstTrack] + receiverCount * 8)
            elif self.ExtenderPos == mcu_extender_location.Right:
                self.SetFirstTrack(self.FirstTrackT[self.FirstTrack])
                for n in range(0, receiverCount):
                    self.McuDevice.SetFirstTrackOnExtender(n, self.FirstTrackT[self.FirstTrack] + ((n + 1) * 8))

        if (oldPage == mcu_pages.Instruments) | (self.Page == mcu_pages.Instruments):
            self.UpdateMeterMode()
        
        if (self.Page != oldPage):
            if (self.Page == mcu_pages.Instruments):
                ui.setFocused(midi.widChannelRack)
            elif (self.Page in [mcu_pages.Effects, mcu_pages.Pan]):
                ui.setFocused(midi.widMixer)

        self.UpdateColT()
        self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
        self.UpdateTextDisplay()

    def UpdateMixer_Sel(self):
        if self.Page != mcu_pages.Instruments:
            if device.isAssigned():
                for m in range(0, len(self.Tracks) - 1):
                    self.McuDevice.GetTrack(m).buttons.SetSelectButton(mixer.isTrackSelected(self.Tracks[m].TrackNum), True)
        else:
            for m in range(0, len(self.Tracks) - 1):
                if self.Tracks[m].TrackNum < channels.channelCount():
                    self.McuDevice.GetTrack(m).buttons.SetSelectButton(channels.isChannelSelected(self.Tracks[m].TrackNum), True)

        if self.Page in [mcu_pages.Sends, mcu_pages.Effects]:
            self.UpdateColT()

    def SetFirstTrack(self, Value):

        self.FirstTrackT[self.FirstTrack] = (Value + mixer.trackCount()) % mixer.trackCount()
        firstTrackNumber = self.FirstTrackT[self.FirstTrack]
        self.UpdateColT()
        self.McuDevice.SetAssignmentMessage(firstTrackNumber)
        device.hardwareRefreshMixerTrack(-1)

    def OnIdle(self):
        self.UpdateTimeDisplay()
        super().OnIdle()

    def UpdateTimeDisplay(self):
        """ Updates the time display to the current value """

        # time display
        if ui.getTimeDispMin():
            # HHH.MM.SS.CC_
            if playlist.getVisTimeBar() == -midi.MaxInt:
                s = '-   0'
            else:
                n = abs(playlist.getVisTimeBar())
                h, m = utils.DivModU(n, 60)
                s = utils.Zeros_Strict((h * 100 + m) * utils.SignOf(playlist.getVisTimeBar()), 5, ' ') #todo sign of...

            s = s + utils.Zeros_Strict(abs(playlist.getVisTimeStep()), 2) + utils.Zeros_Strict(playlist.getVisTimeTick(), 2) + ' '
        else:
            # BBB.BB.__.TTT
            s = utils.Zeros_Strict(playlist.getVisTimeBar(), 3, ' ') + utils.Zeros_Strict(abs(playlist.getVisTimeStep()), 2) + '  ' + utils.Zeros_Strict(playlist.getVisTimeTick(), 3)

        self.McuDevice.TimeDisplay.SetMessage(s)

    def OnWaitingForInput(self):
        """ Called when FL studio is in waiting mode """
        self.McuDevice.TimeDisplay.SetMessage('..........')

MackieCU = TMackieCU()

def OnInit():
    MackieCU.OnInit()

def OnDeInit():
    MackieCU.OnDeInit()

def OnDirtyMixerTrack(SetTrackNum):
    MackieCU.OnDirtyMixerTrack(SetTrackNum)

def OnRefresh(Flags):
    MackieCU.OnRefresh(Flags)

def OnMidiMsg(event):
    MackieCU.OnMidiMsg(event)

def OnSendTempMsg(Msg, Duration = 1000):
    MackieCU.OnSendMsg(Msg)

def OnUpdateBeatIndicator(Value):
    MackieCU.OnUpdateBeatIndicator(Value)

def OnUpdateMeters():
    MackieCU.OnUpdateMeters()

def OnIdle():
    MackieCU.OnIdle()

def OnWaitingForInput():
    MackieCU.OnWaitingForInput()
