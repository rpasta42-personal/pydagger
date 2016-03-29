#!/usr/bin/python3

import sh

date = sh.date()

date_split = date.split(' ')
before = date_split[0:3]
time = date_split[3]
after = date_split[4:]

time_split = time.split(':')
hour = int(time_split[0])
if hour > 12:
   time_split = time_split[1:]
   time_split.insert(0, str(hour-12))
   new_time = ':'.join(time_split)
   date_split[3] = new_time
   print(' '.join(date_split))
else:
   print(time)
