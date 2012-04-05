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
import source_test
from webutil import testutil


class FakeSource(source.Source):
  # {user id: {group id: {activity id, app id}}}
  activities = None
  user_id = 0

  def get_activities(self, user_id=None, group_id=None, app_id=None,
                     activity_id=None, start_index=0, count=0):
    if user_id:
      ret = [a for a in self.activities if a['id'] == user_id]
    else:
      ret = self.activities

    return len(self.activities), ret[start_index:count + start_index]


class HandlerTest(testutil.HandlerTest):

  def setUp(self):
    super(HandlerTest, self).setUp()
    self.reset()

  def reset(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()
    salmon.SOURCE = FakeSource
    self.mox.StubOutWithMock(FakeSource, 'get_activities')

  def get_response(self, url, *args, **kwargs):
    kwargs.setdefault('start_index', 0)
    kwargs.setdefault('count', salmon.ITEMS_PER_PAGE)

    FakeSource.get_activities(*args, **kwargs)\
        .AndReturn((9, [{'foo': 'bar'}]))
    self.mox.ReplayAll()

    return salmon.application.get_response(url)

  def check_request(self, url, *args, **kwargs):
    resp = self.get_response(url, *args, **kwargs)
    self.assertEquals(200, resp.status_int)
    self.assert_equals({
        'startIndex': int(resp.request.get('startIndex', 0)),
        'itemsPerPage': 1,
        'totalResults': 9,
        'items': [{'foo': 'bar'}],
        'filtered': False,
        'sorted': False,
        'updatedSince': False,
        },
      json.loads(resp.body))

  def test_all_defaults(self):
    self.check_request('/')

