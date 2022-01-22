#!/bin/sh

source ~/.profile
exec sandbox \
     ~/Documents/Sandbox/Steam \
     --setenv GDK_SCALE 2 \
     -- \
     /usr/bin/steam \
     "$@"
