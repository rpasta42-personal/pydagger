#!/usr/bin/bash

rsync -rzzcP repo@projects.digithinkit.com:/repos/apps/electron/v0.33.3 electron-bin
ln -s electron-bin/v0.33.3/linux-x64/electron electron
