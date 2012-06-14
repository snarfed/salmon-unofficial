#!/usr/bin/python
"""Unit tests for twitter.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import copy
import json

import twitter
from twitter import TwitterSearch
from webutil import testutil

from google.appengine.ext import db


# test data
TWEETS_JSON = [
  # one embedded url for example.com, no replies
  {'id': 0,
   'created_at': 'Mon, 21 May 2012 02:25:25 +0000',
   'entities': {'urls': [{'display_url': 'example.com/xyz',
                          'expanded_url': 'http://example.com/xyz',
                          'url': 'http://t.co/AhhEkuxo'},
                         ]},
   'from_user': 'snarfed',
   'from_user_name': 'Ryan Barrett',
   'text': 'moire patterns: the new look for spring.',
   'in_reply_to_status_id': 456,
   },
  # two embedded urls, only one for example.com, one reply (below)
  {'id': 1,
   'created_at': 'Wed, 04 Jan 2012 20:10:28 +0000',
   'entities': {'urls': [{'display_url': 'bar.org/qwert',
                          'expanded_url': 'http://bar.org/qwert',
                          'url': 'http://t.co/ZhhEkuxo'},
                         {'display_url': 'example.com/asdf',
                          'url': 'http://example.com/asdf'},
                         ]},
   'from_user': 'user1',
   'from_user_name': 'user 1 name',
   'text': 'this is a tweet',
   },

  # no embedded urls
  {'id': 2,
   'created_at': 'Tue, 03 Jan 2012 16:17:16 +0000',
   'entities': {},
   'from_user': 'user2',
   'from_user_name': 'user 2 name',
   'text': 'this is also a tweet',
   },
  ]

MENTIONS_JSON = [
  # not a reply
  {'created_at': 'Sun, 01 Jan 2012 11:44:57 +0000',
   'entities': {'user_mentions': [{'id': 1, 'screen_name': 'user1'}]},
   'from_user': 'user4',
   'from_user_name': 'user 4 name',
   'id': 4,
   'text': 'boring',
   },
  # reply to tweet id 1 (above)
  {'created_at': 'Sun, 01 Jan 1970 00:00:01 +0000',
   'entities': {'user_mentions': [{'id': 1, 'screen_name': 'user1'}]},
   'from_user': 'user3',
   'from_user_name': 'user 3 name',
   'id': 3,
   'in_reply_to_status_id': 1,
   'text': '@user1 i hereby #reply',
   'to_user': 'user1',
   },
  ]

TWEETS_SALMON_VARS = [
  {'id': 'tag:twitter.com,2012:0',
   'author_name': 'Ryan Barrett',
   'author_uri': 'acct:snarfed@twitter-webfinger.appspot.com',
   'in_reply_to': 'http://example.com/xyz',
   'content': 'moire patterns: the new look for spring.',
   'title': 'moire patterns: the new look for spring.',
   'updated': '2012-05-21T02:25:25',
   },
  {'id': 'tag:twitter.com,2012:1',
   'author_name': 'user 1 name',
   'author_uri': 'acct:user1@twitter-webfinger.appspot.com',
   'in_reply_to': 'http://example.com/asdf',
   'content': 'this is a tweet',
   'title': 'this is a tweet',
    'updated': '2012-01-04T20:10:28',
   },
  {'id': 'tag:twitter.com,2012:3',
   'author_name': 'user 3 name',
   'author_uri': 'acct:user3@twitter-webfinger.appspot.com',
   'in_reply_to': 'http://example.com/asdf',
   'content': '@user1 i hereby #reply',
   'title': '@user1 i hereby #reply',
   'updated': '1970-01-01T00:00:01',
   },
  ]


class TwitterSearchTest(testutil.HandlerTest):

  def setUp(self):
    super(TwitterSearchTest, self).setUp()
    self.twitter = TwitterSearch(key_name='example.com')
    self.datastore_stub = self.testbed.get_stub('datastore_v3')

  def test_tweet_to_salmon_with_expanded_url(self):
    self.assert_equals(TWEETS_SALMON_VARS[0],
                       self.twitter.tweet_to_salmon_vars(TWEETS_JSON[0]))

  def test_tweet_to_salmon_with_url(self):
    self.assert_equals(TWEETS_SALMON_VARS[1],
                       self.twitter.tweet_to_salmon_vars(TWEETS_JSON[1]))

  def test_tweet_to_salmon_minimal(self):
    salmon = self.twitter.tweet_to_salmon_vars({'id': 123})
    self.assert_equals('tag:twitter.com,2012:123', salmon['id'])

  def test_tweet_to_salmon_no_matching_url(self):
    tweet = copy.deepcopy(TWEETS_JSON[0])
    tweet['entities']['urls'][0]['expanded_url'] = 'http://foo.com/bar'

    expected = copy.deepcopy(TWEETS_SALMON_VARS[0])
    expected['in_reply_to'] = None
    self.assert_equals(expected, self.twitter.tweet_to_salmon_vars(tweet))

  def test_get_salmon(self):
    self.expect_urlfetch(twitter.API_SEARCH_URL % 'example.com',
                         json.dumps({'results': TWEETS_JSON}))
    self.expect_urlfetch(twitter.API_SEARCH_URL % '@snarfed',
                         json.dumps({'results': []}))
    self.expect_urlfetch(twitter.API_SEARCH_URL % '@user1',
                         json.dumps({'results': MENTIONS_JSON}))
    self.mox.ReplayAll()

    self.assert_equals(TWEETS_SALMON_VARS, self.twitter.get_salmon())

  def test_add_good_domain(self):
    for domain in 'asdf.com', 'https://asdf.com/', 'asdf.com/foo?bar#baz':
      self.datastore_stub.Clear()

      resp = twitter.application.get_response('/twitter/add?domain=%s' % domain,
                                              method='POST')
      self.assertEquals(302, resp.status_int, resp.body)
      self.assertEquals('http://localhost/', resp.headers['Location'])

      searches = TwitterSearch.all().fetch(10)
      self.assertEqual(1, len(searches))
      ts = searches[0]
      self.assertEqual('asdf.com', ts.key().name())
      self.assertEqual('http://asdf.com/', ts.url)
      self.assertEqual('http://asdf.com/favicon.ico', ts.picture)
      self.assertEqual(self.current_user_id, ts.owner.key().name())

  def test_add_bad_domain(self):
    for domain in '', '  ', 'com', 'com.', 'a/b/c':
      resp = twitter.application.get_response('/twitter/add?domain=%s' % domain,
                                              method='POST')
      self.assertEquals(400, resp.status_int, resp.body)
      self.assertEqual(0, TwitterSearch.all().count())
