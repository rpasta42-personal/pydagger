import logging, logging.config

logging.config.dictConfig({
   'version': 1,
   'disable_existing_loggers': False,  # this fixes the problem

   'formatters': {
      'standard': { #%(asctime)s
         'format'    :  '%(relativeCreated)d [%(levelname)s] %(name)s:%(funcName)s:%(lineno)i: %(message)s'
      },
   },
   'handlers': {
      'default': {
         'formatter' :  'standard',
         'level'     :  'DEBUG',
         'class'     :  'logging.StreamHandler',
      },
   },
   'loggers': {
      '': {
         'handlers'  :  ['default'],
         'level'     :  'DEBUG', #for every type (includes requests)
         #'level'     :  'WARNING', #for higher stuff
         'propagate' :  True
      },
      'requests': { #urllib3
         'level'     : 'CRITICAL' #'WARNING'
      }

   }
})


