#!/usr/bin/python
"""Source base class.

TODO:
- unify tag_uri() with activitystreams-unofficial.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import datetime
try:
  import json
except ImportError:
  import simplejson as json

import appengine_config
from webutil import util
from django_salmon import magicsigs
from django_salmon import utils


# temporary URL for fetching magic sig private keys from webfinger-unofficial
USER_KEY_HANDLER = \
    'https://facebook-webfinger.appspot.com/user_key?uri=%s&secret=%s'

# Template for Atom Salmon. Note that the format specifiers have mapping keys.
# Used in comment_to_salmon().
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


class Source(object):
  """Abstract base class for a source (e.g. Facebook, Twitter).

  Concrete subclasses must override the class constants below and implement
  get_comments().

  Attributes:
    handler: the current RequestHandler

  Class constants:
    DOMAIN: string, the source's domain
  """

  def __init__(self, handler):
    self.handler = handler

  def get_comments(self):
    """
    """
    raise NotImplementedError()

  def tag_uri(self, name):
    """Returns a tag URI string for this source and the given string name.

    Example return value: 'tag:twitter.com,2012:snarfed_org/172417043893731329'

    Background on tag URIs: http://taguri.org/
    """
    return 'tag:%s,%d:%s' % (self.DOMAIN, datetime.datetime.now().year, name)

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
