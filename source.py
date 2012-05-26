#!/usr/bin/python
"""Source base class.

TODO:
- unify tag_uri() with activitystreams-unofficial.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import datetime


class Source(object):
  """Abstract base class for a source (e.g. Facebook, Twitter).

  Concrete subclasses must override the class constants below and implement
  get_comments().

  Attributes:
    handler: the current RequestHandler

  Class constants:
    DOMAIN: string, the source's domain
    FRONT_PAGE_TEMPLATE: string, the front page child template filename
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
