#!/usr/bin/python
"""Salmon model class.

TODO
- don't include user themselves? (option?)
- log in/out, only delete your own sources
- switch plus.json
- cache endpoint discovery

TODO: salmon endpoint disovery doesn't work for some salmon implementations.
status.net, for example, supports it via XRD/LRDD, but you need to know the
user's URI, or at least their username, and I don't know how to do that
programmatically based on a post URL.

For example, if you read it in a browser as a human, it's clear that
http://identi.ca/notice/94643764 was written by a user with the username
forteller. Armed with that knowledge, you can follow the LRDD Link in
http://identi.ca/.well-known/host-meta and get
http://identi.ca/main/xrd?uri=acct:forteller@identi.ca , which tells you that
forteller's salmon reply endpoint is http://identi.ca/main/salmon/user/9896 .

However, how would you write code to determine that the author of
http://identi.ca/notice/94643764 is acct:forteller@identi.ca ? The string
forteller only shows up in the page title and in uremarkable h1 and anchor
elements. There also aren't any link rel="alternate" elements in the header that
point to feeds.

Even if you somehow guessed that the top level stream page was
http://identi.ca/forteller , and autodiscovered a feed like
http://identi.ca/forteller/rss , even *that* doesn't easily lead you to
acct:forteller@identi.ca or even forteller. Grr. :(
"""

# - fix this in all three
# INFO     2012-06-17 17:26:00,986 salmon.py:87] Trying to send slap:
# {u'author_uri': u'acct:102984255052142775811@gmail.com', u'updated': u'2012-06-03T05:33:10.789Z', u'title': u'Thats going on now', u'author_name': u'Kelo Nelson', u'content': u'Thats going on now', u'in_reply_to': u'https://plus.google.com/photos/103651231634018158746/albums/5749677294085736961/5749677297497774114', u'id': u'tag:plus.google.com,2012:ccg0o1_OvkYgU5SIe8zKyJulbJ16Qp_fVvw5wcceWHEfXXAL-gO2rdf3MgxPmHcw2457EmQs9cc'}
# DEBUG    2012-06-17 17:26:00,986 salmon.py:132] Discovering salmon endpoint for u'https://plus.google.com/photos/103651231634018158746/albums/5749677294085736961/5749677297497774114'
# DEBUG    2012-06-17 17:26:00,986 util.py:56] Fetching https://plus.google.com/photos/103651231634018158746/albums/5749677294085736961/5749677297497774114 with kwargs {}
# DEBUG    2012-06-17 17:26:00,986 urlfetch_stub.py:317] Making HTTP request: host = plus.google.com, url = https://plus.google.com/photos/103651231634018158746/albums/5749677294085736961/5749677297497774114, payload = , headers = {'Host': 'plus.google.com', 'Accept-Encoding': 'gzip', 'User-Agent': 'AppEngine-Google; (+http://code.google.com/appengine)'}
# DEBUG    2012-06-17 17:26:01,393 dev_appserver_import_hook.py:1497] Access to module file denied: /usr/lib/pymodules/python2.6/drv_libxml2.py
# DEBUG    2012-06-17 17:26:01,398 dev_appserver_import_hook.py:1497] Access to module file denied: /usr/lib/pymodules/python2.6/drv_libxml2.py
# DEBUG    2012-06-17 17:26:01,401 util.py:56] Fetching http://plus.google.com/.well-known/host-meta with kwargs {}
# DEBUG    2012-06-17 17:26:01,401 urlfetch_stub.py:317] Making HTTP request: host = plus.google.com, url = http://plus.google.com/.well-known/host-meta, payload = , headers = {'Host': 'plus.google.com', 'Accept-Encoding': 'gzip', 'User-Agent': 'AppEngine-Google; (+http://code.google.com/appengine)'}
# ERROR    2012-06-17 17:26:01,493 traceback.py:13] Traceback (most recent call last):
# ERROR    2012-06-17 17:26:01,493 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 768, in emit
# ERROR    2012-06-17 17:26:01,493 traceback.py:13]     msg = self.format(record)
# ERROR    2012-06-17 17:26:01,494 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 648, in format
# ERROR    2012-06-17 17:26:01,494 traceback.py:13]     return fmt.format(record)
# ERROR    2012-06-17 17:26:01,494 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 436, in format
# ERROR    2012-06-17 17:26:01,494 traceback.py:13]     record.message = record.getMessage()
# ERROR    2012-06-17 17:26:01,495 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 306, in getMessage
# ERROR    2012-06-17 17:26:01,495 traceback.py:13]     msg = msg % self.args
# ERROR    2012-06-17 17:26:01,495 traceback.py:13] TypeError: not enough arguments for format string
# ERROR    2012-06-17 17:26:01,495 traceback.py:13] Traceback (most recent call last):
# ERROR    2012-06-17 17:26:01,496 traceback.py:13]   File "/home/ryanb/google_appengine/google/appengine/api/app_logging.py", line 90, in emit
# ERROR    2012-06-17 17:26:01,496 traceback.py:13]     message = self._AppLogsMessage(record)
# ERROR    2012-06-17 17:26:01,496 traceback.py:13]   File "/home/ryanb/google_appengine/google/appengine/api/app_logging.py", line 108, in _AppLogsMessage
# ERROR    2012-06-17 17:26:01,496 traceback.py:13]     message = self.format(record).replace("\r\n", NEWLINE_REPLACEMENT)
# ERROR    2012-06-17 17:26:01,496 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 648, in format
# ERROR    2012-06-17 17:26:01,497 traceback.py:13]     return fmt.format(record)
# ERROR    2012-06-17 17:26:01,497 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 436, in format
# ERROR    2012-06-17 17:26:01,497 traceback.py:13]     record.message = record.getMessage()
# ERROR    2012-06-17 17:26:01,497 traceback.py:13]   File "/usr/lib/python2.6/logging/__init__.py", line 306, in getMessage
# ERROR    2012-06-17 17:26:01,498 traceback.py:13]     msg = msg % self.args
# ERROR    2012-06-17 17:26:01,498 traceback.py:13] TypeError: not enough arguments for format string
# INFO     2012-06-17 17:26:01,498 salmon.py:92] Could not discover Salmon endpoint; giving up. The resource could not be found.

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import appengine_config
import datetime
import feedparser
import logging
import json
import urlparse
from webob import exc
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
  vars = db.TextProperty()

  @db.transactional
  def get_or_save(self):
    existing = db.get(self.key())
    if existing:
      logging.debug('Deferring to existing salmon %s.', existing.key().name())
      return existing

    logging.debug('New salmon to propagate: %s', self.key().name())
    taskqueue.add(queue_name='propagate', params={'salmon_key': str(self.key())})
    self.save()
    return self

  def send_slap(self):
    vars = json.loads(self.vars)
    logging.info('Trying to send slap:\n%r', vars)

    try:
      endpoint = self.discover_salmon_endpoint()
    except exc.HTTPClientError, e:
      logging.info('Could not discover Salmon endpoint; giving up. %s', e)
      return

    if endpoint:
      try:
        logging.info('Sending slap to %r', endpoint)
        resp = util.urlfetch(endpoint, method='POST',
                             payload=self.envelope(), headers=SLAP_HTTP_HEADERS)
      except exc.HTTPClientError, e:
        logging.exception('Error sending slap; giving up.')

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

  def discover_salmon_endpoint(self):
    """Discovers and returns the Salmon endpoint URL for this salmon.
  
    It'd be nice to use an XRD/LRDD library here, but I haven't found much.
    github.com/jcarbaugh/python-xrd is only for generating, not reading.
    pydataportability.net looks powerful but also crazy heavyweight; it
    requires Zope and strongly recommends running inside virtualenv. No thanks.
  
    Returns: string URL or None
    """
    url = json.loads(self.vars)['in_reply_to']
    logging.debug('Discovering salmon endpoint for %r', url)
    body = util.urlfetch(url)
  
    # first look in the document itself
    endpoint = django_salmon.discover_salmon_endpoint(body)
    if endpoint:
      logging.debug('Found in original document: %r', endpoint)
      return endpoint
  
    # next, look in its feed, if any
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
  
    # next, look in /.well-known/host-meta
    host_meta_url = 'http://%s/.well-known/host-meta' % util.domain_from_link(url)
    endpoint = django_salmon.discover_salmon_endpoint(util.urlfetch(host_meta_url))
    if endpoint:
      logging.debug('Found in host-meta: %r', endpoint)
      return endpoint
  
    logging.debug('No salmon endpoint found!')
    return None
