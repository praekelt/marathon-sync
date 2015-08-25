# marathon-sync

`marathon-sync` is a simple tool that helps manage the state of apps running in [Marathon](https://mesosphere.github.io/marathon/).

It reads a set of standard JSON Marathon [group](https://mesosphere.github.io/marathon/docs/application-groups.html) definitions and does 3 things using the Marathon HTTP API:
 1. [GET](https://mesosphere.github.io/marathon/docs/rest-api.html#get-v2-apps)s all running apps in Marathon.
 2. [DELETE](https://mesosphere.github.io/marathon/docs/rest-api.html#delete-v2-apps-appid)s apps running in Marathon which aren't in the group definitions.
 3. [PUT](https://mesosphere.github.io/marathon/docs/rest-api.html#put-v2-groups-groupid)s each group definition, which causes Marathon to create or update any apps as is necessary.

This tool is written in Python using [Twisted](https://twistedmatrix.com/trac/).

## Running
After installing, `marathon-sync` may be launched via a simple CLI:
```
$ marathon-sync --help
Usage: marathon-sync [options]
Options:
  -m, --marathon=  The address for the Marathon HTTP API endpoint. [default:
                   http://localhost:8080]
  -c, --config=    The path to a config file containing a list of paths to
                   Marathon JSON group definitions.
      --version    Display Twisted version and exit.
      --help       Display this help and exit.
```

A config file could look something like this:
```
/path/to/my/groups/group1.json
/path/to/my/groups/group2.json
```

The Marathon group definitions are the same as what you would `curl` to the HTTP API:
```json
{
  "id": "group1",
  "apps": [
    {
      "id": "app1",
      "cmd": "python2 -c 'print(\"hello world\")'",
      "cpus": 0.1,
      "mem": 128,
      "instances": 2,
      "container": {
        "type": "DOCKER",
        "docker": {
          "image": "python:2.7"
        }
      }
    }
  ]
}
```
