# XTouch-FLStudio #
Behringer X-Touch for FL Studio Script (based on FL Studio MCU implementation)


## WHAT'S INCLUDED: ##

* Sends and Pan/Surround (stereo separation) swapped to reflect the labels
* Plugins now show their respective names
* Plugins allow navigating between them to see all 10 (using channel and fader bank buttons)
* Plugins when clicked on, take you to a list of plugin parameters, where you can navigate. 
* Plugin parameters can be adjusted using knobs
* When knob is pressed it flips between 0 and 1 (min and max value)
---
* Midi Tracks - focuses Playlist and upon press and jog wheel runs through patterns
* Inputs - focuses Mixer and sets goes to the location of currently selected Mixer track (it is then assigned to Fader 1)
* Audio Tracks - free for now to use wherever you like
* Audio Inst - focuses Channel Rack/Step Seq. and jog wheel goes through the instruments
* Aux - free for now
* Buses - focuses Mixer and sets fader 1 to first insert track (as far as it is track number > 99)
* Outputs - focuses Mixer and sets fader 1 as Master track
* User - focuses Browser
---
* F1-F8 remains Cut, Copy, Paste, etc. for now
* Ctrl + F1-F8 acts as Draw, Paint, Delete, Mute, etc.
* Shift + F1-F8 acts as F1-F8 on keyboard
---
* Automation is partially assigned for now
---
* Save, Cancel, Enter remains what they are
* Undo - works as intended (Undo/Redo). If you hold it and use the jog wheel, you can undo/redo further in history
---
* Marker - when clicked doesn't do anything for now
  * If you hold Marker and jog wheel jumps between markers
  * Control + Marker toggles a marker (adds or removes it)
  * Shift + Marker and jog wheel selects sections between markers
---
* Holding Cycle and Jog Wheel selects part of a song in the playlist
* Drop - punch-in
* Replace - punch-out
---
* Arrows next to the jog wheel can be used for navigation
* Zoom - when holding the central zoom button and using arrows, vertical and horizontal zoom activates on the playlist
---
* Control + Select links current Channel to selected Mixer Track

* Selecting mixer track when touching faders
* Mixer track numbers on the screens
---
* Some other bugs fixed and Python constants added for some of the buttons/faders

I have not touched the extender script simply because I don't own one and I wouldn't be able to test it.
