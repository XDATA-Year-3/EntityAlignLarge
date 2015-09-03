import json
import os

# Used for caching the config values
CachedConfig = {}


def getDefaultConfig():
    """
    Fetch the defaults.json file.

    :returns: the parsed file.
    """
    return getNamedConfig('defaults.json')


def getNamedConfig(name):
    """
    Fetch a json config file, caching it if possible.

    :returns: the parsed file.
    """
    if name not in CachedConfig:
        scriptPath = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(scriptPath, '..', name)
        if os.path.exists(filename):
            CachedConfig[name] = json.loads(open(filename).read())
        else:
            CachedConfig[name] = {}
    return CachedConfig[name]
