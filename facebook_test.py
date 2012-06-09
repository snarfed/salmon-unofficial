#!/usr/bin/python
"""Unit tests for facebook.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import facebook
from webutil import testutil

# test data
COMMENT_JSON = {
  'id': '10102828452385634_39170557',
  'from': {
    'name': 'Ryan Barrett',
    'id': '212038'
  },
  'message': 'moire patterns: the new look for spring.',
  'can_remove': True,
  'created_time': '2012-05-21T02:25:25+0000',
  'type': 'comment',
}
SALMON_VARS = {
  'id_tag': 'tag:facebook.com,2012:10102828452385634_39170557',
  'author_name': 'Ryan Barrett',
  'author_uri': 'acct:212038@facebook-webfinger.appspot.com',
  # TODO: this should be the original domain link
  'in_reply_to_tag': 'tag:facebook.com,2012:10102828452385634',
  'content': 'moire patterns: the new look for spring.',
  'title': 'moire patterns: the new look for spring.',
  'updated': '2012-05-21T02:25:25+0000',
  }


class FacebookTest(testutil.HandlerTest):

  def setUp(self):
    super(FacebookTest, self).setUp()
    self.facebook = facebook.Facebook(self.handler)

  def test_comment_to_salmon_vars(self):
    self.assert_equals(
      SALMON_VARS, self.facebook.comment_to_salmon_vars(COMMENT_JSON))

  def test_comment_to_salmon_vars_minimal(self):
    salmon = self.facebook.comment_to_salmon_vars({'id': '123_456'})
    self.assert_equals('tag:facebook.com,2012:123_456', salmon['id_tag'])

  def test_comment_to_salmon_vars_bad_id(self):
    comment = dict(COMMENT_JSON)

    for id in '123_', '_123', '123':
      comment['id'] = id
      self.assertRaises(ValueError, self.facebook.comment_to_salmon_vars, comment)

    del comment['id']
    self.assertRaises(ValueError, self.facebook.comment_to_salmon_vars, comment)
