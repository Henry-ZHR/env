#!/bin/sh

readonly DELAY=10s
readonly DIR=$HOME/.config/delayed-autostart

sleep $DELAY
cd $DIR
for app in *.desktop; do
  kioclient exec $app
done
