#!/usr/bin/python
"""Unit tests for source.py.
"""

__author__ = ['Ryan Barrett <salmon@ryanb.org>']

try:
  import json
except ImportError:
  import simplejson as json
import mox

import appengine_config
import source
from webutil import testutil


ATOM_SALMON = """\
<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom'>
  <id>tag:facebook.com,2012:10102828452385634_39170557</id>
  <author>
    <name>Ryan Barrett</name>
    <uri>acct:212038@facebook-webfinger.appspot.com</uri>
  </author>
  <thr:in-reply-to xmlns:thr='http://purl.org/syndication/thread/1.0'
    ref='tag:facebook.com,2012:10102828452385634'>
    tag:facebook.com,2012:10102828452385634
  </thr:in-reply-to>
  <content>moire patterns: the new look for spring.</content>
  <title>moire patterns: the new look for spring.</title>
  <updated>2012-05-21T02:25:25+0000</updated>
</entry>"""

USER_KEY_JSON = {
  'public_exponent': 'AQAB',
  'private_exponent': 'FxCZ_ZWc1w77bAkBQQKUSvwZfaItwmIQRQ3A-KXVsL7Ay5D6tt5jbpQRmgBAYcVDXicq1fV7qa8cVT1Ed9_DusxXYGE=',
  'mod': 'uQS7soeQmMedFCFBLO2L3d7W5hLIE1Jq8IVF1hB8UPrQPQdQK5yQ3IfNkInPNRVhXJSjF9BSih2JeJ_U2lGkdVMCJe7kFMFGVa6etm2A1n6u9yNmlpxNFINyoBREJ4zcPYYLzPkTYI3kY6g71E53YjUrCPXFSu8JhmPDobC0DOc=',
}

ENVELOPE_JSON = {
  # this is base64.urlsafe_b64encode(ATOM_SALMON)
  'data':    'PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPGVudHJ5IHhtbG5zPSdodHRwOi8vd3d3LnczLm9yZy8yMDA1L0F0b20nPgogIDxpZD50YWc6ZmFjZWJvb2suY29tLDIwMTI6MTAxMDI4Mjg0NTIzODU2MzRfMzkxNzA1NTc8L2lkPgogIDxhdXRob3I-CiAgICA8bmFtZT5SeWFuIEJhcnJldHQ8L25hbWU-CiAgICA8dXJpPmFjY3Q6MjEyMDM4QGZhY2Vib29rLXdlYmZpbmdlci5hcHBzcG90LmNvbTwvdXJpPgogIDwvYXV0aG9yPgogIDx0aHI6aW4tcmVwbHktdG8geG1sbnM6dGhyPSdodHRwOi8vcHVybC5vcmcvc3luZGljYXRpb24vdGhyZWFkLzEuMCcKICAgIHJlZj0ndGFnOmZhY2Vib29rLmNvbSwyMDEyOjEwMTAyODI4NDUyMzg1NjM0Jz4KICAgIHRhZzpmYWNlYm9vay5jb20sMjAxMjoxMDEwMjgyODQ1MjM4NTYzNAogIDwvdGhyOmluLXJlcGx5LXRvPgogIDxjb250ZW50Pm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L2NvbnRlbnQ-CiAgPHRpdGxlPm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L3RpdGxlPgogIDx1cGRhdGVkPjIwMTItMDUtMjFUMDI6MjU6MjUrMDAwMDwvdXBkYXRlZD4KPC9lbnRyeT4',
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
  # >>> base64.urlsafe_b64encode(ATOM_SALMON)
  # ...
  # >>> base64.urlsafe_b64encode('application/atom+xml').rstrip('=')
  # 'YXBwbGljYXRpb24vYXRvbSt4bWw'
  # >>> base64.urlsafe_b64encode('base64url').rstrip('=')
  # 'YmFzZTY0dXJs'
  # >>> base64.urlsafe_b64encode('RSA-SHA256').rstrip('=')
  # 'UlNBLVNIQTI1Ng'
  # ...
  # PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPGVudHJ5IHhtbG5zPSdodHRwOi8vd3d3LnczLm9yZy8yMDA1L0F0b20nPgogIDxpZD50YWc6ZmFjZWJvb2suY29tLDIwMTI6MTAxMDI4Mjg0NTIzODU2MzRfMzkxNzA1NTc8L2lkPgogIDxhdXRob3I-CiAgICA8bmFtZT5SeWFuIEJhcnJldHQ8L25hbWU-CiAgICA8dXJpPmFjY3Q6MjEyMDM4QGZhY2Vib29rLXdlYmZpbmdlci5hcHBzcG90LmNvbTwvdXJpPgogIDwvYXV0aG9yPgogIDx0aHI6aW4tcmVwbHktdG8geG1sbnM6dGhyPSdodHRwOi8vcHVybC5vcmcvc3luZGljYXRpb24vdGhyZWFkLzEuMCcKICAgIHJlZj0ndGFnOmZhY2Vib29rLmNvbSwyMDEyOjEwMTAyODI4NDUyMzg1NjM0Jz4KICAgIHRhZzpmYWNlYm9vay5jb20sMjAxMjoxMDEwMjgyODQ1MjM4NTYzNAogIDwvdGhyOmluLXJlcGx5LXRvPgogIDxjb250ZW50Pm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L2NvbnRlbnQ-CiAgPHRpdGxlPm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L3RpdGxlPgogIDx1cGRhdGVkPjIwMTItMDUtMjFUMDI6MjU6MjUrMDAwMDwvdXBkYXRlZD4KPC9lbnRyeT4.YXBwbGljYXRpb24vYXRvbSt4bWw.YmFzZTY0dXJs.UlNBLVNIQTI1Ng
  'sigs': [{
      # this is what sign.sh says, but it's not right. not sure why. :/
      # 'value': 'PbwL0bMBBQNW_yxS1nutL2lni31fbpS1Q6LA8fDKt3cbCSzdxPZEbmoL-xnVu3ilelWeiCvzrVXVjMWEnsnVX-bCWi-_zuEwdKOw2Fgn0ejYcY_OJYgpdZYskWOPzErLBPhI0fUf0-jDjG-roiLVmjsdZDlvGDeCspQIXkRw6uk',
      'value': 'hOR6i-xZZ7Q5Aj_KNPSF1rYIgJbX3kqw90QCO6Rrv2KQW7cWC1gITOpfSyd2slek2NQLwSj4vzBecvD-16Jb-YpcBiD6Roppok4t4aZrJppX6ZZZ6i6T3FGPEiH1_yl_QeIfDXduS-bwS5KETvtvQIRSd8FK0CBK686D4YhfrHY=',
      }],
  }

ENVELOPE_XML = """\
<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env">
<me:data type="application/atom+xml">
PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPGVudHJ5IHhtbG5zPSdodHRwOi8vd3d3LnczLm9yZy8yMDA1L0F0b20nPgogIDxpZD50YWc6ZmFjZWJvb2suY29tLDIwMTI6MTAxMDI4Mjg0NTIzODU2MzRfMzkxNzA1NTc8L2lkPgogIDxhdXRob3I-CiAgICA8bmFtZT5SeWFuIEJhcnJldHQ8L25hbWU-CiAgICA8dXJpPmFjY3Q6MjEyMDM4QGZhY2Vib29rLXdlYmZpbmdlci5hcHBzcG90LmNvbTwvdXJpPgogIDwvYXV0aG9yPgogIDx0aHI6aW4tcmVwbHktdG8geG1sbnM6dGhyPSdodHRwOi8vcHVybC5vcmcvc3luZGljYXRpb24vdGhyZWFkLzEuMCcKICAgIHJlZj0ndGFnOmZhY2Vib29rLmNvbSwyMDEyOjEwMTAyODI4NDUyMzg1NjM0Jz4KICAgIHRhZzpmYWNlYm9vay5jb20sMjAxMjoxMDEwMjgyODQ1MjM4NTYzNAogIDwvdGhyOmluLXJlcGx5LXRvPgogIDxjb250ZW50Pm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L2NvbnRlbnQ-CiAgPHRpdGxlPm1vaXJlIHBhdHRlcm5zOiB0aGUgbmV3IGxvb2sgZm9yIHNwcmluZy48L3RpdGxlPgogIDx1cGRhdGVkPjIwMTItMDUtMjFUMDI6MjU6MjUrMDAwMDwvdXBkYXRlZD4KPC9lbnRyeT4=
</me:data>
<me:encoding>
base64url
</me:encoding>
<me:alg>
RSA-SHA256
</me:alg>
<me:sig>
hOR6i-xZZ7Q5Aj_KNPSF1rYIgJbX3kqw90QCO6Rrv2KQW7cWC1gITOpfSyd2slek2NQLwSj4vzBecvD-16Jb-YpcBiD6Roppok4t4aZrJppX6ZZZ6i6T3FGPEiH1_yl_QeIfDXduS-bwS5KETvtvQIRSd8FK0CBK686D4YhfrHY=
</me:sig>

</me:env>
"""


class SourceTest(testutil.HandlerTest):

  def setUp(self):
    super(SourceTest, self).setUp()
    self.source = source.Source(self.handler)
    appengine_config.USER_KEY_HANDLER_SECRET = 'my_secret'

  def test_envelope(self):
    self.expect_urlfetch('https://facebook-webfinger.appspot.com/user_key'
                         '?uri=acct:ryan@facebook.com&secret=my_secret',
                         json.dumps(USER_KEY_JSON))
    self.mox.ReplayAll()

    envelope = self.source.envelope(ATOM_SALMON, 'acct:ryan@facebook.com')\
        .replace('>', '>\n').replace('</', '\n</')
    self.assert_multiline_equals(ENVELOPE_XML, envelope)
