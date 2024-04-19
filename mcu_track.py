import mcu_knob_mode

class McuTrack:
    """ Represents data for a track on the XTouch """

    def __init__(self):
        self.TrackNum = 0 # The index of the mixer track in FL studio
        self.BaseEventID = 0
        self.KnobEventID = 0 
        self.KnobPressEventID = 0
        self.KnobResetEventID = 0
        self.KnobResetValue = 0
        self.KnobMode = mcu_knob_mode.SingleDot
        self.KnobCenter = 0
        self.KnobHeld = False
        self.KnobName = "" # The name of the knob that you will see on the screen when you turn it
        self.SliderEventID = 0
        self.SliderName = "" # The name of the slider that you will see on the screen when you slide it
        self.Dirty = False # Indicates that the mixer track has changed in FL studio
        self.Pinned = False # Indicates that the mixer track is pinned to the XTouch

    def copy(self):
        TrackCopy = McuTrack()
        TrackCopy.TrackNum = self.TrackNum
        TrackCopy.BaseEventID = self.BaseEventID
        TrackCopy.KnobEventID = self.KnobEventID
        TrackCopy.KnobPressEventID = self.KnobPressEventID
        TrackCopy.KnobResetEventID = self.KnobResetEventID
        TrackCopy.KnobResetValue = self.KnobResetValue
        TrackCopy.KnobMode = self.KnobMode
        TrackCopy.KnobCenter = self.KnobCenter
        TrackCopy.KnobHeld = self.KnobHeld
        TrackCopy.KnobName = self.KnobName
        TrackCopy.SliderEventID = self.SliderEventID
        TrackCopy.SliderName = self.SliderName
        TrackCopy.Dirty = self.Dirty
        
        return TrackCopy