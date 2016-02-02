#!/usr/bin/bash

ver=v0.35.4

rsync -rzzcP repo@projects.digithinkit.com:/repos/apps/electron/$ver/linux-x64 electron-bin
ln -s electron-bin/linux-x64/electron electron
