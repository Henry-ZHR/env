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
           --dev-bind-try /dev/nvidia0 /dev/nvidia0 \
           --dev-bind-try /dev/nvidiactl /dev/nvidiactl \
           --ro-bind-try /proc/driver/nvidia /proc/driver/nvidia \
           --ro-bind /run/dbus /run/dbus \
           --ro-bind /run/user/$(id -u)/bus /run/user/$(id -u)/bus \
           --ro-bind /run/user/$(id -u)/pulse /run/user/$(id -u)/pulse \
           --ro-bind /sys/block /sys/block \
           --ro-bind /sys/bus /sys/bus \
           --ro-bind /sys/class /sys/class \
           --ro-bind /sys/dev /sys/dev \
           --ro-bind /sys/devices /sys/devices \
           --ro-bind /tmp/.X11-unix /tmp/.X11-unix \
           --bind $1 ~ \
           --bind ~/.cache/fontconfig ~/.cache/fontconfig \
           --ro-bind ~/.config/fontconfig ~/.config/fontconfig \
           --ro-bind ~/.Xauthority ~/.Xauthority \
           --chdir ~ \
           "${@:2}"
