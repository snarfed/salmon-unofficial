#!/usr/bin/python
"""Fake model classes used in unit tests.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import models

from google.appengine.ext import db


class FakeBase(db.Model):
  """Not thread safe.
  """

  key_name_counter = 1

  @classmethod
  def new(cls, handler, **props):
    if 'url' not in props:
      props['url'] = 'http://fake/url'
    inst = cls(key_name=str(cls.key_name_counter), **props)
    cls.key_name_counter += 1
    return inst

  def type_display_name(self):
    return self.__class__.__name__


class FakeSource(FakeBase, models.Source):
  """A fake Source class.

  Class attributes:
    salmon: dict mapping FakeSource string key to list of Salmon to be
      returned by poll(). Can't just store in an instance attribute because
      tasks.py code loads entities from the datastore.
  """
  salmon = {}

  def set_salmon(self, salmon):
    FakeSource.salmon[str(self.key())] = salmon

  def get_salmon(self):
    return FakeSource.salmon[str(self.key())]
