#!/usr/bin/python
"""Salmon model class."""
# STATE: need to do extra LRDD lookup for salmon link

# curl http://identi.ca/.well-known/host-meta
# <?xml version="1.0" encoding="UTF-8"?>
# <XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0"><hm:Host xmlns:hm="http://host-meta.net/xrd/1.0">identi.ca</hm:Host><Link rel="lrdd" template="http://identi.ca/main/xrd?uri={uri}"><Title>Resource Descriptor</Title></Link></XRD>laptop:~> curl 'http://identi.ca/main/xrd?uri=acct:forteller@identi.ca'
# <?xml version="1.0" encoding="UTF-8"?>
# <XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0"><Subject>acct:forteller@identi.ca</Subject><Alias>http://identi.ca/user/9896</Alias><Alias>http://identi.ca/forteller</Alias><Link rel="http://webfinger.net/rel/profile-page" type="text/html" href="http://identi.ca/forteller"></Link><Link rel="http://gmpg.org/xfn/11" type="text/html" href="http://identi.ca/forteller"></Link><Link rel="describedby" type="application/rdf+xml" href="http://identi.ca/forteller/foaf"></Link><Link rel="http://apinamespace.org/atom" type="application/atomsvc+xml" href="http://identi.ca/api/statusnet/app/service/forteller.xml"><Property type="http://apinamespace.org/atom/username">forteller</Property></Link><Link rel="http://apinamespace.org/twitter" href="https://identi.ca/api/"><Property type="http://apinamespace.org/twitter/username">forteller</Property></Link><Link rel="http://schemas.google.com/g/2010#updates-from" href="http://identi.ca/api/statuses/user_timeline/9896.atom" type="application/atom+xml"></Link><Link rel="salmon" href="http://identi.ca/main/salmon/user/9896"></Link><Link rel="http://salmon-protocol.org/ns/salmon-replies" href="http://identi.ca/main/salmon/user/9896"></Link><Link rel="http://salmon-protocol.org/ns/salmon-mention" href="http://identi.ca/main/salmon/user/9896"></Link><Link rel="magic-public-key" href="data:application/magic-public-key,RSA.ohR-_jdQ5yQeGPBzTPysQvTav93FL-P_5yVfvJl1sUQBdRA7dFZpqR83vJOnsgHbO3KEo8yKadWNCrS6A-IJZn2tHrxHTJ1lasXGkNxGQuIKt3hsZXsEvChqNZrq8cqDXXOl6vMCWccBVO1w6HCXHtfgZRhrC6tbDUtXlhHd_O0=.AQAB"></Link><Link rel="http://ostatus.org/schema/1.0/subscribe" template="http://identi.ca/main/ostatussub?profile={uri}"></Link><Link rel="http://specs.openid.net/auth/2.0/provider" href="http://identi.ca/forteller"></Link></XRD>laptop:~> 
# laptop:~> 

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

# sent with salmon slaps
SLAP_HTTP_HEADERS = {'Content-Type': 'application/magic-envelope+xml'}

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
    vars = json.loads(self.vars)
    url = vars['in_reply_to']
    logging.info('Trying to send slap:\n%r', vars)

    endpoint = discover_salmon_endpoint(url)
    if endpoint:
      resp = util.urlfetch(endpoint, method='POST',
                           payload=self.envelope(), headers=SLAP_HTTP_HEADERS)
      logging.info('Sent slap to %r. Response: %r', endpoint, resp)

  def envelope(self):
    """Signs and encloses this salmon in a Magic Signature envelope.

    Fetches the author's Magic Signatures public key via LRDD in order to create
    the signature.

    Returns: JSON dict following Magic Signatures spec section 3.5:
    http://salmon-protocol.googlecode.com/svn/trunk/draft-panzer-magicsig-01.html#anchor5
    """
    class UserKey(object):
      def __init__(self, **kwargs):
        vars(self).update(**kwargs)

    salmon_vars = json.loads(self.vars)
    key_url = USER_KEY_HANDLER % (salmon_vars['author_uri'],
                                  appengine_config.USER_KEY_HANDLER_SECRET)
    key = UserKey(**json.loads(util.urlfetch(key_url)))
    return magicsigs.magic_envelope(ATOM_SALMON_TEMPLATE % salmon_vars,
                                    'application/atom+xml', key)


def discover_salmon_endpoint(url):
  """Discovers and returns the Salmon endpoint URL for a post URL.

  Args:
    url: string URL

  Returns: string URL or None
  """
  logging.debug('Discovering salmon endpoint for %r', url)
  body = util.urlfetch(url)

  # first look in the document itself
  endpoint = django_salmon.discover_salmon_endpoint(body)
  if endpoint:
    logging.debug('Found in original document: %r', endpoint)
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
        logging.debug('Found in feed: %r', endpoint)
        return endpoint

  # finally, look in /.well-known/host-meta
  host_meta_url = 'http://%s/.well-known/host-meta' % util.domain_from_link(url)
  endpoint = django_salmon.discover_salmon_endpoint(util.urlfetch(host_meta_url))
  if endpoint:
    logging.debug('Found in host-meta: %r', endpoint)
    return endpoint

  logging.debug('No salmon endpoint found!')
  return None
