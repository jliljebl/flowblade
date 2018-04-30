#!/bin/bash

#NatronRenderer -w Write2 1-10 /home/janne/test/natrontestout/frame###.png /home/janne/test/natrontest.ntp
RENDER_COMMAND=$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8
echo $RENDER_COMMAND
#NatronRenderer  $RENDER_COMMAND
