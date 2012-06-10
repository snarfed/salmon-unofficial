#!/usr/bin/python
"""Unit tests for app.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import app
from webutil import testutil

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import db


class AppTest(testutil.HandlerTest):

  def setUp(self):
    super(AppTest, self).setUp()
    self.datastore_stub = self.testbed.get_stub('datastore_v3')

  def test_add_good_domain(self):
    for domain in 'asdf.com', 'https://asdf.com/', 'asdf.com/foo?bar#baz':
      self.datastore_stub.Clear()

      resp = app.application.get_response('/add_domain?domain=%s' % domain, method='POST')
      self.assertEquals(302, resp.status_int, resp.body)
      self.assertEquals('http://localhost/', resp.headers['Location'])

      domains = app.Domain.all().fetch(10)
      self.assertEqual(1, len(domains))
      self.assertEqual('asdf.com', domains[0].key().name())

  def test_add_bad_domain(self):
    for domain in '', '  ', 'com', 'com.', 'a/b/c':
      resp = app.application.get_response('/add_domain?domain=%s' % domain,
                                          method='POST')
      self.assertEquals(400, resp.status_int, resp.body)
      self.assertEqual(0, app.Domain.all().count())
