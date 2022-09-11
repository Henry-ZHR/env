#!/bin/bash

set -e

DIR=/sdcard/Documents/Rime

(cd android; ./generate.sh)

adb push /usr/share/rime-data/* $DIR
adb push *.yaml $DIR
adb push android/*.yaml $DIR
