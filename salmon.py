#!/usr/bin/python
"""Salmon API handler classes.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json
import logging
import re
import os
import urllib
from webob import exc
from webutil import webapp2

import appengine_config
import facebook
import source
# import twitter
from webutil import util

from google.appengine.ext.webapp.util import run_wsgi_app

# maps app id to source class
SOURCE = {
  'facebook-salmon': facebook.Facebook,
  # 'twitter-salmon': twitter.Twitter,
  }.get(appengine_config.APP_ID)

