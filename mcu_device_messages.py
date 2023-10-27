import mcu_device

class McuDeviceMessages:
    def __init__(self, device: mcu_device.McuDevice):
        self.McuDevice = device
        self.MsgT = ["", ""]
        self.MsgDirty = False

    def SendMsg(self, Msg):
        self.MsgT[1] = Msg
        self.MsgDirty = True

    def UpdateMsg(self):
        if not self.MsgDirty:
            return
        
        self.McuDevice.SetTextDisplay(self.MsgT[1])
        self.MsgDirty = False