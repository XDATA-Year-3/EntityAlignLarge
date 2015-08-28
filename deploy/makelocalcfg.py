#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

rootPath = os.environ['KWDEMO_KEY']

cfg = """
{
    "host"          : "elasticsearch",
    "graphsDatabase": "test1!entity",
    "entities"      : "%HOSTIP%:9200!test1!entity",
    "metrics"       : "%HOSTIP%:9200!test1!metrics",
    "rankings"      : "%HOSTIP%:9200!test1!rankings",
    "istRankingsOld": "https://memex:3vYAZ8bSztbxmznvhD4C@els.istresearch.com:49200/syrian_visa",
    "istRankings"   : "http://%HOSTIP%:9200/syrian_visa",
    "loggingUrl"    : "http://10.253.253.253",
    "toolVersion"   : "1.0.0",
    "sendLogs"      : false
}
"""

hostip = os.popen("netstat -nr | grep '^0\.0\.0\.0' | awk '{print $2}'").read()
cfg = cfg.replace('%HOSTIP%', hostip.strip()).strip()
cfg = cfg.replace('%ROOTPATH%', rootPath)

print cfg
