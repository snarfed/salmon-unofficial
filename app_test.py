#!/usr/bin/python
"""Unit tests for app.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import app
import facebook
from webutil import testutil


class AppTest(testutil.HandlerTest):

  def test_delete(self):
    facebook.Facebook(key_name='ryan').save()
    self.assertEqual(1, facebook.Facebook.all().count())

    resp = app.application.get_response('/delete?kind=Facebook&key_name=ryan',
                                        method='POST')
    self.assertEquals(302, resp.status_int, resp.body)
    self.assertEquals('http://localhost/', resp.headers['Location'])
    self.assertEqual(0, facebook.Facebook.all().count())
