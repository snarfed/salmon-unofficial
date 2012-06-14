#!/usr/bin/python
"""Unit tests for googleplus.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import copy

import models
from googleplus import GooglePlus, GooglePlusService
from webutil import testutil

# test data
ACTIVITY_JSON = {
  'title': 'moire patterns!',
  'published': '2012-06-07T05:32:31.000Z',
  'updated': '2012-06-07T05:32:31.466Z',
  'id': '123',
  'actor': {
    'id': '103651231634018158746',
    'displayName': 'Ryan Barrett',
    },
  'object': {
    'content': 'moire patterns: the new look for spring.',
    'attachments': [{
        'objectType': 'article',
        'url': 'http://foo/bar',
        }],
    },
  }
ACTIVITY_SALMON_VARS = {
  'id': 'tag:plus.google.com,2012:123',
  'author_name': 'Ryan Barrett',
  'author_uri': 'acct:103651231634018158746@gmail.com',
  'in_reply_to': 'http://foo/bar',
  'content': 'moire patterns: the new look for spring.',
  'title': 'moire patterns!',
  'updated': '2012-06-07T05:32:31.000Z',
  }

COMMENT_JSON = {
  'id': 'ccg0o1_OvkYgU_fVvw5-gO2rdf3',
  'actor': {
    'id': '222',
    'displayName': 'fred',
    'url': 'http://fred',
    },
  'object': {
    'content': 'i agree',
    },
  'published': '2012-06-03T05:33:10.789Z',
  'inReplyTo': [{
      'id': '123',
      }],
  }
COMMENT_SALMON_VARS = {
  'id': 'tag:plus.google.com,2012:ccg0o1_OvkYgU_fVvw5-gO2rdf3',
  'author_name': 'fred',
  'author_uri': 'acct:222@gmail.com',
  'in_reply_to': 'http://foo/bar',
  'content': 'i agree',
  'title': 'i agree',
  'updated': '2012-06-03T05:33:10.789Z',
  }


class GooglePlusTest(testutil.HandlerTest):

  def setUp(self):
    super(GooglePlusTest, self).setUp()
    self.googleplus = GooglePlus(key_name='x')

    self.mox.StubOutWithMock(GooglePlusService, 'call')
    self.mox.StubOutWithMock(GooglePlusService, 'call_with_creds')

  def test_activity_to_salmon_vars(self):
    self.assert_equals(ACTIVITY_SALMON_VARS,
                       self.googleplus.activity_to_salmon_vars(ACTIVITY_JSON))

  def test_activity_to_salmon_vars_minimal(self):
    salmon = self.googleplus.activity_to_salmon_vars({'id': '123'})
    self.assert_equals('tag:plus.google.com,2012:123', salmon['id'])

  def test_comment_to_salmon_vars(self):
    expected = copy.deepcopy(COMMENT_SALMON_VARS)
    expected['in_reply_to'] = None
    self.assert_equals(expected,
                       self.googleplus.activity_to_salmon_vars(COMMENT_JSON))

  def test_get_salmon(self):
    GooglePlusService.call_with_creds('my gae user id', 'activities.list',
                                      userId='x', collection='public',
                                      maxResults=100)\
        .AndReturn({'items': [ACTIVITY_JSON]})
    GooglePlusService.call_with_creds('my gae user id', 'comments.list',
                                      activityId='123', maxResults=100)\
        .AndReturn({'items': [COMMENT_JSON]})
    self.mox.ReplayAll()

    self.googleplus.owner = models.User(key_name='my gae user id')
    self.assert_equals([ACTIVITY_SALMON_VARS, COMMENT_SALMON_VARS],
                       self.googleplus.get_salmon())


  def test_new(self):
    GooglePlusService.call('http placeholder', 'people.get', userId='me')\
        .AndReturn({'id': '1',
                    'displayName': 'Mr. Foo',
                    'url': 'http://my.g+/url',
                    'image': {'url': 'http://my.pic/small'},
                    })
    self.mox.ReplayAll()

    gp = GooglePlus.new(self.handler, http='http placeholder')
    self.assertEqual('1', gp.key().name())
    self.assertEqual('Mr. Foo', gp.name)
    self.assertEqual('http://my.pic/small', gp.picture)
    self.assertEqual('http://my.g+/url', gp.url)
    self.assertEqual(self.current_user_id, gp.owner.key().name())

