#!/usr/bin/python
"""Unit tests for twitter.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import twitter
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
  'in_reply_to_status_id': 456,
  }
SALMON_VARS = {
  'id_tag': 'tag:twitter.com,2012:123',
  'author_name': 'Ryan Barrett',
  'author_uri': 'acct:snarfed@twitter-webfinger.appspot.com',
  # TODO: this should be the original domain link
  'in_reply_to_tag': 'tag:twitter.com,2012:456',
  'content': 'moire patterns: the new look for spring.',
  'title': 'moire patterns: the new look for spring.',
  'updated': 'Mon, 21 May 2012 02:25:25 +0000',
  }

class TwitterTest(testutil.HandlerTest):

  def setUp(self):
    super(TwitterTest, self).setUp()
    self.twitter = twitter.Twitter(key_name='x')

  def test_tweet_to_salmon(self):
    self.assert_equals(SALMON_VARS, self.twitter.tweet_to_salmon_vars(TWEET_JSON))

  def test_tweet_to_salmon_minimal(self):
    salmon = self.twitter.tweet_to_salmon_vars({'id': 123})
    self.assert_equals('tag:twitter.com,2012:123', salmon['id_tag'])
