#!/usr/bin/python
"""Facebook source class.
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
from django_salmon import magicsigs
from django_salmon import utils


# temporary URL for fetching magic sig private keys from webfinger-unofficial
USER_KEY_HANDLER = \
    'https://facebook-webfinger.appspot.com/user_key?uri=%s&secret=%s'

# Templates for Atom Salmons and Magic Envelopes. Note that the format
# specifiers have mapping keys. Used in comment_to_salmon().
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


class Facebook(source.Source):
  """Implements the Salmon API for Facebook.
  """

  DOMAIN = 'facebook.com'
  FRONT_PAGE_TEMPLATE = 'templates/facebook_index.html'


  def comment_to_salmon(self, comment):
    """Converts a Facebook JSON comment dict to an Atom Salmon.

    Args:
      comment: JSON dict

    Returns: string

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

  def envelope(self, salmon, author_uri):
    """Signs and encloses an Atom Salmon in a Magic Signature envelope.

    Fetches the author's Magic Signatures public key via LRDD in order to create
    the signature.

    Args:
      salmon: string, an Atom Salmon
      author_uri: string, the author's URI, beginning with acct:

    Returns: JSON dict following Magic Signatures spec section 3.5:
    http://salmon-protocol.googlecode.com/svn/trunk/draft-panzer-magicsig-01.html#anchor5
    """
    class Struct(object):
      def __init__(self, **kwargs):
        vars(self).update(**kwargs)

    key_url = USER_KEY_HANDLER % (author_uri, appengine_config.USER_KEY_HANDLER_SECRET)
    key = Struct(**json.loads(util.urlfetch(key_url)))
    return magicsigs.magic_envelope(salmon, 'application/atom+xml', key)
