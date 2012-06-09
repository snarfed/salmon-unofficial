#!/usr/bin/python
"""Twitter source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json

import appengine_config
import source
from webutil import util
from django_salmon import magicsigs
from django_salmon import utils


# temporary URL for fetching magic sig private keys from webfinger-unofficial
USER_KEY_HANDLER = \
    'https://twitter-webfinger.appspot.com/user_key?uri=%s&secret=%s'

# Templates for Atom Salmons and Magic Envelopes. Note that the format
# specifiers have mapping keys. Used in tweet_to_salmon().
ATOM_SALMON_TEMPLATE = """\
<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom'>
  <id>%(id_tag)s</id>
  <author>
    <name>%(author_name)s</name>
    <uri>%(author_uri)s</uri>
  </author>
  <thr:in-reply-to xmlns:thr='http://purl.org/syndication/thread/1.0'
    ref='%(in_reply_to_tag)s'>
    %(in_reply_to_tag)s
  </thr:in-reply-to>
  <content>%(content)s</content>
  <title>%(title)s</title>
  <updated>%(updated)s</updated>
</entry>"""


class Twitter(source.Source):
  """Implements the Salmon API for Twitter.
  """

  DOMAIN = 'twitter.com'
  FRONT_PAGE_TEMPLATE = 'templates/twitter_index.html'


  def tweet_to_salmon_vars(self, tweet):
    """Extracts Salmon template vars from a JSON tweet.

    Args:
      tweet: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE
    """
    vars = {
      'id_tag': self.tag_uri(str(tweet.get('id'))),
      'author_name': tweet.get('from_user_name'),
      'author_uri': 'acct:%s@twitter-webfinger.appspot.com' % tweet.get('from_user'),
      # TODO: this should be the original domain link
      'in_reply_to_tag': self.tag_uri(tweet.get('in_reply_to_status_id')),
      'content': tweet.get('text'),
      'title': tweet.get('text'),
      # TODO: use rfc2822_to_iso8601() from activitystreams-unofficial/twitter.py
      'updated': tweet.get('created_at'),
      }

    parent_id = tweet.get('in_reply_to_status_id')
    if parent_id:
      # TODO: this should be the original domain link
      vars['in_reply_to_tag'] = self.tag_uri(parent_id)

    return vars
