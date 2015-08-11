#!/usr/bin/python3

#Pycloak requires a specific project directory tree to work:
#  RootOfProject
#  |--src
#     |--pycloak
#     |--<MAIN_PROJECT_FILE>.py

import sys
sys.path.append('pycloak/src')
import icloak

debug = False
app_name = 'Sample App'

app = icloak.Application(debug, app_name, __file__)

