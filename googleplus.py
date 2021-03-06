#!/usr/bin/python
"""Google+ source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import httplib2
import logging
import os
import urlparse

import models

import appengine_config
from webutil import util
from webutil import webapp2

from apiclient.discovery import build

from oauth2client.appengine import CredentialsModel
from oauth2client.appengine import OAuth2Decorator
from oauth2client.appengine import StorageByKeyName

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

# plus_api is a decorator for request handlers that need to make OAuth-based
# calls to the Google+ REST API. we need to create it manually this way so that
# we can use store
plus_api = OAuth2Decorator(client_id=appengine_config.GOOGLE_CLIENT_ID,
                           client_secret=appengine_config.GOOGLE_CLIENT_SECRET,
                           scope='https://www.googleapis.com/auth/plus.me')


class GooglePlusService(db.Model):
  """A Google+ API service wrapper. Useful for mocking.

  Not thread safe.
  """

  http = httplib2.Http()
  # initialized in call()
  service = None

  @classmethod
  def call_with_creds(cls, gae_user_id, endpoint, **kwargs):
    """Makes a Google+ API call with a user's stored credentials.

    Args:
      gae_user_id: string, App Engine user id used to retrieve the
        CredentialsModel that stores the user credentials for this call
      endpoint: string, 'RESOURCE.METHOD', e.g. 'Activities.list'

    Returns: dict
    """
    credentials = StorageByKeyName(CredentialsModel, gae_user_id,
                                   'credentials').get()
    assert credentials, 'Credentials not found for user id %s' % gae_user_id
    return cls.call(credentials.authorize(cls.http), endpoint, **kwargs)

  @classmethod
  def call(cls, http, endpoint, **kwargs):
    """Makes a Google+ API call.

    Args:
      http: httplib2.Http instance
      endpoint: string, 'RESOURCE.METHOD', e.g. 'Activities.list'

    Returns: dict
    """
    if not cls.service:
      cls.service = build('plus', 'v1', cls.http)

    resource, method = endpoint.split('.')
    resource = resource.lower()
    fn = getattr(getattr(cls.service, resource)(), method)
    return fn(**kwargs).execute(http)


class GooglePlus(models.Source):
  """Implements the Salmon API for Google+."""

  DOMAIN = 'plus.google.com'

  # full human-readable name
  name = db.StringProperty()

  @staticmethod
  def new(handler, http=None):
    """Creates and returns a GooglePlus for the logged in user.

    Args:
      handler: the current webapp.RequestHandler
      http: httplib2.Http instance created with the plus_api decorator
    """
    # Google+ Person resource
    # https://developers.google.com/+/api/latest/people#resource
    person = GooglePlusService.call(http, 'people.get', userId='me')
    return GooglePlus(key_name=person['id'],
                      url=person['url'],
                      owner=models.User.get_or_insert_current_user(handler),
                      name=person['displayName'],
                      picture=person['image']['url'])

  def display_name(self):
    return self.name

  def type_display_name(self):
    return 'Google+'

  def activity_to_salmon_vars(self, activity):
    """Extracts Salmon template vars from a JSON activity.

    https://developers.google.com/+/api/latest/activies#resource

    Args:
      activity: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE
    """
    actor = activity.get('actor', {})
    content = activity.get('object', {}).get('content')
    title = activity.get('title')

    # find the attached link, if any
    link = None
    for attachment in activity.get('object', {}).get('attachments', []):
      if attachment.get('objectType') == 'article':
        link = attachment.get('url')

    vars = {
      'id': util.tag_uri(self.DOMAIN, activity.get('id')),
      'author_name': actor.get('displayName'),
      'author_uri': 'acct:%s@gmail.com' % actor.get('id'),
      'in_reply_to': link,
      'content': content,
      'title': title if title else content,
      'updated': activity.get('published'),
      }

    return vars

  def get_salmon(self):
    """Returns a list of Salmon template var dicts for posts and their comments.

    https://developers.google.com/+/api/latest/activies#resource
    https://developers.google.com/+/api/latest/comments#resource
    """
    activities = GooglePlusService.call_with_creds(
      self.owner.key().name(), 'activities.list', userId=self.key().name(),
      collection='public', maxResults=100)
    logging.debug('Received activities for user id %s:\n%s',
                  self.key().name(), activities)

    salmons = []

    for activity in activities['items']:
      salmon = self.activity_to_salmon_vars(activity)

      # only take activities with links
      link = salmon['in_reply_to']
      if not link:
        continue

      salmons.append(salmon)

      comments = GooglePlusService.call_with_creds(
        self.owner.key().name(), 'comments.list', activityId=activity['id'],
        maxResults=100)
      for comment in comments['items']:
        salmon = self.activity_to_salmon_vars(comment)
        salmon['in_reply_to'] = link
        salmons.append(salmon)

    return salmons


class AddGooglePlus(webapp2.RequestHandler):
  @plus_api.oauth_required
  def post(self):
    GooglePlus.create_new(self, http=plus_api.http())
    self.redirect('/')

  @plus_api.oauth_required
  def get(self):
    self.post()


application = webapp2.WSGIApplication([
    ('/googleplus/add', AddGooglePlus),
    ], debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
