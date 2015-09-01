import json
import os

# Used for caching the config values
DefaultConfigObj = None


def getDefaultConfig():
    """
    Fetch the defaults.json file.

    :returns: the parsed file.
    """
    global DefaultConfigObj

    if not DefaultConfigObj:
        scriptPath = os.path.dirname(os.path.realpath(__file__))
        DefaultConfigObj = json.loads(open(os.path.join(
            scriptPath, '..', 'defaults.json')).read())
    return DefaultConfigObj
