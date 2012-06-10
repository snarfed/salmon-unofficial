#!/usr/bin/python
"""Unit tests for models.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

from models import Domain, User
from fakes import FakeSite, FakeSource#, FakeDestination
import util
from webutil import testutil

from google.appengine.api import users
from google.appengine.datastore import datastore_stub_util


class UserTest(testutil.HandlerTest):

  def test_no_logged_in_user(self):
    self.testbed.setup_env(overwrite=True, user_id='', user_email='')
    self.assertEqual(None, users.get_current_user())
    self.assertEqual(None, User.get_current_user())
    self.assertEqual(None, User.get_or_insert_current_user(self.handler))

  def test_user(self):
    self.assertEqual(0, User.all().count())
    self.assertEqual(None, User.get_current_user())

    user = User.get_or_insert_current_user(self.handler)
    self.assertEqual(self.current_user_id, user.key().name())
    self.assert_entities_equal([User(key_name=self.current_user_id)], User.all())


class SiteTest(testutil.HandlerTest):

  def _test_create_new(self):
    FakeSite.create_new(self.handler)
    self.assertEqual(1, FakeSite.all().count())
    self.assertEqual(0, len(self.taskqueue_stub.GetTasks('poll')))

  def test_create_new(self):
    self.assertEqual(0, FakeSite.all().count())
    self._test_create_new()
    self.assertEqual(1, FakeSite.all().count())

  def test_create_new_already_exists(self):
    FakeSite.new(None).save()
    self.assertEqual(1, FakeSite.all().count())

    FakeSite.key_name_counter -= 1
    self._test_create_new()
    self.assertEqual(1, FakeSite.all().count())


class SourceTest(testutil.HandlerTest):

  def _test_create_new(self):
    FakeSource.create_new(self.handler)
    self.assertEqual(1, FakeSource.all().count())

    tasks = self.taskqueue_stub.GetTasks('poll')
    self.assertEqual(1, len(tasks))
    source = FakeSource.all().get()
    self.assertEqual('/_ah/queue/poll', tasks[0]['url'])
    params = testutil.get_task_params(tasks[0])
    self.assertEqual(str(source.key()), params['source_key'])
    self.assertEqual('1970-01-01-00-00-00',
                     params['last_polled'])

  def test_create_new(self):
    self.assertEqual(0, FakeSource.all().count())
    self._test_create_new()

  def test_create_new_already_exists(self):
    FakeSource.new(None).save()
    FakeSource.key_name_counter -= 1
    self._test_create_new()

