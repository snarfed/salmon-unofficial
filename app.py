#!/usr/bin/env python
"""Serves the HTML front page and discovery files.

The discovery files inside /.well-known/ include host-meta (XRD), and
host-meta.xrds (XRDS-Simple), and host-meta.jrd (JRD ie JSON).
"""

__author__ = 'Ryan Barrett <salmon@ryanb.org>'

import salmon
import appengine_config
from webutil import handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class FrontPageHandler(handlers.TemplateHandler):
  """Renders and serves /, ie the front page.
  """
  def template_file(self):
    return salmon.SOURCE.FRONT_PAGE_TEMPLATE

  def template_vars(self):
    return {'domain': salmon.SOURCE.DOMAIN,
            'auth_url': salmon.SOURCE.AUTH_URL,
            }


def main():
  application = webapp.WSGIApplication(
      [('/', FrontPageHandler)] + handlers.HOST_META_ROUTES,
      debug=appengine_config.DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
