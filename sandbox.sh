#!/bin/sh

if [ $# -lt 2 ]; then
  echo "Usage: $0 HOME [BWRAP ARGS...] [--] COMMAND [ARGS...]"
  exit 1
fi

exec bwrap --unshare-all \
           --share-net \
           --die-with-parent \
           --ro-bind / / \
           --dev /dev \
           --tmpfs /home \
           --proc /proc \
           --tmpfs /run \
           --tmpfs /sys \
           --tmpfs /tmp \
           --dev-bind /dev/dri /dev/dri \
           --dev-bind /dev/nvidia0 /dev/nvidia0 \
           --dev-bind /dev/nvidiactl /dev/nvidiactl \
           --ro-bind /proc/driver/nvidia /proc/driver/nvidia \
           --ro-bind /run/dbus /run/dbus \
           --ro-bind /run/user/$UID/bus /run/user/$UID/bus \
           --ro-bind /run/user/$UID/pulse /run/user/$UID/pulse \
           --ro-bind /sys/dev/char /sys/dev/char \
           --ro-bind /sys/devices /sys/devices \
           --bind $1 ~ \
           --bind ~/.cache/fontconfig ~/.cache/fontconfig \
           --ro-bind ~/.config/fontconfig ~/.config/fontconfig \
           --ro-bind ~/.Xauthority ~/.Xauthority \
           --ro-bind /tmp/.X11-unix /tmp/.X11-unix \
           --chdir ~ \
           "${@:2}"
