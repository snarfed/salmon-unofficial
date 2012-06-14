#!/usr/bin/python
"""Twitter source class.

Python code to pretty-print JSON responses from Twitter Search API:
pprint.pprint(json.loads(urllib.urlopen(
  'http://search.twitter.com/search.json?q=snarfed.org+filter%3Alinks&include_entities=true&result_type=recent&rpp=100').read()))
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import datetime
import json
import logging
import re
import urlparse
from webob import exc

import appengine_config
import models

from webutil import util
from webutil import webapp2

from google.appengine.ext.webapp.util import run_wsgi_app

# Search for tweets using the Twitter Search API.
#
# Background:
# https://dev.twitter.com/docs/using-search
# https://dev.twitter.com/docs/api/1/get/search
# http://stackoverflow.com/questions/2693553/replies-to-a-particular-tweet-twitter-api
API_SEARCH_URL = 'http://search.twitter.com/search.json?q=%s+filter:links&include_entities=true&result_type=recent&rpp=100'


class TwitterSearch(models.Source):
  """A Twitter search for posts that link to a given domain.

  The key name is the domain.
  """

  DOMAIN = 'twitter.com'

  @staticmethod
  def new(handler, domain=None):
    """Returns a new TwitterSearch for the logged in user based on URL params.

    Args:
      handler: the current webapp2.RequestHandler
    """
    assert domain
    url = 'http://%s/' % domain
    favicon = util.favicon_for_url(url)
    return TwitterSearch(key_name=domain, url=url, picture=favicon,
                         owner=models.User.get_or_insert_current_user(handler))

  def display_name(self):
    return self.key().name()

  def type_display_name(self):
    return 'Twitter search'

  def tweet_to_salmon_vars(self, tweet):
    """Extracts Salmon template vars from a JSON tweet.

    Args:
      tweet: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE
    """
    # there might be more than one URL in the tweet. find the one on our domain.
    # https://dev.twitter.com/docs/tweet-entities
    link = None
    for url_data in tweet.get('entities', {}).get('urls', []):
      # expanded_url isn't always provided
      url = url_data.get('expanded_url') or url_data.get('url')
      if url and urlparse.urlparse(url).netloc == self.key().name():
        link = url

    # parse the timestamp, formatted e.g. 'Sun, 01 Jan 2012 11:44:57 +0000'
    created_at = tweet.get('created_at')
    if created_at:
      created_at = re.sub(' \+[0-9]{4}$', '', created_at)
      updated = datetime.datetime.strptime(created_at,
                                           '%a, %d %b %Y %H:%M:%S')
      updated = updated.isoformat()
    else:
      updated = ''

    return {
      'id': util.tag_uri(self.DOMAIN, str(tweet.get('id'))),
      'author_name': tweet.get('from_user_name'),
      'author_uri': 'acct:%s@twitter-webfinger.appspot.com' % tweet.get('from_user'),
      'in_reply_to': link,
      'content': tweet.get('text'),
      'title': tweet.get('text'),
      'updated': updated,
      }

  @staticmethod
  def tweet_url(username, id):
    """Returns the URL of a tweet."""
    return 'http://twitter.com/%s/status/%d' % (username, id)

  def get_salmon(self):
    """Returns a list of Salmon template var dicts for tweets and replies."""
    # find tweets with links that include our base url. response is JSON tweets:
    # https://dev.twitter.com/docs/api/1/get/search
    resp = util.urlfetch(API_SEARCH_URL % self.key().name())
    tweets = json.loads(resp)['results']

    # twitter usernames of people who wrote tweets with links to our domain
    author_usernames = set()

    # maps tweet id to the link (to our domain) that it contains
    tweets_to_links = {}

    # get tweets that link to our domain
    salmons = []
    for tweet in tweets:
      id = tweet.get('id')
      username = tweet.get('from_user')
      tweet_url = self.tweet_url(username, id)
      salmon = self.tweet_to_salmon_vars(tweet)
      if salmon['in_reply_to']:
        logging.debug('Found link %s in tweet %s', salmon['in_reply_to'], tweet_url)
        salmons.append(salmon)
        author_usernames.add(username)
        tweets_to_links[id] = salmon['in_reply_to']
      else:
        logging.info("Tweet %s should have %s link but doesn't. Maybe shortened?",
                     tweet_url, self.key().name())

    # find replies to those tweets by searching for tweets that mention the
    # authors.
    for username in author_usernames:
      resp = util.urlfetch(API_SEARCH_URL % ('@' + username))
      mentions = json.loads(resp)['results']
      for mention in mentions:
        logging.debug('Looking at mention: %s', mention)
        link = tweets_to_links.get(mention.get('in_reply_to_status_id'))
        if link:
          salmon = self.tweet_to_salmon_vars(mention)
          salmon['in_reply_to'] = link
          salmons.append(salmon)
          logging.debug('Found reply %s',
                        self.tweet_url(mention['from_user'], mention['id']))

    return salmons


class AddTwitterSearch(webapp2.RequestHandler):
  def post(self):
    value = self.request.get('domain')
    parsed = urlparse.urlparse(value)
    if not parsed.netloc:
      parsed = urlparse.urlparse('http://' + value)

    domain = parsed.netloc
    if not domain:
      raise exc.HTTPBadRequest('No domain found in %r' % value)

    # strip exactly one dot from the right, if present
    if domain[-1:] == ".":
      domain = domain[:-1] 

    split = domain.split('.')
    if len (split) <= 1:
      raise exc.HTTPBadRequest('No TLD found in domain %r' % domain)

    # http://stackoverflow.com/questions/2532053/validate-hostname-string-in-python
    allowed = re.compile('(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)
    for part in split:
      if not allowed.match(part):
        raise exc.HTTPBadRequest('Bad component in domain: %r' % part)

    TwitterSearch.create_new(self, domain=domain).save()
    self.redirect('/')


application = webapp2.WSGIApplication(
  [('/twitter/add', AddTwitterSearch)],
  debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
