import json
import sys

from twisted.internet.task import react
from twisted.python import usage


class Options(usage.Options):
    optParameters = [
        ["marathon", "m", "http://localhost:8080",
         "The address for the Marathon HTTP API endpoint."],
        ["config", "c", None,
         "The path to a config file containing a list of paths to Marathon "
         "JSON group definitions."],
    ]

    def postOptions(self):
        if self['config'] is None:
            raise usage.UsageError("Please specify a config file.")


def load_config_groups(config_path):
    group_paths = read_config(config_path)
    return [read_group(group_path) for group_path in group_paths]


def read_config(config_path):
    group_paths = []
    with open(config_path) as config_file:
        for line in config_file:
            group_path = line.strip()
            if group_path:
                group_paths.append(group_path)
    return group_paths


def read_group(group_path):
    with open(group_path) as group_file:
        return json.load(group_file)


def main(_reactor, name, *args):
    from marathon_sync.main import MarathonSync
    from twisted.python import log

    log.startLogging(sys.stdout)

    try:
        options = Options()
        options.parseOptions(args)
    except usage.UsageError, errortext:
        print '%s: %s' % (name, errortext)
        print '%s: Try --help for usage details.' % (name,)
        sys.exit(1)

    marathon_endpoint = options['marathon']
    groups = load_config_groups(options['config'])

    marathon_sync = MarathonSync(marathon_endpoint, groups)
    return marathon_sync.run()


def entry_point():
    react(main, sys.argv)

if __name__ == '__main__':
    entry_point()
