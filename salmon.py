#!/usr/bin/python
"""Source base class.
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

from google.appengine.ext import db


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


class Salmon(util.KeyNameModel):
  """A salmon to be propagated.

  Class constants:
    DOMAIN: string, the source's domain
  """

  def __init__(self, handler):
    self.handler = handler

  def get_comments(self):
    """
    """
    raise NotImplementedError()

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



  # STATUSES = ('new', 'processing', 'complete')

  # source = db.ReferenceProperty(reference_class=Source, required=True)
  # dest = db.ReferenceProperty(reference_class=Destination, required=True)
  # source_post_url = db.LinkProperty()
  # source_comment_url = db.LinkProperty()
  # dest_post_url = db.LinkProperty()
  # dest_comment_url = db.LinkProperty()
  # created = db.DateTimeProperty()
  # author_name = db.StringProperty()
  # author_url = db.LinkProperty()
  # content = db.TextProperty()

  # status = db.StringProperty(choices=STATUSES, default='new')
  # leased_until = db.DateTimeProperty()

  # @db.transactional
  # def get_or_save(self):
  #   existing = db.get(self.key())
  #   if existing:
  #     logging.debug('Deferring to existing comment %s.', existing.key().name())
  #     # this might be a nice sanity check, but we'd need to hard code certain
  #     # properties (e.g. content) so others (e.g. status) aren't checked.
  #     # for prop in self.properties().values():
  #     #   new = prop.get_value_for_datastore(self)
  #     #   existing = prop.get_value_for_datastore(existing)
  #     #   assert new == existing, '%s: new %s, existing %s' % (prop, new, existing)
  #     return existing

  #   logging.debug('New comment to propagate: %s' % self.key().name())
  #   taskqueue.add(queue_name='propagate', params={'comment_key': str(self.key())})
  #   self.save()
  #   return self
