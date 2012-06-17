#!/usr/bin/python
"""Salmon model class."""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import appengine_config
import datetime
import feedparser
import logging
import json
import urlparse
from webutil import util

import django_salmon
from django_salmon import magicsigs
from django_salmon import utils

from google.appengine.api import taskqueue
from google.appengine.ext import db

FEED_MIME_TYPES = ('application/rss+xml', 'application/atom+xml')

# temporary URL for fetching magic sig private keys from webfinger-unofficial
USER_KEY_HANDLER = \
    'https://facebook-webfinger.appspot.com/user_key?uri=%s&secret=%s'

# Template for Atom Salmon. Note that the format specifiers have mapping keys.
ATOM_SALMON_TEMPLATE = """\
<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom'>
  <id>%(id)s</id>
  <author>
    <name>%(author_name)s</name>
    <uri>%(author_uri)s</uri>
  </author>
  <thr:in-reply-to xmlns:thr='http://purl.org/syndication/thread/1.0'
    ref='%(in_reply_to)s'>
    %(in_reply_to)s
  </thr:in-reply-to>
  <content>%(content)s</content>
  <title>%(title)s</title>
  <updated>%(updated)s</updated>
</entry>"""


class Salmon(util.KeyNameModel):
  """A salmon to be propagated.

  Key name is the id tag URI.
  """

  STATUSES = ('new', 'processing', 'complete')

  status = db.StringProperty(choices=STATUSES, default='new')
  leased_until = db.DateTimeProperty()
  vars = db.StringProperty()

  @db.transactional
  def get_or_save(self):
    existing = db.get(self.key())
    if existing:
      logging.debug('Deferring to existing salmon %s.', existing.key().name())
      return existing

    logging.debug('New salmon to propagate: %s' % self.key().name())
    taskqueue.add(queue_name='propagate', params={'salmon_key': str(self.key())})
    self.save()
    return self

  def send_slap(self):
    url = json.loads(self.vars)['in_reply_to']

    # TODO(paulosman)
    # really crappy HTTP client right now. Can improve when the basic
    # protocol flow is working.
    headers = {
        'Content-Type': 'application/magic-envelope+xml',
    }
    req = urllib2.Request(sub.salmon_endpoint, magic_envelope, headers)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except urllib2.HTTPError, e:
        print repr(e)
        print e.read()

    util.urlfetch(salmon.endpoint, method='POST', payload=self.envelope(),
                  headers={'Content-Type': 'application/magic-envelope+xml'})

  def envelope(self, author_uri):
    """Signs and encloses an Atom Salmon in a Magic Signature envelope.

    Fetches the author's Magic Signatures public key via LRDD in order to create
    the signature.

    Args:
      salmon: string, an Atom Salmon
      author_uri: string, the author's URI, beginning with acct:

    Returns: JSON dict following Magic Signatures spec section 3.5:
    http://salmon-protocol.googlecode.com/svn/trunk/draft-panzer-magicsig-01.html#anchor5
    """
    class UserKey(object):
      def __init__(self, **kwargs):
        vars(self).update(**kwargs)

    key_url = USER_KEY_HANDLER % (author_uri, appengine_config.USER_KEY_HANDLER_SECRET)
    key = UserKey(**json.loads(util.urlfetch(key_url)))
    return magicsigs.magic_envelope(ATOM_SALMON_TEMPLATE % json.loads(self.vars),
                                    'application/atom+xml', key)


def discover_salmon_endpoint(url):
  """Discovers and returns the Salmon endpoint URL for a post URL.

  Args:
    url: string URL

  Returns: string URL or None
  """
  body = util.urlfetch(url)

  # first look in the document itself
  endpoint = django_salmon.discover_salmon_endpoint(body)
  if endpoint:
    return endpoint

  # next look in its feed, if any
  #
  # background on feed autodiscovery:
  # http://blog.whatwg.org/feed-autodiscovery
  parsed = feedparser.parse(body)
  for link in parsed.feed.get('links', []):
    rels = link.get('rel').split()
    href = link.get('href')
    if href and ('feed' in rels or 'alternate' in rels):
      endpoint = django_salmon.discover_salmon_endpoint(util.urlfetch(href))
      if endpoint:
        return endpoint

  # finally, look in /.well-known/host-meta
  host_meta_url = 'http://%s/.well-known/host-meta' % util.domain_from_link(url)
  return django_salmon.discover_salmon_endpoint(util.urlfetch(host_meta_url))

