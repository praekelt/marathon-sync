import json

from twisted.internet.defer import (
    inlineCallbacks, DeferredQueue, Deferred, succeed)
from twisted.python import log
from twisted.trial.unittest import TestCase

from marathon_sync.main import (
    MarathonSync, normalise_app_id, normalise_group_id)


class NormalisersTest(TestCase):
    def test_normalise_group_id_no_leading_slash(self):
        """ Group IDs without a leading '/' should have one added. """
        normalised = normalise_group_id('test/abc')
        self.assertEqual(normalised, '/test/abc')

    def test_normalise_group_id_trailing_slash(self):
        """ Group IDs with a trailing '/' should have it removed. """
        normalised = normalise_group_id('/test/abc/')
        self.assertEqual(normalised, '/test/abc')

    def test_normalise_group_id_empty(self):
        """ Empty group IDs should be considered the root group ID. """
        normalised = normalise_group_id('')
        self.assertEqual(normalised, '/')

    def test_normalise_group_id_root(self):
        """ The root group ID should be recognised and returned unchanged. """
        normalised = normalise_group_id('/')
        self.assertEqual(normalised, '/')

    def test_normalise_group_id_normal(self):
        """ A normal group ID should be returned unchanged. """
        normalised = normalise_group_id('/test/abc')
        self.assertEqual(normalised, '/test/abc')

    def test_normalise_app_id(self):
        """ App IDs should be appended to their group ID. """
        normalised = normalise_app_id('app', '/test/abc')
        self.assertEqual(normalised, '/test/abc/app')

    def test_normalise_app_id_root(self):
        """
        App IDs should be appended to their group ID when the group ID is root.
        """
        normalised = normalise_app_id('app', '/')
        self.assertEqual(normalised, '/app')

    def test_normalise_app_id_trailing_slash(self):
        """ App IDs with a trailing '/' should have it removed. """
        normalised = normalise_app_id('app/', '/test/abc')
        self.assertEqual(normalised, '/test/abc/app')

    def test_normalise_app_id_normal(self):
        """ A normal app ID should be returned unchanged. """
        normalised = normalise_app_id('/test/abc/app', '/test/abc')
        self.assertEqual(normalised, '/test/abc/app')


class FakeResponse(object):

    def __init__(self, code, headers, content=None):
        self.code = code
        self.headers = headers
        self._content = content

    def content(self):
        return succeed(self._content)

    def json(self):
        d = self.content()
        d.addCallback(lambda content: json.loads(content) if content else None)
        return d


class MarathonSyncTest(TestCase):

    def setUp(self):
        self.marathon_sync = MarathonSync('http://1.2.3.4:8080', [])

        # We use this to mock requests going to Marathon
        self.requests = DeferredQueue()

        def mock_requests(method, url, headers, data):
            d = Deferred()
            self.requests.put({
                'method': method,
                'url': url,
                'data': data,
                'deferred': d,
            })
            return d

        self.patch(self.marathon_sync, 'requester', mock_requests)

    def tearDown(self):
        pass

    @inlineCallbacks
    def test_delete_unknown_apps(self):
        self.marathon_sync.groups = [
            {
                'id': 'test1',
                'apps': [
                    {'id': 'app1'},
                    {'id': 'app2'}
                ]
            },
            {
                'id': 'test2',
                'apps': [
                    {'id': 'app1'}
                ]
            }
        ]
        d = self.marathon_sync.delete_unknown_apps()
        d.addErrback(log.err)

        get_request = yield self.requests.get()
        self.assertEqual(get_request['url'], 'http://1.2.3.4:8080/v2/apps')
        self.assertEqual(get_request['method'], 'GET')

        # Return 2 out of 3 of the known apps plus 1 unknown app
        get_request['deferred'].callback(FakeResponse(200, [], json.dumps({
            'apps': [
                {'id': '/test1/app1'},
                {'id': '/test2/app1'},
                {'id': '/app2'}
            ]
        })))

        delete_request = yield self.requests.get()
        self.assertEqual(delete_request['url'],
                         'http://1.2.3.4:8080/v2/apps/app2')
        self.assertEqual(delete_request['method'], 'DELETE')

        delete_request['deferred'].callback(FakeResponse(200, [], json.dumps({
            "version": "2015-08-25T10:06:19.918Z",
            "deploymentId": "7828f718-ef25-426b-9d80-82ad3b39c8ae"
        })))

        yield d

    @inlineCallbacks
    def test_sync_apps(self):
        self.marathon_sync.groups = [
            {
                'id': 'test1',
                'apps': [
                    {'id': 'app1'},
                    {'id': 'app2'}
                ]
            },
            {
                'id': 'test2',
                'apps': [
                    {'id': 'app1'}
                ]
            }
        ]
        d = self.marathon_sync.sync_apps()
        d.addErrback(log.err)

        request1 = yield self.requests.get()
        self.assertEqual(request1['url'], 'http://1.2.3.4:8080/v2/groups')
        self.assertEqual(request1['method'], 'PUT')
        self.assertEqual(request1['data'], json.dumps({
            'id': 'test1',
            'apps': [
                {'id': 'app1'},
                {'id': 'app2'}
            ]
        }))
        request1['deferred'].callback(FakeResponse(200, [], json.dumps({
            "version": "2015-08-25T08:36:47.314Z",
            "deploymentId": "54ba4426-433d-4d38-b97e-5b9e3ac9d027"
        })))

        request2 = yield self.requests.get()
        self.assertEqual(request2['url'], 'http://1.2.3.4:8080/v2/groups')
        self.assertEqual(request2['method'], 'PUT')
        self.assertEqual(request2['data'], json.dumps({
            'id': 'test2',
            'apps': [
                {'id': 'app1'}
            ]
        }))
        request2['deferred'].callback(FakeResponse(200, [], json.dumps({
            "version": "2015-08-25T09:50:54.340Z",
            "deploymentId": "54393ec8-e93e-4132-abe6-e78e4545a965"
        })))

        yield d
