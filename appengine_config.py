"""App Engine settings.
"""

import sys
import os

# git submodules to allow importing from
for submodule in ('django-salmon',
                  'google-api-python-client',
                  'httplib2/python2',
                  'python-gflags',
                  ):
  sys.path.append(os.path.join(os.path.abspath("."), submodule))

from webutil.appengine_config import *

USER_KEY_HANDLER_SECRET = read('user_key_handler_secret')

