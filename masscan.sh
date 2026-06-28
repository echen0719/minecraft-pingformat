#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Forgot to run as sudo boi"
  exit 1
fi

masscan 0.0.0.0-255.255.255.255 -p 25565 --rate $1 --exclude 255.255.255.255 -oJ output.json
rm paused.conf