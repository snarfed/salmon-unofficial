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


class TwitterSearch(models.Source):
  """A Twitter search for posts that link to a given domain.

  The key name is the domain.
  """

  DOMAIN = 'twitter.com'

  def tweet_to_salmon_vars(self, tweet):
    """Extracts Salmon template vars from a JSON tweet.

    Args:
      tweet: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE
    """
    vars = {
      'id_tag': util.tag_uri(self.DOMAIN, str(tweet.get('id'))),
      'author_name': tweet.get('from_user_name'),
      'author_uri': 'acct:%s@twitter-webfinger.appspot.com' % tweet.get('from_user'),
      # TODO: this should be the original domain link
      'in_reply_to_tag': util.tag_uri(self.DOMAIN, tweet.get('in_reply_to_status_id')),
      'content': tweet.get('text'),
      'title': tweet.get('text'),
      # TODO: use rfc2822_to_iso8601() from activitystreams-unofficial/twitter.py
      'updated': tweet.get('created_at'),
      }

    parent_id = tweet.get('in_reply_to_status_id')
    if parent_id:
      # TODO: this should be the original domain link
      vars['in_reply_to_tag'] = util.tag_uri(self.DOMAIN, parent_id)

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

    TwitterSearch(key_name=domain).save()
    self.redirect('/')


application = webapp2.WSGIApplication(
  [('/twitter/add', AddTwitterSearch)],
  debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
