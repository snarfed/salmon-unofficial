#!/usr/bin/env python
"""Serves the HTML front page and discovery files.

The discovery files inside /.well-known/ include host-meta (XRD), and
host-meta.xrds (XRDS-Simple), and host-meta.jrd (JRD ie JSON).
"""

__author__ = 'Ryan Barrett <salmon@ryanb.org>'

import re
import urlparse

import salmon
import appengine_config
from webob import exc
from webutil import handlers
from webutil import webapp2

from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app


class Domain(db.Model):
  """A domain that we should send Salmon slaps to.

  The key name is the domain"""
  pass


class FrontPageHandler(handlers.TemplateHandler):
  """Renders and serves /, ie the front page. """

  def template_file(self):
    return 'templates/index.html'

  def template_vars(self):
    return {'domains': Domain.all()}


class AddDomainHandler(handlers.TemplateHandler):
  """Handles POSTs to /add_domain.  """

  def post(self):
    value = self.request.get('domain')
    parsed = urlparse.urlparse(value)
    if not parsed.netloc:
      parsed = urlparse.urlparse('http://' + value)

    domain = parsed.netloc
    if not domain:
      raise exc.HTTPBadRequest('No domain found in %r' % value)

    # strip exactly one dot from the right, if present
    if domain[-1:] == ".":
      domain = domain[:-1] 

    split = domain.split('.')
    if len (split) <= 1:
      raise exc.HTTPBadRequest('No TLD found in domain %r' % domain)

    # http://stackoverflow.com/questions/2532053/validate-hostname-string-in-python
    allowed = re.compile('(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)
    for part in split:
      if not allowed.match(part):
        raise exc.HTTPBadRequest('Bad component in domain: %r' % part)

    Domain(key_name=domain).save()
    self.redirect('/')


application = webapp2.WSGIApplication(
  [('/', FrontPageHandler),
   ('/add_domain', AddDomainHandler),
   ] + handlers.HOST_META_ROUTES,
  debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
