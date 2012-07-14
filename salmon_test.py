#!/usr/bin/python
"""Unit tests for salmon.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

import json
import mox
from webob import exc

import appengine_config
import salmon
from webutil import testutil


SALMON_VARS = {
  'id': 'tag:facebook.com,2012:10102828452385634_39170557',
  'author_name': 'Ryan Barrett',
  'author_uri': 'acct:212038@facebook-webfinger.appspot.com',
  'in_reply_to': 'http://my.blog/post',
  'content': 'moire patterns: the new look for spring.',
  'title': 'moire patterns: the new look for spring.',
  'updated': '2012-05-21T02:25:25+0000',
  }

USER_KEY_URL = (
    'https://facebook-webfinger.appspot.com/user_key?'
    'uri=acct:212038@facebook-webfinger.appspot.com&secret=my_secret')

USER_KEY_JSON = {
  'public_exponent': 'AQAB',
  'private_exponent': 'FxCZ_ZWc1w77bAkBQQKUSvwZfaItwmIQRQ3A-KXVsL7Ay5D6tt5jbpQRmgBAYcVDXicq1fV7qa8cVT1Ed9_DusxXYGE=',
  'mod': 'uQS7soeQmMedFCFBLO2L3d7W5hLIE1Jq8IVF1hB8UPrQPQdQK5yQ3IfNkInPNRVhXJSjF9BSih2JeJ_U2lGkdVMCJe7kFMFGVa6etm2A1n6u9yNmlpxNFINyoBREJ4zcPYYLzPkTYI3kY6g71E53YjUrCPXFSu8JhmPDobC0DOc=',
}

ENVELOPE_JSON = {
  # this is base64.urlsafe_b64encode(ATOM_SALMON_TEMPLATE % SALMON_VARS)
  'data': 'PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPGVudHJ5IHhtbG5zPSdodHRwOi8vd3d3LnczLm9yZy8yMDA1L0F0b20nPgogIDxpZD50YWc6ZmFjZWJvb2suY29tLDIwMTI6MTAxMDI4Mjg0NTIzODU2MzRfMzkxNzA1NTc8L2lkPgogIDxhdXRob3I-CiAgICA8bmFtZT5SeWFuIEJhcnJldHQ8L25hbWU-CiAgICA8dXJpPmFjY3Q6MjEyMDM4QGZhY2Vib29rLXdlYmZpbmdlci5hcHBzcG90LmNvbTwvdXJpPgogIDwvYXV0aG9yPgogIDx0aHI6aW4tcmVwbHktdG8geG1sbnM6dGhyPSdodHRwOi8vcHVybC5vcmcvc3luZGljYXRpb24vdGhyZWFkLzEuMCcKICAgIHJlZj0naHR0cDovL215LmJsb2cvcG9zdCc-CiAgICBodHRwOi8vbXkuYmxvZy9wb3N0CiAgPC90aHI6aW4tcmVwbHktdG8-CiAgPGNvbnRlbnQ-bW9pcmUgcGF0dGVybnM6IHRoZSBuZXcgbG9vayBmb3Igc3ByaW5nLjwvY29udGVudD4KICA8dGl0bGU-bW9pcmUgcGF0dGVybnM6IHRoZSBuZXcgbG9vayBmb3Igc3ByaW5nLjwvdGl0bGU-CiAgPHVwZGF0ZWQ-MjAxMi0wNS0yMVQwMjoyNToyNSswMDAwPC91cGRhdGVkPgo8L2VudHJ5Pg==',
  'data_type': 'application/atom+xml',
  'encoding': 'base64url',
  'alg': 'RSA-SHA256',
  # the signature base string is based on section 3.2 of the magic sig spec:
  # http://salmon-protocol.googlecode.com/svn/trunk/draft-panzer-magicsig-01.html#sbs
  #
  # used https://github.com/eschnou/salmon-bash :
  # ./sign.sh input.txt key.pem
  #
  # here, it's these components, in order, joined with period (.) separators:
  # >>> base64.urlsafe_b64encode(ATOM_SALMON_TEMPLATE % SALMON_VARS)
  # ...
  # >>> base64.urlsafe_b64encode('application/atom+xml').rstrip('=')
  # 'YXBwbGljYXRpb24vYXRvbSt4bWw'
  # >>> base64.urlsafe_b64encode('base64url').rstrip('=')
  # 'YmFzZTY0dXJs'
  # >>> base64.urlsafe_b64encode('RSA-SHA256').rstrip('=')
  # 'UlNBLVNIQTI1Ng'
  # ...
  'sigs': [{
      # sign.sh says it's something else. not sure why. :/
      'value': 'ZT07BcAOjdQuVTTnfR9Eq5pAZBLzhllbd3794tAeOYh3QVGSH4KjgBUEWfRsdFPrFJdAw1ZTWjP-59Qw014DPgUov1fIEwQ4ck1Q6BJS0PLLgeDKAwbuar2PL6Iw4mZ0s7FYorMTDtzUGV2sp-P_iHc0JXu2J63jwzSdzwCJwA0=',
      }],
  }

ENVELOPE_XML = salmon.XML_DOCTYPE_LINE + """
<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env">
<me:data type="application/atom+xml">
PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPGVudHJ5IHhtbG5zPSdodHRwOi8vd3d3LnczLm9yZy8yMDA1L0F0b20nPgogIDxpZD50YWc6ZmFjZWJvb2suY29tLDIwMTI6MTAxMDI4Mjg0NTIzODU2MzRfMzkxNzA1NTc8L2lkPgogIDxhdXRob3I-CiAgICA8bmFtZT5SeWFuIEJhcnJldHQ8L25hbWU-CiAgICA8dXJpPmFjY3Q6MjEyMDM4QGZhY2Vib29rLXdlYmZpbmdlci5hcHBzcG90LmNvbTwvdXJpPgogIDwvYXV0aG9yPgogIDx0aHI6aW4tcmVwbHktdG8geG1sbnM6dGhyPSdodHRwOi8vcHVybC5vcmcvc3luZGljYXRpb24vdGhyZWFkLzEuMCcKICAgIHJlZj0naHR0cDovL215LmJsb2cvcG9zdCc-CiAgICBodHRwOi8vbXkuYmxvZy9wb3N0CiAgPC90aHI6aW4tcmVwbHktdG8-CiAgPGNvbnRlbnQ-bW9pcmUgcGF0dGVybnM6IHRoZSBuZXcgbG9vayBmb3Igc3ByaW5nLjwvY29udGVudD4KICA8dGl0bGU-bW9pcmUgcGF0dGVybnM6IHRoZSBuZXcgbG9vayBmb3Igc3ByaW5nLjwvdGl0bGU-CiAgPHVwZGF0ZWQ-MjAxMi0wNS0yMVQwMjoyNToyNSswMDAwPC91cGRhdGVkPgo8L2VudHJ5Pg==
</me:data>
<me:encoding>
base64url
</me:encoding>
<me:alg>
RSA-SHA256
</me:alg>
<me:sig>
ZT07BcAOjdQuVTTnfR9Eq5pAZBLzhllbd3794tAeOYh3QVGSH4KjgBUEWfRsdFPrFJdAw1ZTWjP-59Qw014DPgUov1fIEwQ4ck1Q6BJS0PLLgeDKAwbuar2PL6Iw4mZ0s7FYorMTDtzUGV2sp-P_iHc0JXu2J63jwzSdzwCJwA0=
</me:sig>

</me:env>
""".replace('\n', '')


class SalmonTest(testutil.HandlerTest):

  def setUp(self):
    super(SalmonTest, self).setUp()
    self.salmon = salmon.Salmon(key_name='tag:xyz', vars=json.dumps(SALMON_VARS))
    appengine_config.USER_KEY_HANDLER_SECRET = 'my_secret'

  def test_get_or_save(self):
    self.assertEqual(0, salmon.Salmon.all().count())
    self.assertEqual(0, len(self.taskqueue_stub.GetTasks('propagate')))

    # new. should add a propagate task.
    saved = self.salmon.get_or_save()
    self.assertTrue(saved.is_saved())
    self.assertEqual(self.salmon.key(), saved.key())

    tasks = self.taskqueue_stub.GetTasks('propagate')
    self.assertEqual(1, len(tasks))
    self.assertEqual(str(self.salmon.key()),
                     testutil.get_task_params(tasks[0])['salmon_key'])
    self.assertEqual('/_ah/queue/propagate', tasks[0]['url'])

    # existing. no new task.
    same = saved.get_or_save()
    self.assertEqual(1, len(tasks))

  def test_envelope(self):
    self.expect_urlfetch(USER_KEY_URL, json.dumps(USER_KEY_JSON))
    self.mox.ReplayAll()

    envelope = self.salmon.envelope()
    self.assert_multiline_equals(ENVELOPE_XML, envelope)

  def test_send_slap(self):
    self.mox.StubOutWithMock(self.salmon, 'discover_salmon_endpoint')
    self.salmon.discover_salmon_endpoint().AndReturn('http://my/endpoint')
    self.expect_urlfetch(USER_KEY_URL, json.dumps(USER_KEY_JSON))
    self.expect_urlfetch('http://my/endpoint', 'response', method='POST',
                         headers=salmon.SLAP_HTTP_HEADERS, payload=ENVELOPE_XML)
    self.mox.ReplayAll()

    self.salmon.send_slap()

  def test_send_slap__no_endpoint_found(self):
    self.mox.StubOutWithMock(self.salmon, 'discover_salmon_endpoint')
    self.salmon.discover_salmon_endpoint().AndReturn(None)
    # expect no urlfetch to send the slap
    self.mox.ReplayAll()

    self.salmon.send_slap()

  def test_send_slap__error_discovering_endpoint(self):
    self.mox.StubOutWithMock(self.salmon, 'discover_salmon_endpoint')
    self.salmon.discover_salmon_endpoint().AndRaise(exc.HTTPNotFound())
    # expect no urlfetch to send the slap
    self.mox.ReplayAll()

    self.salmon.send_slap()

  def test_send_slap__error_sending(self):
    self.mox.StubOutWithMock(self.salmon, 'discover_salmon_endpoint')
    self.salmon.discover_salmon_endpoint().AndReturn('http://my/endpoint')
    self.expect_urlfetch(USER_KEY_URL, json.dumps(USER_KEY_JSON))
    self.expect_urlfetch('http://my/endpoint', 'response', method='POST',
                         headers=salmon.SLAP_HTTP_HEADERS, payload=ENVELOPE_XML,
                         status=404)
    self.mox.ReplayAll()

    self.salmon.send_slap()

  def test_discover_salmon_endpoint__found_in_html(self):
    self.expect_urlfetch(
      'http://my.blog/post',
      '<html><head><link rel="salmon" href="my endpoint" /></head></html>')
    self.mox.ReplayAll()

    self.assertEquals('my endpoint', self.salmon.discover_salmon_endpoint())

  def test_discover_salmon_endpoint__found_in_feed(self):
    self.expect_urlfetch('http://my.blog/post', """
<html><head>
<link rel="foo alternate" type="application/rss+xml" href="my.blog/feed" />
</head></html>""")
    self.expect_urlfetch('my.blog/feed', """
<rss><channel>
<link rel="salmon" href="my endpoint" type="" />
</channel></rss>""")
    self.mox.ReplayAll()

    self.assertEquals('my endpoint', self.salmon.discover_salmon_endpoint())

  def test_discover_salmon_endpoint__found_in_hostmeta(self):
    self.expect_urlfetch('http://my.blog/post', '<html></html>')
    self.expect_urlfetch(
      'http://my.blog/.well-known/host-meta',
      '<XRD><Link rel="salmon" href="my endpoint"></Link></XRD>')
    self.mox.ReplayAll()

    self.assertEquals('my endpoint', self.salmon.discover_salmon_endpoint())

  # not ready yet. see the TODO in the salmon.py docstring.
  #
  # def test_discover_salmon_endpoint__found_in_user_lrdd(self):
  #   self.expect_urlfetch('http://my.blog/post', '<html></html>')
  #   self.expect_urlfetch(
  #     'http://my.blog/.well-known/host-meta',
  #     '<XRD><Link rel="lrdd" template="http://foo/{uri}/bar"></Link></XRD>')
  #   self.expect_urlfetch(
  #     'http://foo/acct:',
  #     '<XRD><Link rel="lrdd" template="http://foo/{uri}/bar"></Link></XRD>')
  #   self.mox.ReplayAll()

  #   self.assertEquals('my endpoint', self.salmon.discover_salmon_endpoint())

  def test_discover_salmon_endpoint__not_found(self):
    self.expect_urlfetch('http://my.blog/post', """
<html><head>
<link rel="foo alternate" type="application/rss+xml" href="my.blog/feed" />
</head></html>""")
    self.expect_urlfetch('my.blog/feed', '<rss><channel></channel></rss>')
    self.expect_urlfetch('http://my.blog/.well-known/host-meta', '<XRD></XRD>')
    self.mox.ReplayAll()

    self.assertEquals(None, self.salmon.discover_salmon_endpoint())
