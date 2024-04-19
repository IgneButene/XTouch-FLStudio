import device
import ui
import time
import utils
import mixer
import midi
import transport
import general
import channels
import plugins

import mcu_constants
import mcu_device
import mcu_track
import mcu_pages
import mcu_knob_mode
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
class McuBaseClass():
    """ Shared base class for both the extender and the main mackie unit """

    def __init__(self, device: mcu_device.McuDevice, 
                 jog: mcu_device_jog.McuDeviceJog, 
                 modifiers: mcu_device_modifiers.McuDeviceModifiers,
                 leds: mcu_device_leds.McuDeviceLeds,
                 messages: mcu_device_messages.McuDeviceMessages,
                 transport: mcu_device_transport.McuDeviceTransport,
                 faders: mcu_device_faders.McuDeviceFaders,
                 utility: mcu_device_utility.McuDeviceUtility,
                 functions: mcu_device_functions.McuDeviceFunctions,
                 automation: mcu_device_automation.McuDeviceAutomation):
    
        self.Tracks = [mcu_track.McuTrack() for i in range(0)] # empty array, since "import typing" is not supported
        self.PinnedTracks = dict()


        self.Shift = False # indicates that the shift button is pressed

        self.FirstTrack = 0 # the count mode for the tracks (0 = normal, 1 = free mode)
        self.FirstTrackT = [0, 0]

        self.FreeCtrlT = [0 for x in range(mcu_constants.FreeTrackCount + 1)]  # 64+1 sliders

        self.Page = 0
        self.Flip = False
        
        self.CurPluginID = -1
        self.CurPluginOffset = 0
        self.PluginParamOffset = 0

        self.SmoothSpeed = 0

        self.McuDevice = device
        self.McuDeviceJog = jog
        self.McuDeviceModifiers = modifiers
        self.McuDeviceLeds = leds
        self.McuDeviceMessages = messages
        self.McuDeviceTransport = transport
        self.McuDeviceFaders = faders
        self.McuDeviceUtility = utility
        self.McuDeviceFunctions = functions
        self.McuDeviceAutomation = automation

    def OnInit(self):
        """ Called when the script has been started """
        self.FirstTrackT[0] = 1
        self.FirstTrack = 0
        self.SmoothSpeed = 0 # TODO: is not required if OnInit is not called more than once, need to check if this is the case

        device.setHasMeters()
        
        # set free mode faders to center
        for m in range(0, len(self.FreeCtrlT)):
            self.FreeCtrlT[m] = 8192 

        # init hardware
        self.McuDevice.Initialize()
        self.McuDevice.SetBackLightTimeout(2) # backlight timeout to 2 minutes

    def OnDeInit(self):
        """ Called before the script will be stopped """
        self.McuDevice.DisableMeters()

        if device.isAssigned():
            if ui.isClosing():
                self.McuDevice.SetTextDisplay(ui.getProgTitle() + ' session closed at ' + time.ctime(time.time()), 0, skipIsAssignedCheck = True)
            else:
                self.McuDevice.SetTextDisplay('', skipIsAssignedCheck = True)

            self.McuDevice.SetTextDisplay('', 1, skipIsAssignedCheck = True)
            self.McuDevice.SetScreenColors(skipIsAssignedCheck = True)

    def OnDirtyMixerTrack(self, SetTrackNum):
        """
        Called on mixer track(s) change, 'SetTrackNum' indicates track index of track that changed or -1 when all tracks changed
        collect info about 'dirty' tracks here but do not handle track(s) refresh, wait for OnRefresh event with HW_Dirty_Mixer_Controls flag
        """
        for m in range(0, len(self.Tracks)):
            if (self.Tracks[m].TrackNum == SetTrackNum) | (SetTrackNum == -1):
                self.Tracks[m].Dirty = True

    def UpdateTextDisplay(self):
        """ Updates the mixer track names and colors """
        # Update names
        s1 = ''
        for m in range(0, len(self.Tracks) - 1):
            s = ''
            if (self.Page == mcu_pages.Effects) | (self.Page == mcu_pages.Instruments):
                s = self.DisplayName(self.Tracks[m].SliderName)
            else:
                s = tracknames.GetAsciiSafeTrackName(self.Tracks[m].TrackNum, self.Tracks[m].Pinned, 7)
            for n in range(1, 7 - len(s) + 1):
                s = s + ' '
            s1 = s1 + s

        self.McuDevice.SetTextDisplay(s1, 1)

        # Update colors
        if self.Page == mcu_pages.Instruments:
            self.McuDevice.SetScreenColors() # all white
        else:
            colorArr = []
            for m in range(0, len(self.Tracks) - 1):
                c = mixer.getTrackColor(self.Tracks[m].TrackNum)
                colorArr.append(c)
            self.McuDevice.SetScreenColors(colorArr)

    def UpdateMeterMode(self):
        self.McuDevice.ClearMeters()
        self.McuDevice.DisableMeters() #TODO: check if it's actually required to disable and then enable again here

        # reset stuff
        self.UpdateTextDisplay()
        self.McuDevice.EnableMeters()

    def OnUpdateMeters(self):
        """ Called when peak meters have updated values """

        for track in self.McuDevice.tracksWithMeters:
            trackNum = -1
            if self.Page == mcu_pages.Instruments:
                if self.Tracks[track.index].TrackNum < channels.channelCount():
                    trackNum = channels.getTargetFxTrack(self.Tracks[track.index].TrackNum)
            else:
                trackNum = self.Tracks[track.index].TrackNum
            if trackNum >= 0:
                currentPeak = mixer.getTrackPeaks(trackNum, midi.PEAK_LR_INV)
                track.meter.SetValue(currentPeak)

    def OnIdle(self):
        """ Called from time to time. Can be used to do some small tasks, mostly UI related """
        self.McuDeviceMessages.UpdateMsg()

    def UpdateColT(self):
        firstTrackNum = self.FirstTrackT[self.FirstTrack]
        CurID = mixer.getTrackPluginId(mixer.trackNumber(), 0)

        for i in range(0, len(self.Tracks)):
            self.Tracks[i].KnobPressEventID = -1

            # mixer
            if i == 8:
                self.Tracks[i].TrackNum = -2
                self.Tracks[i].BaseEventID = midi.REC_MainVol
                self.Tracks[i].SliderEventID = self.Tracks[i].BaseEventID
                self.Tracks[i].SliderName = 'Master Vol'
            else:
                self.Tracks[i].TrackNum = midi.TrackNum_Master + ((firstTrackNum + i) % mixer.trackCount())
                if self.Page == mcu_pages.Instruments:
                    if self.Tracks[i].TrackNum < channels.channelCount():
                        self.Tracks[i].BaseEventID = channels.getRecEventId(self.Tracks[i].TrackNum)
                else:
                    self.Tracks[i].BaseEventID = mixer.getTrackPluginId(self.Tracks[i].TrackNum, 0)
                self.Tracks[i].SliderEventID = self.Tracks[i].BaseEventID + midi.REC_Mixer_Vol
                s = tracknames.GetAsciiSafeTrackName(self.Tracks[i].TrackNum, self.Tracks[i].Pinned)
                self.Tracks[i].SliderName = s + ' - Vol'

                self.Tracks[i].KnobEventID = -1
                self.Tracks[i].KnobResetEventID = -1
                self.Tracks[i].KnobResetValue = midi.FromMIDI_Max >> 1
                self.Tracks[i].KnobName = ''
                self.Tracks[i].KnobMode = mcu_knob_mode.BoostCut # parameter, pan, volume, off
                self.Tracks[i].KnobCenter = -1

                if self.Page == mcu_pages.Pan:
                    self.Tracks[i].KnobEventID = self.Tracks[i].BaseEventID + midi.REC_Mixer_Pan
                    self.Tracks[i].KnobResetEventID = self.Tracks[i].KnobEventID
                    self.Tracks[i].KnobName = tracknames.GetAsciiSafeTrackName(self.Tracks[i].TrackNum, self.Tracks[i].Pinned) + ' - ' + 'Pan'
                elif self.Page == mcu_pages.Stereo:
                    self.Tracks[i].KnobEventID = self.Tracks[i].BaseEventID + midi.REC_Mixer_SS
                    self.Tracks[i].KnobResetEventID = self.Tracks[i].KnobEventID
                    self.Tracks[i].KnobName = tracknames.GetAsciiSafeTrackName(self.Tracks[i].TrackNum, self.Tracks[i].Pinned) + ' - ' + 'Sep'
                elif self.Page == mcu_pages.Sends:
                    self.Tracks[i].KnobEventID = CurID + midi.REC_Mixer_Send_First + self.Tracks[i].TrackNum
                    s = mixer.getEventIDName(self.Tracks[i].KnobEventID)
                    self.Tracks[i].KnobName = s
                    self.Tracks[i].KnobResetValue = round(12800 * midi.FromMIDI_Max / 16000)
                    self.Tracks[i].KnobCenter = mixer.getRouteSendActive(mixer.trackNumber(),self.Tracks[i].TrackNum)
                    if self.Tracks[i].KnobCenter == 0:
                        self.Tracks[i].KnobMode = mcu_knob_mode.Off
                    else:
                        self.Tracks[i].KnobMode = mcu_knob_mode.Wrap
                elif self.Page == mcu_pages.Effects:
                    if self.CurPluginID == -1: # Plugin not selected
                        CurID = mixer.getTrackPluginId(mixer.trackNumber(), i)
                        self.Tracks[i].KnobEventID = CurID + midi.REC_Plug_MixLevel
                        s = mixer.getEventIDName(self.Tracks[i].KnobEventID)
                        self.Tracks[i].KnobName = s
                        self.Tracks[i].KnobResetValue = midi.FromMIDI_Max

                        IsValid = mixer.isTrackPluginValid(mixer.trackNumber(), i + self.CurPluginOffset)
                        IsEnabledAuto = mixer.isTrackAutomationEnabled(mixer.trackNumber(), i + self.CurPluginOffset)
                        if IsValid:
                            self.Tracks[i].KnobMode = mcu_knob_mode.Wrap
                            #self.Tracks[i].KnobPressEventID = CurID + midi.REC_Plug_Mute
                            self.Tracks[i].SliderName = plugins.getPluginName(mixer.trackNumber(), i + self.CurPluginOffset)
                        else:
                            self.Tracks[i].KnobMode = mcu_knob_mode.Off
                            self.Tracks[i].SliderName = ''
                        
                        self.Tracks[i].KnobCenter = int(IsValid & IsEnabledAuto)
                    else: # Plugin selected
                        CurID = mixer.getTrackPluginId(mixer.trackNumber(), i + self.CurPluginOffset)
                        if i + self.PluginParamOffset < plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset):
                            self.Tracks[i].SliderName = plugins.getParamName(i + self.PluginParamOffset, mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset)
                        else:
                            self.Tracks[i].SliderName = ''
                        self.Tracks[i].KnobEventID = -1
                        self.Tracks[i].KnobMode = mcu_knob_mode.Off
                        self.Tracks[i].SliderEventID = -1
                elif self.Page == mcu_pages.Equalizer:
                    if self.McuDevice.isExtender or i >= 6:
                        # disable encoders on extenders and tracks > 6
                        self.Tracks[i].SliderEventID = -1
                        self.Tracks[i].KnobEventID = -1
                        self.Tracks[i].KnobMode = mcu_knob_mode.Off
                    elif i < 3:
                        # gain & freq
                        self.Tracks[i].SliderEventID = CurID + midi.REC_Mixer_EQ_Gain + i
                        self.Tracks[i].KnobResetEventID = self.Tracks[i].SliderEventID
                        s = mixer.getEventIDName(self.Tracks[i].SliderEventID)
                        self.Tracks[i].SliderName = s
                        self.Tracks[i].KnobEventID = CurID + midi.REC_Mixer_EQ_Freq + i
                        s = mixer.getEventIDName(self.Tracks[i].KnobEventID)
                        self.Tracks[i].KnobName = s
                        self.Tracks[i].KnobResetValue = midi.FromMIDI_Max >> 1
                        self.Tracks[i].KnobCenter = -2
                        self.Tracks[i].KnobMode = mcu_knob_mode.SingleDot
                    else:
                        # Q
                        self.Tracks[i].SliderEventID = CurID + midi.REC_Mixer_EQ_Q + i - 3
                        self.Tracks[i].KnobResetEventID = self.Tracks[i].SliderEventID
                        s = mixer.getEventIDName(self.Tracks[i].SliderEventID)
                        self.Tracks[i].SliderName = s
                        self.Tracks[i].KnobEventID = self.Tracks[i].SliderEventID
                        self.Tracks[i].KnobName = self.Tracks[i].SliderName
                        self.Tracks[i].KnobResetValue = 17500
                        self.Tracks[i].KnobCenter = -1
                        self.Tracks[i].KnobMode = mcu_knob_mode.Wrap
                elif self.Page == mcu_pages.Instruments:
                    if self.CurPluginID == -1: # Plugin not selected
                        IsValid = i + self.CurPluginOffset < channels.channelCount()
                        if IsValid:
                            CurID = channels.getRecEventId(i + self.CurPluginOffset)
                            self.Tracks[i].KnobEventID = CurID + midi.REC_Chan_Pan
                            self.Tracks[i].KnobName = channels.getChannelName(i + self.CurPluginOffset) + ' - ' + 'Pan'
                            #self.Tracks[i].KnobPressEventID = CurID + midi.REC_Plug_Mute
                            self.Tracks[i].SliderEventID = CurID + midi.REC_Chan_Vol
                            self.Tracks[i].SliderName = channels.getChannelName(i + self.CurPluginOffset)
                        else:
                            self.Tracks[i].KnobMode = mcu_knob_mode.Off
                            self.Tracks[i].SliderName = ''
                        
                        self.Tracks[i].KnobCenter = int(IsValid)
                    else: # Plugin selected
                        if i + self.PluginParamOffset < plugins.getParamCount(self.CurPluginID + self.CurPluginOffset):
                            self.Tracks[i].SliderName = plugins.getParamName(i + self.PluginParamOffset, self.CurPluginID + self.CurPluginOffset)
                        else:
                            self.Tracks[i].SliderName = ''
                        self.Tracks[i].KnobEventID = -1
                        self.Tracks[i].KnobMode = mcu_knob_mode.Off
                        self.Tracks[i].SliderEventID = -1
                # self.Flip knob & slider
                if self.Flip:
                    self.Tracks[i].KnobEventID, self.Tracks[i].SliderEventID = utils.SwapInt(self.Tracks[i].KnobEventID, self.Tracks[i].SliderEventID)
                    s = self.Tracks[i].SliderName
                    self.Tracks[i].SliderName = self.Tracks[i].KnobName
                    self.Tracks[i].KnobName = s
                    self.Tracks[i].KnobMode = mcu_knob_mode.Wrap
                    if not (self.Page in [mcu_pages.Sends, mcu_pages.Effects, mcu_pages.Equalizer if self.McuDevice.isExtender else -1 ]):
                        self.Tracks[i].KnobCenter = -1
                        self.Tracks[i].KnobResetValue = round(12800 * midi.FromMIDI_Max / 16000)
                        self.Tracks[i].KnobResetEventID = self.Tracks[i].KnobEventID

            # override with pinned tracks
            if self.PinnedTracks.get(str(i)) != None:
                self.Tracks[i] = self.PinnedTracks[str(i)].copy()
                self.Tracks[i].Pinned = True
                self.Tracks[i].SliderName += '*';

            self.UpdateTrack(i)

    def UpdateTrack(self, Num):
        """ Updates the sliders, buttons & rotary encoders for a specific track """

        # do not process tracks above 8 on extenders
        if self.McuDevice.isExtender and Num >= 8:
            return
        
        if device.isAssigned():
            sv = mixer.getEventValue(self.Tracks[Num].SliderEventID)

            if Num < 8:
                # V-Pot
                center = self.Tracks[Num].KnobCenter
                knobMode = self.Tracks[Num].KnobMode
                value = 0

                if self.Tracks[Num].KnobEventID >= 0:
                    m = mixer.getEventValue(self.Tracks[Num].KnobEventID, midi.MaxInt, False)
                    if center < 0:
                        if self.Tracks[Num].KnobResetEventID == self.Tracks[Num].KnobEventID:
                            center = int(m != self.Tracks[Num].KnobResetValue)
                        else:
                            center = int(sv != self.Tracks[Num].KnobResetValue)

                    if knobMode == mcu_knob_mode.SingleDot or knobMode == mcu_knob_mode.BoostCut:
                        value = 1 + round(m * (10 / midi.FromMIDI_Max))
                    elif knobMode == mcu_knob_mode.Wrap:
                        value = round(m * (11 / midi.FromMIDI_Max))
                    else:
                        print('Unsupported knob mode')
                else:
                    if self.Page == mcu_pages.Effects:
                        # Plugin Parameter Value
                        if int(Num + self.PluginParamOffset) < plugins.getParamCount(mixer.trackNumber(), int(self.CurPluginID + self.CurPluginOffset)):
                            paramValue = plugins.getParamValue(int(Num + self.PluginParamOffset), mixer.trackNumber(), int(self.CurPluginID + self.CurPluginOffset))
                            # 32..43
                            value = round(paramValue * 11 + 32)
                    elif self.Page == mcu_pages.Instruments:
                        # Plugin Parameter Value
                        if self.CurPluginID + self.CurPluginOffset >= 0 and self.CurPluginID + self.CurPluginOffset < channels.channelCount():
                            if int(Num + self.PluginParamOffset) < plugins.getParamCount(int(self.CurPluginID + self.CurPluginOffset)):
                                paramValue = plugins.getParamValue(int(Num + self.PluginParamOffset), int(self.CurPluginID + self.CurPluginOffset))
                                # 32..43
                                value = round(paramValue * 11 + 32)
                # device.midiOutNewMsg(midi.MIDI_CONTROLCHANGE + ((0x30 + Num) << 8) + (data1 << 16), self.Tracks[Num].LastValueIndex)

                self.McuDevice.GetTrack(Num).knob.setLedsValue(knobMode, center, value)


                # arm, solo, mute
                if self.Page == mcu_pages.Instruments:
                    if self.Tracks[Num].TrackNum < channels.channelCount():
                        self.McuDevice.GetTrack(Num).buttons.SetMuteButton(channels.isChannelMuted(self.Tracks[Num].TrackNum), True)
                        self.McuDevice.GetTrack(Num).buttons.SetSoloButton(channels.isChannelSolo(self.Tracks[Num].TrackNum), True)
                else:
                    self.McuDevice.GetTrack(Num).buttons.SetArmButton(mixer.isTrackArmed(self.Tracks[Num].TrackNum), transport.isRecording(), True)
                    self.McuDevice.GetTrack(Num).buttons.SetSoloButton(mixer.isTrackSolo(self.Tracks[Num].TrackNum), True)
                    self.McuDevice.GetTrack(Num).buttons.SetMuteButton(not mixer.isTrackEnabled(self.Tracks[Num].TrackNum), True)

            # slider
            self.McuDevice.GetTrack(Num).fader.SetLevelFromFlsFader(sv, True)

            self.Tracks[Num].Dirty = False

    def SetKnobValue(self, trackNumber, midiValue, resolution = midi.EKRes):
        """ Sets the value of a knob in FL Studio (for all except free page?) (and shows it on the display) """
        if self.CurPluginID != -1: # Plugin Selected
            if self.Page in [mcu_pages.Effects, mcu_pages.Instruments]:
                paramIndex = trackNumber + self.PluginParamOffset
                trackId = mixer.trackNumber()
                slotIndex = self.CurPluginID + self.CurPluginOffset
                if self.Page == mcu_pages.Instruments:
                    trackId = self.CurPluginID + self.CurPluginOffset
                    slotIndex = -1
                
                n = plugins.getParamValue(paramIndex, trackId, slotIndex)
                pv = round(midiValue / 127, 2)
                if self.McuDeviceModifiers.Control:
                    pv = pv * 10
                elif self.McuDeviceModifiers.Shift:
                    pv = pv * 0.01
                elif self.McuDeviceModifiers.Alt:
                    pv = pv * 0.1
                pv += n

                if midiValue == midi.MaxInt:
                    if n == 0:
                        pv = 1
                    else:
                        pv = 0
                if (pv <= 0):
                    pv = 0
                if (pv >= 1):
                    pv = 1

                if (pv >= 0) & (pv <= 1):
                    plugins.setParamValue(pv, paramIndex, trackId, slotIndex)
                    self.UpdateColT()
                    self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
                    self.UpdateTextDisplay()
                    s = plugins.getParamValueString(paramIndex, trackId, slotIndex)
                    self.McuDeviceMessages.SendMsg(self.Tracks[trackNumber].SliderName + ': ' + s)

        if not (self.Tracks[trackNumber].KnobEventID >= 0) & (self.Tracks[trackNumber].KnobMode != mcu_knob_mode.Off):
            return
        
        if midiValue == midi.MaxInt:
            if self.Page == mcu_pages.Effects:
                if self.McuDeviceModifiers.Control: # Only Focus Plugin
                    activeEffect = mixer.getActiveEffectIndex()
                    
                    if (activeEffect != None) and (activeEffect[0] == mixer.trackNumber()) & (activeEffect[1] == trackNumber + self.CurPluginOffset):
                        ui.escape()
                    else:
                        mixer.focusEditor(mixer.trackNumber(), trackNumber + self.CurPluginOffset) # Show Plugin
                else: # Select Plugin
                    if plugins.isValid(mixer.trackNumber(), trackNumber + self.CurPluginOffset):
                        mixer.focusEditor(mixer.trackNumber(), trackNumber + self.CurPluginOffset) # Show Plugin
                        self.CurPluginID = trackNumber

                self.PluginParamOffset = 0
                self.UpdateColT()
                self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
                self.UpdateTextDisplay()
                return
            elif self.Page == mcu_pages.Instruments:
                if self.McuDeviceModifiers.Control:
                    activeEffect = channels.showEditor(trackNumber + self.CurPluginOffset, -1)
                else: # Select Plugin
                    if plugins.isValid(trackNumber + self.CurPluginOffset):
                        channels.showEditor(trackNumber + self.CurPluginOffset, 1) # Show Plugin
                        self.CurPluginID = trackNumber
                self.PluginParamOffset = 0
                self.UpdateColT()
                self.McuDeviceLeds.UpdateMasterSectionLEDs(self.Page, self.Flip, self.SmoothSpeed, self.Tracks)
                self.UpdateTextDisplay()
                return

            else:
                mixer.automateEvent(self.Tracks[trackNumber].KnobResetEventID, self.Tracks[trackNumber].KnobResetValue, midi.REC_MIDIController, self.SmoothSpeed)
        else:
            mixer.automateEvent(self.Tracks[trackNumber].KnobEventID, midiValue, midi.REC_Controller, self.SmoothSpeed, 1, resolution)

        # show the value of the knob on the display
        n = mixer.getAutoSmoothEventValue(self.Tracks[trackNumber].KnobEventID)
        s = mixer.getEventIDValueString(self.Tracks[trackNumber].KnobEventID, n)
        if s !=  '':
            s = ': ' + s
        self.McuDeviceMessages.SendMsg(self.Tracks[trackNumber].KnobName + s)

    def OnSendMsg(self, Msg):
        self.McuDeviceMessages.SendMsg(Msg)

    # Display shortened name to fit to 7 characters (e.g., Fruity Chorus = FChorus, EQ Enhancer = EQEnhan)
    def DisplayName(self, name):
        if name == '':
            return ''
        
        words = name.split()
        if len(words) == 0:
            return ''
        
        shortName = ''

        for w in words:
            first = True
            for c in w:
                if c.isupper():
                    shortName += c
                elif first:
                    shortName += c
                else:
                    break
                first = False
        
        lastWord = words[len(words)-1]
        shortName += lastWord[1:]
                
        return shortName[0:7]
