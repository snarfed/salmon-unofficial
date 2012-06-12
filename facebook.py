#!/usr/bin/python
"""Facebook source class.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import json
import logging
import urllib
import urlparse

import appengine_config
import models

from webutil import util
from webutil import webapp2

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

# facebook api url templates. can't (easily) use urllib.urlencode() because i
# want to keep the %(...)s placeholders as is and fill them in later in code.
# TODO: use appengine_config.py for local mockfacebook vs prod facebook
GET_AUTH_CODE_URL = '&'.join((
    ('http://localhost:8000/dialog/oauth/?'
     if appengine_config.MOCKFACEBOOK else
     'https://www.facebook.com/dialog/oauth/?'),
    'scope=read_stream,offline_access',
    'client_id=%(client_id)s',
    # redirect_uri here must be the same in the access token request!
    'redirect_uri=%(host_url)s/facebook/got_auth_code',
    'response_type=code',
    'state=%(state)s',
    ))

GET_ACCESS_TOKEN_URL = '&'.join((
    ('http://localhost:8000/oauth/access_token?'
     if appengine_config.MOCKFACEBOOK else
     'https://graph.facebook.com/oauth/access_token?'),
    'client_id=%(client_id)s',
    # redirect_uri here must be the same in the oauth request!
    # (the value here doesn't actually matter since it's requested server side.)
    'redirect_uri=%(host_url)s/facebook/got_auth_code',
    'client_secret=%(client_secret)s',
    'code=%(auth_code)s',
    ))

API_USER_URL = 'https://graph.facebook.com/%(id)s?access_token=%(access_token)s'


class Facebook(models.Source):
  """Implements the Salmon API for Facebook.
  """

  DOMAIN = 'facebook.com'

  # full human-readable name
  name = db.StringProperty()

  # the token should be generated with the offline_access scope so that it
  # doesn't expire. details: http://developers.facebook.com/docs/authentication/
  access_token = db.StringProperty()

  def display_name(self):
    return self.name

  @staticmethod
  def new(handler):
    """Creates and returns a Facebook for the logged in user.

    Args:
      handler: the current webapp2.RequestHandler
    """
    access_token = handler.request.get('access_token')
    resp = util.urlfetch(API_USER_URL % {'id': 'me', 'access_token': access_token})
    me = json.loads(resp)

    id = me['id']
    return Facebook(
      key_name=id,
      owner=models.User.get_or_insert_current_user(handler),
      access_token=access_token,
      name=me.get('name', {}).get('formatted'),
      picture='https://graph.facebook.com/%s/picture?type=small' % id,
      url='http://facebook.com/%s' % id)

  def comment_to_salmon_vars(self, comment):
    """Extracts Salmon template vars from a JSON Facebook comment.

    Args:
      comment: JSON dict

    Returns: dict of template vars for ATOM_SALMON_TEMPLATE

    Raises:
      ValueError if comment['id'] cannot be parsed. It should be of the form
      PARENT_COMMENT
    """
    id = comment.get('id', '')
    parent_id, _, cmt_id = id.partition('_')
    if not parent_id or not cmt_id:
      raise ValueError('Could not parse comment id: %s' % id)

    cmt_from = comment.get('from', {})

    return {
      'id_tag': util.tag_uri(self.DOMAIN, id),
      'author_name': cmt_from.get('name'),
      'author_uri': 'acct:%s@facebook-webfinger.appspot.com' % cmt_from.get('id'),
      # TODO: this should be the original domain link
      'in_reply_to_tag': util.tag_uri(self.DOMAIN, parent_id),
      'content': comment.get('message'),
      'title': comment.get('message'),
      'updated': comment.get('created_time'),
      }


class AddFacebook(webapp2.RequestHandler):
  def post(self):
    """Gets an access token for the current user.

    Actually just gets the auth code and redirects to /facebook_got_auth_code,
    which makes the next request to get the access token.
    """
    redirect_uri = '/facebook/got_access_token'

    url = GET_AUTH_CODE_URL % {
      'client_id': appengine_config.FACEBOOK_APP_ID,
      # TODO: CSRF protection identifier.
      # http://developers.facebook.com/docs/authentication/
      'host_url': self.request.host_url,
      'state': self.request.host_url + redirect_uri,
      # 'state': urllib.quote(json.dumps({'redirect_uri': redirect_uri})),
      }
    self.redirect(url)


class GotAuthCode(webapp2.RequestHandler):
  def get(self):
    """Gets an access token based on an auth code."""
    auth_code = self.request.get('code')
    assert auth_code

    redirect_uri = urllib.unquote(self.request.get('state'))
    assert '?' not in redirect_uri

    # TODO: handle permission declines, errors, etc
    url = GET_ACCESS_TOKEN_URL % {
      'auth_code': auth_code,
      'client_id': appengine_config.FACEBOOK_APP_ID,
      'client_secret': appengine_config.FACEBOOK_APP_SECRET,
      'host_url': self.request.host_url,
      }
    resp = urlfetch.fetch(url, deadline=999)
    # TODO: error handling. handle permission declines, errors, etc
    logging.debug('access token response: %s' % resp.content)
    params = urlparse.parse_qs(resp.content)
    access_token = params['access_token'][0]

    url = '%s?access_token=%s' % (redirect_uri, access_token)
    self.redirect(url)
    

class GotAccessToken(webapp2.RequestHandler):
  def get(self):
    Facebook.create_new(self)
    self.redirect('/')


application = webapp2.WSGIApplication([
    ('/facebook/add', AddFacebook),
    ('/facebook/got_auth_code', GotAuthCode),
    ('/facebook/got_access_token', GotAccessToken),
    ], debug=appengine_config.DEBUG)

def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
