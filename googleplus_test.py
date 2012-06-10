#!/usr/bin/python
"""Unit tests for googleplus.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import googleplus
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
  'id_tag': 'tag:plus.google.com,2012:123',
  'author_name': 'Ryan Barrett',
  'author_uri': 'acct:103651231634018158746@gmail.com',
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
  'id_tag': 'tag:plus.google.com,2012:ccg0o1_OvkYgU_fVvw5-gO2rdf3',
  'author_name': 'fred',
  'author_uri': 'acct:222@gmail.com',
  # TODO: this should be the original domain link
  'in_reply_to_tag': 'tag:plus.google.com,2012:123',
  'content': 'i agree',
  'title': 'i agree',
  'updated': '2012-06-03T05:33:10.789Z',
  }


class GooglePlusTest(testutil.HandlerTest):

  def setUp(self):
    super(GooglePlusTest, self).setUp()
    self.googleplus = googleplus.GooglePlus(key_name='x')

  def test_activity_to_salmon_vars(self):
    self.assert_equals(ACTIVITY_SALMON_VARS,
                       self.googleplus.activity_to_salmon_vars(ACTIVITY_JSON))

  def test_activity_to_salmon_vars_minimal(self):
    salmon = self.googleplus.activity_to_salmon_vars({'id': '123'})
    self.assert_equals('tag:plus.google.com,2012:123', salmon['id_tag'])

  def test_activity_to_salmon_vars_with_in_reply_to(self):
    self.assert_equals(COMMENT_SALMON_VARS,
                       self.googleplus.activity_to_salmon_vars(COMMENT_JSON))
