import json
import treq

from twisted.python import log
from twisted.web import client
# Twisted's default HTTP11 client factory is way too verbose
client._HTTP11ClientFactory.noisy = False
from twisted.internet.defer import (
    gatherResults, inlineCallbacks, returnValue)


def normalise_group_id(group_id):
    """
    Group IDs can be specified with or without leading and trailing '/'s. We
    want a leading '/' but not a trailing one.
    """
    if not group_id.startswith('/'):
        group_id = '/' + group_id

    if group_id.endswith('/') and group_id != '/':
        group_id = group_id[:-1]

    return group_id


def normalise_app_id(app_id, group_id):
    """
    App IDs can be specified with or without a trailing '/' and with or without
    leading group IDs if specified within a group definition. We want the
    fully-qualified app ID with its group ID.

    :param: group_id
    Expects an already normalised group ID.
    """
    if app_id.endswith('/'):
        app_id = app_id[:-1]

    if not app_id.startswith(group_id):
        if group_id != '/':
            app_id = group_id + '/' + app_id
        else:
            app_id = group_id + app_id

    return app_id


class MarathonSync(object):

    requester = lambda self, *a, **kw: treq.request(*a, **kw)

    def __init__(self, marathon_endpoint, groups):
        self.marathon_endpoint = marathon_endpoint
        self.groups = groups

    @inlineCallbacks
    def run(self):
        yield self.delete_unknown_apps()
        yield self.sync_apps()

    @inlineCallbacks
    def delete_unknown_apps(self):
        """
        Delete apps in Marathon that are not defined in the loaded config.
        """
        known_apps = self.collect_known_apps()
        present_apps = yield self.collect_present_apps()
        log.msg('Found %d apps in the config, %d apps in Marathon'
                % (len(known_apps), len(present_apps)))

        # Delete the difference between the two sets of apps
        unknown_apps = present_apps - known_apps
        log.msg('Deleting %d unknown apps...' % len(unknown_apps))
        yield gatherResults([self.delete_marathon_app(app_id)
                             for app_id in unknown_apps])

    def collect_known_apps(self):
        known_apps = set()
        for group in self.groups:
            apps = self.parse_group_apps(group)
            for app in apps:
                known_apps.add(app)
        return known_apps

    @inlineCallbacks
    def collect_present_apps(self):
        apps_json = yield self.get_marathon_apps()
        returnValue(set([app['id'] for app in apps_json['apps']]))

    def sync_apps(self):
        """
        Push all the group definitions to Marathon. Let Marathon handle the
        updates.
        """
        log.msg('Syncing %d groups...' % len(self.groups))
        return gatherResults([self.put_marathon_group(group)
                             for group in self.groups])

    def parse_group_apps(self, group_json):
        """
        Get the app IDs from a group definition, normalising the app IDs to the
        fully-qualified paths that Marathon will return to us when we ask it
        for a list of apps.
        """
        group_id = normalise_group_id(group_json['id'])

        apps_json = group_json['apps']
        apps = [normalise_app_id(app_json['id'], group_id)
                for app_json in apps_json]

        return apps

    def get_marathon_apps(self):
        return self.marathon_request('GET', '/v2/apps')

    def delete_marathon_app(self, app_id):
        return self.marathon_request('DELETE', '/v2/apps%s' % (app_id,))

    def put_marathon_group(self, group_json):
        return self.marathon_request('PUT', '/v2/groups', group_json)

    def marathon_request(self, method, path, data=None):
        return self._json_request(
            method, '%s%s' % (self.marathon_endpoint, path), data)

    def _json_request(self, method, url, data):
        d = self.requester(
            method,
            url.encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            data=(json.dumps(data) if data is not None else None))
        d.addCallback(lambda response: response.json())
        return d
