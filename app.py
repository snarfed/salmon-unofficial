#!/usr/bin/env python
"""Serves the HTML front page and discovery files.

The discovery files inside /.well-known/ include host-meta (XRD), and
host-meta.xrds (XRDS-Simple), and host-meta.jrd (JRD ie JSON).
"""

__author__ = 'Ryan Barrett <salmon@ryanb.org>'

import itertools
import re
import urlparse

import appengine_config
import facebook
import googleplus
import twitter
from webutil import handlers
from webutil import webapp2

from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app


class FrontPage(handlers.TemplateHandler):
  """Renders and serves /, ie the front page. """

  def template_file(self):
    return 'templates/index.html'

  def template_vars(self):
    sources = itertools.chain(facebook.Facebook.all().run(),
                              googleplus.GooglePlus.all().run(),
                              twitter.TwitterSearch.all().run())
    return {'sources': sources}


class DeleteSource(webapp2.RequestHandler):
  def post(self):
    kind = self.request.params['kind']
    key_name = self.request.params['key_name']

    # this reaches down into the implementation details of
    # SingleEGModel.shared_parent_key(). TODO: fix that.
    db.delete(db.Key.from_path('Parent', kind, kind, key_name))

    # TODO: remove tasks, etc.
    self.redirect('/')


application = webapp2.WSGIApplication(
  [('/', FrontPage),
   ('/delete', DeleteSource),
   ] + handlers.HOST_META_ROUTES,
  debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
