#!/usr/bin/python
"""Unit tests for facebook.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json
import mox
import urllib
import urlparse
from webutil import webapp2

import facebook
import source
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
ATOM_SALMON = """\
<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom'>
  <id>tag:facebook.com,2012:10102828452385634_39170557</id>
  <author>
    <name>Ryan Barrett</name>
    <uri>acct:212038@facebook-webfinger.appspot.com</uri>
  </author>
  <thr:in-reply-to xmlns:thr='http://purl.org/syndication/thread/1.0'
    ref='tag:facebook.com,2012:10102828452385634'>
    tag:facebook.com,2012:10102828452385634
  </thr:in-reply-to>
  <content>moire patterns: the new look for spring.</content>
  <title>moire patterns: the new look for spring.</title>
  <updated>2012-05-21T02:25:25+0000</updated>
</entry>
"""


class FacebookTest(testutil.HandlerTest):

  def setUp(self):
    super(FacebookTest, self).setUp()
    self.facebook = facebook.Facebook(self.handler)

  def test_comment_to_salmon(self):
    self.assertEqual(ATOM_SALMON, self.facebook.comment_to_salmon(COMMENT_JSON))

  def test_comment_to_salmon_minimal(self):
    salmon = self.facebook.comment_to_salmon({'id': '123_456'})
    self.assertTrue('<id>tag:facebook.com,2012:123_456</id>' in salmon, salmon)

  def test_comment_to_salmon_bad_id(self):
    comment = dict(COMMENT_JSON)

    for id in '123_', '_123', '123':
      comment['id'] = id
      self.assertRaises(ValueError, self.facebook.comment_to_salmon, comment)

    del comment['id']
    self.assertRaises(ValueError, self.facebook.comment_to_salmon, comment)
