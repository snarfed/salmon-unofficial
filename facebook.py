#!/usr/bin/python
"""Facebook source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

from models import Source

from webutil import util


class Facebook(Source):
  """Implements the Salmon API for Facebook.
  """

  DOMAIN = 'facebook.com'

  def comment_to_salmon_vars(self, comment):
    """Extracts Salmon template vars from a JSON Facebook comment.

    Args:
      comment: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE

    Raises:
      ValueError if comment['id'] cannot be parsed. It should be of the form
      PARENT_COMMENT
    """
    id = comment.get('id', '')
    parent_id, _, cmt_id = id.partition('_')
    if not parent_id or not cmt_id:
      raise ValueError('Could not parse comment id: %s' % id)

    cmt_from = comment.get('from', {})

    return {
      'id_tag': util.tag_uri(self.DOMAIN, id),
      'author_name': cmt_from.get('name'),
      'author_uri': 'acct:%s@facebook-webfinger.appspot.com' % cmt_from.get('id'),
      # TODO: this should be the original domain link
      'in_reply_to_tag': util.tag_uri(self.DOMAIN, parent_id),
      'content': comment.get('message'),
      'title': comment.get('message'),
      'updated': comment.get('created_time'),
      }
