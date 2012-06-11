#!/usr/bin/python
"""Unit tests for twitter.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import twitter
from twitter import TwitterSearch
from webutil import testutil

from google.appengine.ext import db


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


class TwitterSearchTest(testutil.HandlerTest):

  def setUp(self):
    super(TwitterSearchTest, self).setUp()
    self.twitter = TwitterSearch(key_name='x')
    self.datastore_stub = self.testbed.get_stub('datastore_v3')

  def test_tweet_to_salmon(self):
    self.assert_equals(SALMON_VARS, self.twitter.tweet_to_salmon_vars(TWEET_JSON))

  def test_tweet_to_salmon_minimal(self):
    salmon = self.twitter.tweet_to_salmon_vars({'id': 123})
    self.assert_equals('tag:twitter.com,2012:123', salmon['id_tag'])

  def test_add_good_domain(self):
    for domain in 'asdf.com', 'https://asdf.com/', 'asdf.com/foo?bar#baz':
      self.datastore_stub.Clear()

      resp = twitter.application.get_response('/twitter/add?domain=%s' % domain,
                                              method='POST')
      self.assertEquals(302, resp.status_int, resp.body)
      self.assertEquals('http://localhost/', resp.headers['Location'])

      searches = TwitterSearch.all().fetch(10)
      self.assertEqual(1, len(searches))
      self.assertEqual('asdf.com', searches[0].key().name())

  def test_add_bad_domain(self):
    for domain in '', '  ', 'com', 'com.', 'a/b/c':
      resp = twitter.application.get_response('/twitter/add?domain=%s' % domain,
                                              method='POST')
      self.assertEquals(400, resp.status_int, resp.body)
      self.assertEqual(0, TwitterSearch.all().count())
