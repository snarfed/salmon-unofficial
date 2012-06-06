#!/usr/bin/python
"""Unit tests for twitter.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json

import twitter
import source
from webutil import testutil

# test data
TWEET_JSON = {
  'id': 123,
  'created_at': 'Mon, 21 May 2012 02:25:25 +0000',
  'entities': {'urls': [{'display_url': 'example.com/xyz',
                         'expanded_url': 'http://example.com/xyz',
                         'url': 'http://t.co/AhhEkuxo'},
                        ]},
  'from_user': 'snarfed',
  'from_user_name': 'Ryan Barrett',
  'text': 'moire patterns: the new look for spring.',
  # 'in_reply_to_status_id': 456,
  }

ATOM_SALMON = """\
<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom'>
  <id>tag:twitter.com,2012:123</id>
  <author>
    <name>Ryan Barrett</name>
    <uri>acct:snarfed@twitter-webfinger.appspot.com</uri>
  </author>
  <thr:in-reply-to xmlns:thr='http://purl.org/syndication/thread/1.0'
    ref='tag:twitter.com,2012:456'>
    tag:twitter.com,2012:456
  </thr:in-reply-to>
  <content>moire patterns: the new look for spring.</content>
  <title>moire patterns: the new look for spring.</title>
  <updated>2012-05-21T02:25:25+0000</updated>
</entry>"""


class TwitterTest(testutil.HandlerTest):

  def setUp(self):
    super(TwitterTest, self).setUp()
    self.twitter = twitter.Twitter(self.handler)

  def test_comment_to_salmon(self):
    self.assert_multiline_equals(ATOM_SALMON,
                                 self.twitter.comment_to_salmon(TWEET_JSON))

  # def test_comment_to_salmon_minimal(self):
  #   salmon = self.twitter.comment_to_salmon({'id': '123_456'})
  #   self.assertTrue('<id>tag:twitter.com,2012:123_456</id>' in salmon)

  # def test_comment_to_salmon_bad_id(self):
  #   comment = dict(TWEET_JSON)

  #   for id in '123_', '_123', '123':
  #     comment['id'] = id
  #     self.assertRaises(ValueError, self.twitter.comment_to_salmon, comment)

  #   del comment['id']
  #   self.assertRaises(ValueError, self.twitter.comment_to_salmon, comment)
