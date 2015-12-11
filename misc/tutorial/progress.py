#!/usr/bin/env python

from pycloak.shellutils import ProgressBar
import time

p = ProgressBar()

for x in range(0, 100):
   time.sleep(0.1)
   p.update(x, 'Hello', 20)
