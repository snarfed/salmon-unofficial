#!/usr/bin/python
"""Twitter source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import source


class Twitter(source.Source):
  """Implements the Salmon API for Twitter.
  """

  DOMAIN = 'twitter.com'

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
