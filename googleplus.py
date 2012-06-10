#!/usr/bin/python
"""Google+ source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

from models import Source

from webutil import util


class GooglePlus(Source):
  """Implements the Salmon API for Google+.
  """

  DOMAIN = 'plus.google.com'

  def activity_to_salmon_vars(self, activity):
    """Extracts Salmon template vars from a JSON activity.

    Args:
      activity: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE
    """
    actor = activity.get('actor', {})
    content = activity.get('object', {}).get('content')
    title = activity.get('title')
    vars = {
      'id_tag': util.tag_uri(self.DOMAIN, activity.get('id')),
      'author_name': actor.get('displayName'),
      'author_uri': 'acct:%s@gmail.com' % actor.get('id'),
      # TODO: this should be the original domain link
      'content': content,
      'title': title if title else content,
      'updated': activity.get('published'),
      }

    in_reply_to = activity.get('inReplyTo')
    if in_reply_to:
      vars['in_reply_to_tag'] = util.tag_uri(self.DOMAIN, in_reply_to[0].get('id'))

    return vars
