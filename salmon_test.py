#!/usr/bin/python
"""Unit tests for salmon.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json

import salmon
import source
from webutil import testutil


class FakeSource(source.Source):
  # {user id: {group id: {activity id, app id}}}
  activities = None
  user_id = 0

  def get_comments(self):
    pass


class HandlerTest(testutil.HandlerTest):

  def setUp(self):
    super(HandlerTest, self).setUp()
    self.reset()


