#!/usr/bin/python
"""Fake model classes used in unit tests.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

from models import Site, Source

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


class FakeSite(FakeBase, Site):
  pass


# class FakeDestination(FakeBase, Destination):
#   """  Attributes:
#     comments: dict mapping FakeDestination string key to list of Comment entities
#   """

#   comments = collections.defaultdict(list)

#   def add_comment(self, comment):
#     FakeDestination.comments[str(self.key())].append(comment)

#   def get_comments(self):
#     return FakeDestination.comments[str(self.key())]


class FakeSource(FakeBase, Source):
  """Attributes:
    comments: dict mapping FakeSource string key to list of Comments to be
      returned by poll()
  """
  comments = {}

  def set_comments(self, comments):
    FakeSource.comments[str(self.key())] = comments

  def get_posts(self):
    return [(c, c.dest_post_url) for c in FakeSource.comments[str(self.key())]]

  def get_comments(self, posts):
    assert posts
    return FakeSource.comments[str(self.key())]
