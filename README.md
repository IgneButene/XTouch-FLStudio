# XTouch-FLStudio #
Behringer X-Touch for FL Studio Script (based on FL Studio MCU implementation)


# WHAT'S INCLUDED: #

## Jogging ##
* Midi Tracks - focuses Playlist and upon press and jog wheel runs through patterns
* Inputs - focuses Mixer and sets goes to the location of currently selected Mixer track (it is then assigned to Fader 1)
* Audio Tracks - move between the playlist tracks
* Audio Inst - focuses Channel Rack/Step Seq. and jog wheel goes through the instruments
* Aux - moves through the docked channels (mixes)
* Buses - focuses Mixer and moves through the channels which names end with BUS or MIX
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
* Option + Select links current Channel to selected Mixer Track

* Selecting mixer track when touching faders
* Mixer track numbers on the screens
---
* Some other bugs fixed and Python constants added for some of the buttons/faders

## Sends ##
* Toggle of volume (for sidechain) can be done by holding Control + Encoder

## Plugins ##
* Plugins can be opened to changed their respective parameters via encoders
* Plugins screen can be opened/closed (Control + Encoder)
* Plugins values can be fine-tuned by holding Shift + Encoder, Alt + Encoder (or Control + Encoder for faster changes)
* Plugin presets can be shuffled (Control + Jog Wheel) while the plugin is open
* When knob is pressed it flips between min and max value

## Instruments ##
* Instruments (channel rack) are now displayed on the screen
* Instrument interface can be opened/closed (Control + Encoder)
* Plugins can be controller via encoders


I have not touched the extender script simply because I don't own one and I wouldn't be able to test it.

## AKNOWLEDGEMENT ##
* The latest version of the script is merged with the refactored version by @bramdebouvere (https://github.com/bramdebouvere/fltouch)