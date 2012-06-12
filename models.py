#!/usr/bin/python
"""Datastore model classes.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import datetime
import itertools
import logging
import urlparse

import appengine_config
from webutil import util
from webutil import webapp2

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app


class User(util.KeyNameModel, util.SingleEGModel):
  """A registered user.

  The key name is the App Engine user_id.
  """

  @classmethod
  def get_current_user(cls):
    key_name = cls._current_user_key_name()
    if key_name:
      return cls.get_by_key_name(key_name)

  @classmethod
  @db.transactional
  # TODO: switch to plain get_or_insert()
  def get_or_insert_current_user(cls, handler):
    """Returns the logged in user's User instance, creating it if necessary.

    Implemented manually instead of via Model.get_or_insert() because we want to
    know if we created the User object so we can add a message to the handler.

    Args:
      handler: the current webapp.RequestHandler
    """
    key_name = cls._current_user_key_name()
    if key_name:
      user = cls.get_by_key_name(key_name)
      if not user:
        user = cls(key_name=key_name)
        user.save()

      return user

  @staticmethod
  def _current_user_key_name():
    """Returns a unique key name for the current user.

    Returns: the user's OpenId identifier or App Engine user id or None if
      they're not logged in, 
    """
    user = users.get_current_user()
    if user:
      return user.user_id()


class Source(util.KeyNameModel, util.SingleEGModel):
  """A source to read posts from, e.g. a Facebook profile.

  Each concrete source should subclass this.
  """

  POLL_TASK_DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'
  EPOCH = datetime.datetime.utcfromtimestamp(0)

  last_polled = db.DateTimeProperty(default=EPOCH)

  # human-readable name for this source type. subclasses should override.
  TYPE_NAME = None

  url = db.LinkProperty()
  picture = db.LinkProperty()
  owner = db.ReferenceProperty(User)

  @classmethod
  def create_new(cls, handler, **kwargs):
    """Creates and saves a new Source and adds a poll task for it.

    Args:
      handler: the current webapp.RequestHandler
      **kwargs: passed to new()
    """
    new = cls.new(handler, **kwargs)
    new.save()
    new.add_poll_task()
    return new

  @classmethod
  def new(cls, handler, **kwargs):
    """Factory method. Creates and returns a new instance for the current user.

    To be implemented by subclasses.

    Args:
      handler: the current webapp.RequestHandler
      **kwargs: passed to new()
    """
    raise NotImplementedError()

  def display_name(self):
    """Returns a human-readable name for this source, e.g. 'My Thoughts'.

    To be implemented by subclasses.
    """
    raise NotImplementedError()

  def type_display_name(self):
    """Returns a human-readable name for this type of source, e.g. 'Facebook'.
    
    To be implemented by subclasses.
    """
    raise NotImplementedError()

  def get_posts(self):
    """Returns a list of the most recent posts from this source.
 
    To be implemented by subclasses.

    Returns: list of (post, url), where post is any object and url is the string
      url for the post
    """
    raise NotImplementedError()

  def add_poll_task(self, **kwargs):
    """Adds a poll task for this source."""
    last_polled_str = self.last_polled.strftime(self.POLL_TASK_DATETIME_FORMAT)
    taskqueue.add(queue_name='poll',
                  params={'source_key': str(self.key()),
                          'last_polled': last_polled_str},
                  **kwargs)
