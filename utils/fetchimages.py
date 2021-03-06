#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#############################################################################

import argparse
import md5
import os
import pymongo
import re
import requests
import sys
import unicodedata
import urllib


MimeExtensions = {
    'image/gif': '.gif',
    'image/jpeg': '.jpg',
    'image/png': '.png',
}
UsedMD5Sums = {}


def safe_path(value, noperiods=False):
    """
    Make sure a string is a safe file path.

    :param value: the string to escape.
    :param noperids: if true, escape periods, too.
    :returns: the escaped string
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = re.sub('[-\s]+', '-', value)
    if noperiods:
        value = value.replace('.', '-')
    return value


def fetch_image_twitter(basepath, username):
    """
    Check if we need to fetch an image from Twitter.  If so, do so.

    :param basepath: base path to store images.  Created if necessary.
    :param username: username to fetch.
    """
    if not username:
        return
    safe_name = safe_path(username, True)
    path = os.path.join(basepath, safe_name[:2])
    filename = os.path.join(path, safe_name)
    if not os.path.exists(path):
        os.makedirs(path)
    files = [file for file in os.listdir(path)
             if file.split('.')[0] == safe_name]
    if len(files):
        if os.path.getsize(os.path.join(path, files[0])):
            md5sum = md5.new(open(os.path.join(path, files[0]), 'rb').read(
                )).hexdigest()
            UsedMD5Sums[md5sum] = UsedMD5Sums.get(md5sum, 0) + 1
            # Report if more than a few users have the same image
            if UsedMD5Sums[md5sum] >= 3:
                print 'used', UsedMD5Sums[md5sum], os.path.join(path, files[0])
        return
    url = 'https://twitter.com/%s/profile_image?size=original' % (
        urllib.quote(username), )
    req = requests.get(url)
    if req.status_code in (403, 404):
        data = ''
    elif req.status_code == 200:
        data = req.content
        md5sum = md5.new(data).hexdigest()
        mime = req.headers['Content-Type']
        # If the image matches particular md5 sums, then they are twitter
        # default images and should be excluded.
        if mime.startswith('text/') or md5sum in (
                'eff522de713c9faf5306578a1a5f6f00',
                '4cc37d5daba30f3a3e9eb579987f484e',
                'd22796f1ffef64e584899475096801a0',
                'bafcc4c38220b75c6739a8f68a1c88bd',
                '0d75373e1c612ef553b64c3a9e638aae',
                '531003390ee8fa9a0cf3b7fbc36f5960',
                '6df7294d31afb0d070aa59b90a650223',
                ):
            data = ''
        else:
            UsedMD5Sums[md5sum] = UsedMD5Sums.get(md5sum, 0) + 1
            # Report if more than a few users have the same image
            if UsedMD5Sums[md5sum] >= 3:
                print 'used', UsedMD5Sums[md5sum], os.path.join(path, files[0])
            if mime not in MimeExtensions:
                print 'Unknown mime', mime, url
                sys.exit(0)
            filename += MimeExtensions[mime]
    else:
        print 'Unknown status code', req.status_code, url
        sys.exit(0)
    open(filename, 'wb').write(data)
    print filename, len(data)


def fetch_images(mongo, mongoCollection, out, **kwargs):
    """
    Get a list of user names from Mongo, then fetch images for each user if
    we don't already have them.

    :param mongo: the mongo server and database.
    :param mongoCollection: the name of the mongo collection.
    :param out: the output directory.  This is created if it does not exist.
    """
    service = None
    if mongoCollection.lower().startswith('twitter'):
        service = 'twitter'
    if not service:
        print 'No known service'
        return
    if not mongo.startswith('mongodb://'):
        mongo = 'mongodb://' + mongo
    mongoClientOptions = {'connectTimeoutMS': 15000}
    mconn = pymongo.MongoClient(mongo, **mongoClientOptions)
    mdb = mconn.get_default_database()
    mcoll = mdb[mongoCollection]
    cur = mcoll.find({'type': 'node'}, {'data.name': True, '_id': False},
                     limit=kwargs.get('limit'))
    usernames = {entry['data']['name'].strip() for entry in cur}
    func = globals()['fetch_image_' + service]
    for username in sorted(usernames):
        func(os.path.join(out, service), username)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fetch user profile images based on users in a mongo '
        'database.')
    parser.add_argument(
        '--mongo', help='The mongo database.  For example, '
        '127.0.0.1:27017/may2016_isil.',
        default='127.0.0.1:27017/may2016_isil')
    parser.add_argument(
        '--coll', '--collection', help='Mongo collection name.  For example, '
        'twitter_isil_36_nodelink.', default='twitter_isil_36_nodelink',
        dest='mongoCollection')
    parser.add_argument(
        '--limit', help='Only check this many usernames.', type=int, default=0)
    parser.add_argument(
        '--out', help='Output directory.  Within this directory a '
        'sub-directory for each service (twitter, instagram) will be '
        'created.  Within those directories, images are stored in the form '
        '(username).(extension), where a zero-length file indicates that we '
        'received a successfull response from the service but that no profile '
        'picture was available or the default is being used.',
        default='profileimages')
    parser.set_defaults(nodup=True)
    args = vars(parser.parse_args())

    fetch_images(**args)
