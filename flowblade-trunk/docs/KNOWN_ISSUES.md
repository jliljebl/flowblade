# Known Issues

This is list of bugs and defectes that are known to exist, but will probably not be fixed anytime soon.

#### 1. Selecting clip in timeline often blocks ability to drag / move / select tracks in awesomeWM

In awesomeWM there are often problems dragging clips. Instead of moving the clip, a file icon appears and is moved. 

The problem causing the bug is that awesome fires 'leave-notify-event' signals even when mouse has not left the timeline area.

**Status:** Problem is in another program, cannot be fixed in Flowblade

