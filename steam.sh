#!/bin/sh

exec sandbox \
     ~/Documents/Sandbox/Steam \
     --setenv GDK_SCALE 2 \
     -- \
     /usr/bin/steam \
     "$@"
