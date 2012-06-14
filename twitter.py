#!/usr/bin/python
"""Twitter source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import re
import urlparse
from webob import exc

import appengine_config
import models

from webutil import util
from webutil import webapp2

from google.appengine.ext.webapp.util import run_wsgi_app


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
    link = ''
    for url in tweet.get('entities', {}).get('urls', []):
      expanded = url['expanded_url']
      if urlparse.urlparse(expanded).netloc == self.key().name():
        link = expanded

    vars = {
      'id_tag': util.tag_uri(self.DOMAIN, str(tweet.get('id'))),
      'author_name': tweet.get('from_user_name'),
      'author_uri': 'acct:%s@twitter-webfinger.appspot.com' % tweet.get('from_user'),
      'in_reply_to_tag': link,
      'content': tweet.get('text'),
      'title': tweet.get('text'),
      # TODO: use rfc2822_to_iso8601() from activitystreams-unofficial/twitter.py
      'updated': tweet.get('created_at'),
      }

    return vars


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
