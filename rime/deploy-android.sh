#!/bin/bash

set -e

DIR=/sdcard/Documents/Rime/user

(cd android; ./generate.sh)

adb push *.yaml $DIR
adb push android/*.yaml $DIR
