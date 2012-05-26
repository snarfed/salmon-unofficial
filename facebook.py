#!/usr/bin/python
"""Facebook source class. Uses the Graph API.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import cgi
import collections
import datetime
try:
  import json
except ImportError:
  import simplejson as json
import re
import urllib
import urlparse

import appengine_config
import source
from webutil import util

# A template for generating an unsigned Atom Salmon based on a JSON Facebook
# Graph API comment. Note that the format specifiers have mapping keys. Used in
# comment_to_salmon().
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
</entry>
"""


class Facebook(source.Source):
  """Implements the Salmon API for Facebook.
  """

  DOMAIN = 'facebook.com'
  FRONT_PAGE_TEMPLATE = 'templates/facebook_index.html'


  def comment_to_salmon(self, comment):
    """Converts a Facebook comment in a JSON dict to an unsigned Atom Salmon.

    Raises:
      ValueError if comment['id'] cannot be parsed. It should be of the form
      PARENT_COMMENT.
    """
    id = comment.get('id', '')
    parent_id, _, cmt_id = id.partition('_')
    if not parent_id or not cmt_id:
      raise ValueError('Could not parse comment id: %s' % id)

    cmt_from = comment.get('from', {})

    return ATOM_SALMON_TEMPLATE % {
      'id_tag': self.tag_uri(id),
      'author_name': cmt_from.get('name'),
      'author_uri': 'acct:%s@facebook-webfinger.appspot.com' % cmt_from.get('id'),
      'in_reply_to_tag': self.tag_uri(parent_id),
      'content': comment.get('message'),
      'title': comment.get('message'),
      'updated': comment.get('created_time'),
      }
