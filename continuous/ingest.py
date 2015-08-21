#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This includes general utils for the continual ingest process.

import argparse
import bz2
import calendar
import glob
import HTMLParser
import json
import math
import os
import pprint
import pymongo
import re
import sys
import time
import xml.sax.saxutils
from bson.objectid import ObjectId

import metric


TwitterMentionPattern = re.compile('@[a-zA-Z0-9_]{1,15}')
InstagramMentionPattern = re.compile(
    '@[a-zA-Z0-9_][a-zA-Z0-9_.]{0,28}[a-zA-Z0-9_]?')

HTMLDecoder = HTMLParser.HTMLParser()
# Used for doing timing tests
Timers = {'lastreport': time.time()}


# -------- General Functions --------

def castObjectId(id):
    """
    Make sure an obejct is an ObjectId or None.

    :param id: the object to check.  This may be a string, ObjectId, or a
               dictionary with an _id field.
    :returns: an ObjectId or None.
    """
    if isinstance(id, dict):
        id = id['_id']
    if id is None or type(id) is ObjectId:
        return id
    return ObjectId(id)


def calculateMetrics(state, entities=None):
    """
    Calculate metrics for dirty entities.

    :param state: the state dictionary with the config values.
    :param entities: a list of entities to calculate the metrics for.  If None,
                     calculate the metrics for all entities.
    """
    metricDict = state['config'].get('metrics', {})
    if state['args']['metric']:
        metricDict = dict.fromkeys(state['args']['metric'])
    for met in metricDict:
        metric.loadMetric(met, metricDict[met])
    if entities is not None:
        entities = [castObjectId(entity) for entity in entities]
    metColl = getDb('metrics', state)
    entityColl = getDb('entity', state)
    linkColl = getDb('link', state)
    latestEntity = entityColl.find(timeout=False).sort([
        ('date_updated', pymongo.DESCENDING)]).limit(-1).next()
    if not latestEntity:
        # If there are no entities, we have nothing to do
        return
    latestEntity = latestEntity['date_updated']
    latestLink = linkColl.find(timeout=False).sort([
        ('date_updated', pymongo.DESCENDING)]).limit(-1).next()
    latestLink = 0 if not latestLink else latestLink['date_updated']
    idQuery = {} if entities is None else {'_id': {'$in': entities}}
    cursor = entityColl.find(idQuery, timeout=False).sort(
        [('_id', pymongo.ASCENDING)])
    count = numCalc = 0
    starttime = lastreport = time.time()
    for entity in cursor:
        for met in metric.LoadedMetrics:
            metClass = metric.LoadedMetrics[met]
            date = entity['date_updated']
            if metClass.onEntities or not metClass.onEntitiesOnlyNew:
                date = max(date, latestEntity)
            if metClass.onLinks or not metClass.onLinksOnlyNew:
                date = max(date, latestLink)
            oldMetric = metColl.find_one({
                'entity': castObjectId(entity),
                'metric': met
            }, timeout=False)
            # Already up to date
            if oldMetric and oldMetric['date_updated'] >= date:
                continue
            calculateOneMetric(entityColl, linkColl, metColl, metClass, entity,
                               oldMetric, state)
            numCalc += 1
        count += 1
        if state['args']['verbose'] >= 1:
            curtime = time.time()
            if curtime - lastreport > 10.0 / state['args']['verbose']:
                print '%d %d %d %5.3f' % (count, numCalc, cursor.count(),
                                          curtime - starttime)
                lastreport = curtime


def calculateOneMetric(entityColl, linkColl, metColl, metClass, entity,
                       metricDoc, state):
    """
    Calculate the value of a single metric for a single entity.

    :param entityColl: the database entity collection.
    :param linkColl: the database link collection.
    :param metColl: the database metrics collection.
    :param metClass: the instance of the metrics class used for computation.
    :param entity: the entity for which the metric is being computed.
    :param metricDoc: if the metric was previously computed, that previous
                      record.  May be None to force a completely fresh
                      computation.
    :param state: the state dictionary with the config values.
    """
    entityId = castObjectId(entity)
    if metricDoc is None:
        metricDoc = {
            'metric': metClass.name,
            'entity': entityId,
            'date_updated': 0
        }
    work = metricDoc.get('work', {})
    kwargs = {
        'work': work,
        'entityColl': entityColl,
        'linkColl': linkColl,
        'old': metricDoc,
        'state': state,
    }
    # The time has to be before we do the computation, as data could be added
    # during the comptation.
    metricDoc['date_updated'] = time.time()
    refresh = (metClass.saveWork and work == {})
    if metClass.onEntities:
        query = ({} if not metClass.onEntitiesOnlyNew or refresh else
                 {'date_updated': {'$gte': metricDoc['date_updated']}})
        for gb in entityColl.find(query, timeout=False):
            if castObjectId(gb) != entityId:
                metClass.calcEntity(entity, gb, **kwargs)
    if metClass.onLinks:
        query = ({} if not metClass.onLinksOnlyNew or refresh else
                 {'date_updated': {'$gte': metricDoc['date_updated']}})
        query['ga'] = entityId
        for link in linkColl.find(query, timeout=False):
            gb = entityColl.find_one(castObjectId(link['gb']), timeout=False)
            metClass.calcLink(entity, gb, link, **kwargs)
    value = metClass.calc(entity, **kwargs)
    if metClass.saveWork:
        metricDoc['work'] = work
    metricDoc['value'] = value
    metColl.save(metricDoc)


def convertInstagramESToMsg(inst, subset='unknown'):
    """
    Convert an instragam Elasticsearch record to our message format.  This
    normalizes the format so that other routines can handle the data
    generically.

    :param inst: the instagram record.
    :param subset: a subset name to attach to the record.  This is probably the
                   Elasticsearch _type.
    :returns: a message record or None for failed.
    """
    msg = {
        'service':       'instagram',
        'subset':        subset,
        'user_name':     inst.get('user', {}).get('username', None),
        'user_fullname': inst.get('user', {}).get('full_name', None),
        'user_id':       inst.get('user', {}).get('id', None),
        'msg_date':      float(inst['created_time']),
        'msg_id':        inst['link'].strip('/').rsplit('/', 1)[-1],
        'url':           inst['link'],
    }
    if msg['user_fullname'] == '':
        msg['user_fullname'] = None
    if msg['user_name'] == '':
        msg['user_name'] = None
    if msg['user_name']:
        msg['user_name'] = msg['user_name'].lower()
    if ('location' in inst and
            inst['location'].get('latitude', None) is not None):
        msg['latitude'] = inst['location']['latitude']
        msg['longitude'] = inst['location']['longitude']
    if inst.get('caption', None):
        msg['msg'] = inst['caption']['text']
        if '@' in msg['msg']:
            msg['mentions'] = set(mention[1:].lower() for mention in
                                  InstagramMentionPattern.findall(msg['msg']))
    if inst.get('comments', None) and inst['comments'].get('data', None):
        msg['comments'] = {}
        for comment in inst['comments']['data']:
            if 'from' in comment and 'id' in comment['from']:
                record = comment['from']
                msg['comments'][record['id']] = {
                    'user_name': (record['username']
                                  if 'username' in record else None),
                    'user_fullname': record.get('full_name', None),
                }
    if inst.get('likes', None) and inst['likes'].get('data', None):
        msg['likes'] = {}
        for record in inst['likes']['data']:
            if 'id' in record:
                msg['likes'][record['id']] = {
                    'user_name': (record['username']
                                  if 'username' in record else None),
                    'user_fullname': record.get('full_name', None),
                }
    return msg


def convertTwitterGNIPToMsg(gnip):
    """
    Convert a Twitter GNIP record to our message format.  This normalizes the
    format so that other routines can handle the data generically.

    :param gnip: the twitter gnip record.
    :returns: a message record or None for failed.
    """
    if 'postedTime' not in gnip:
        return None
    msg = {
        'service':       'twitter',
        'subset':        'unknown',
        'user_name':     gnip['actor'].get('preferredUsername', None),
        'user_fullname': gnip['actor'].get('displayName', None),
        'user_id':       gnip['actor']['id'].split(':')[-1],
        'msg_date':      int(calendar.timegm(time.strptime(
                             gnip['postedTime'], "%Y-%m-%dT%H:%M:%S.000Z"))),
        'msg_id':        gnip['object']['id'].split(':')[-1],
        'msg':           xml.sax.saxutils.unescape(gnip['body']),
    }
    if msg['user_name']:
        msg['user_name'] = msg['user_name'].lower()
    msg['url'] = 'http://twitter.com/%s/statuses/%s' % (
        msg['user_id'], msg['msg_id'])
    if ('geo' in gnip and gnip['geo'] and 'coordinates' in gnip['geo'] and
            len(gnip['geo']['coordinates']) >= 2):
        # gnip using latitude, longitude for geo (but twitter used long, lat
        # for coordinates)
        msg['latitude'] = gnip['geo']['coordinates'][0]
        msg['longitude'] = gnip['geo']['coordinates'][1]
    if ('twitter_entities' in gnip and 'media' in gnip['twitter_entities'] and
            len(gnip['twitter_entities']['media']) > 0 and
            'media_url_https' in gnip['twitter_entities']['media'][0]):
        msg['image_url'] = gnip['twitter_entities']['media'][0][
            'media_url_https']
    if ('instagram' in gnip['generator'].get('link', '') and 'gnip' in gnip and
            'urls' in gnip['gnip'] and len(gnip['gnip']['urls']) and
            'expanded_url' in gnip['gnip']['urls'][0] and
            'instagram.com/p/' in gnip['gnip']['urls'][0]['expanded_url']):
        msg['source'] = {
            'instagram': gnip['gnip']['urls'][0]['expanded_url'].rstrip(
                '/').rsplit('/')[-1]
        }
    if ('twitter_entities' in gnip and
            'user_metions' in gnip['twitter_entities']):
        msg['mentions'] = {}
        for mention in gnip['twitter_entities']['user_mentions']:
            if mention.get('id_str', None):
                msg['mentions'][mention['id_str']] = {
                    'user_name': mention.get('screen_name', None),
                    'user_fullname': mention.get('name', None),
                }
    if ('inReplyTo' in gnip and 'link' in gnip['inReplyTo'] and
            '/statuses/' in gnip['inReplyTo']['link']):
        msg['replies'] = [gnip['inReplyTo']['link'].split(
            '/statuses/')[0].rsplit('/', 1)[-1]]
    return msg


def convertTwitterJSONToMsg(tw):
    """
    Convert a Twitter firehose JSON record to our message format.  This
    normalizes the format so that other routines can handle the data
    generically.

    :param tw: the twitter record.
    :returns: a message record or None for failed.
    """
    msg = {
        'service':       'twitter',
        'subset':        'unknown',
        'user_name':     tw['user']['screen_name'].lower(),
        'user_fullname': tw['user']['name'],
        'user_id':       tw['user']['id_str'],
        'msg_date':      int(calendar.timegm(time.strptime(
                         tw['created_at'][4:], "%b %d %H:%M:%S +0000 %Y"))),
        'msg_id':        tw['id_str'],
        'msg':           HTMLDecoder.unescape(tw['text']),
    }
    msg['url'] = 'http://twitter.com/%s/statuses/%s' % (
        msg['user_id'], msg['msg_id'])
    if ('coordinates' in tw and 'coordinates' in tw['coordinates'] and
            len(tw['coordinates']['coordinates']) >= 2):
        msg['latitude'] = tw['coordinates']['coordinates'][1]
        msg['longitude'] = tw['coordinates']['coordinates'][0]
    if ('entities' in tw and 'media' in tw['entities'] and
            len(tw['entities']['media']) > 0 and
            'media_url_https' in tw['entities']['media'][0]):
        msg['image_url'] = tw['entities']['media'][0]['media_url_https']
    if ('Instagram' in tw.get('source', '') and 'entities' in tw and
            'urls' in tw['entities'] and len(tw['entities']['urls']) > 0 and
            'expanded_url' in tw['entities']['urls'][0] and
            'instagram.com' in tw['entities']['urls'][0]['expanded_url']):
        msg['source'] = {
            'instagram': tw['entities']['urls'][0]['expanded_url'].rstrip(
                '/').rsplit('/')[-1]
        }
    if ('entities' in tw and 'user_mentions' in tw['entities'] and
            len(tw['entities']['user_mentions']) > 0):
        msg['mentions'] = {}
        for mention in tw['entities']['user_mentions']:
            if mention.get('id_str', None):
                msg['mentions'][mention['id_str']] = {
                    'user_name': mention.get('screen_name', None),
                    'user_fullname': mention.get('name', None),
                }
    if tw.get('in_reply_to_user_id_str', None) is not None:
        msg['replies'] = {
            tw['in_reply_to_user_id_str']: {
                'user_name': tw.get('in_reply_to_screen_name', None),
            }
        }
    return msg


def getDb(dbName, state):
    """
    Check if a DB has been connected to.  If not, connect to it and ensure that
    the appropriate indices are present.

    :param dbName: the internal key name of the database.
    :param state: the state dictionary with the config values and a place to
                  store the result.
    :returns: the collection.
    """
    coll = state.get('db', {}).get(dbName, {}).get('coll', None)
    if coll:
        return coll
    if 'db' not in state:
        state['db'] = {}
    state['db'][dbName] = getDbConnection(**state['config']['db'][dbName])
    coll = state['db'][dbName]['coll']
    indices = {
        'entity': [
            [('user_id', pymongo.ASCENDING)],
            [('name', pymongo.ASCENDING)],
            [('msgs.msg_id', pymongo.ASCENDING)],
            [('date_updated', pymongo.ASCENDING)],
        ],
        'link': [
            [('ga', pymongo.ASCENDING)],
            [('gb', pymongo.ASCENDING)],
            [('date_updated', pymongo.ASCENDING)],
        ],
        'metrics': [
            [('entity', pymongo.ASCENDING)],
        ],
    }
    for index in indices.get(dbName, []):
        coll.create_index(index)
    return coll


def getDbConnection(dbUri, **kwargs):
    """
    Get a connection to a mongo DB.  The adds a connection timeout.

    :param dbUri: the uri to connect to.  Usually something like
                  mongodb://(host):27017/(db)
    :param database: if specified, connect to thsi database.  Otherwise,
                     use the default database.
    :param collection: the default collection to connect to.
    :returns: a dictionary with 'connection', 'database', and 'coll'.
    """
    clientOptions = {
        'connectTimeoutMS': 15000,
    }
    result = {
        'connection': pymongo.MongoClient(dbUri, **clientOptions)
    }
    if kwargs.get('database', None):
        result['database'] = result['connection'].get_database(
            kwargs['database'])
    else:
        result['database'] = result['connection'].get_default_database()
    if 'collection' in kwargs:
        result['coll'] = result['database'][kwargs['collection']]
    return result


def getEntityByName(state, entity):
    """
    Given some known information which can include _id (our id), service,
    user_id, name, and fullname, ensure that the specified entity is in the
    database and the associated ObjectId of the entity or None.

    :param state: includes the database connection.
    :param entity: a dictionary of _id, service, user_id, name, and fullname.
                   if _id is unspecified, service is required and at least one
                   of user_id or name.  If the entity doesn't exist, a
                   neighbors key may be present to populate the new entity,
                   otherwise this key is ignored.
    :returns: an entity document or None.
    :returns: updated: True if the document was changed in any way.  'new' if
              the entity was added.
    """
    entityColl = getDb('entity', state)
    if entity.get('_id', None):
        id = castObjectId(entity['_id'])
        return entityColl.find_one({'_id': id}, timeout=False), False
    spec = {'service': entity['service']}
    specUserId = {'service': entity['service']}
    specName = {'service': entity['service']}
    for key in ['name', 'fullname']:
        if entity.get(key, None) is not None and entity[key].strip() != '':
            spec[key] = entity[key]
        else:
            entity[key] = None
    hasUserId = entity.get('user_id', None) is not None
    if hasUserId:
        spec['user_id'] = specUserId['user_id'] = entity['user_id']
    if entity['name'] is not None:
        specName['name'] = entity['name']
    doc = entityColl.find_one(spec, timeout=False)
    if doc:
        # We have an entity that matches all of our information
        return doc, False
    doc = entityColl.find_one(specUserId if hasUserId else specName,
                              timeout=False)
    if not doc and hasUserId and entity['name'] is not None:
        doc = entityColl.find_one(specName, timeout=False)
    curtime = time.time()
    if doc:
        # We have this user id, but not all of its aliases.
        if (entity['name'] is not None and hasUserId and
                entity['name'] not in doc['name']):
            knownName = entityColl.find_one(specName, timeout=False)
            if knownName:
                # Merge this with the main doc
                mergeEntities(state, doc, knownName)
        doc['date_updated'] = curtime
        updated = True
    else:
        # We've never seen this entity, so add it.
        doc = {
            'service': entity['service'],
            'name': [],
            'fullname': [],
            'date_added': curtime,
            'date_updated': curtime,
            'msgs': [],
            'neighbors': entity.get('neighbors', []),
        }
        updated = 'new'
    if hasUserId:
        doc['user_id'] = entity['user_id']
    # Update the names and full names.
    for key in [key for key in ['name', 'fullname']
                if entity.get(key, None) is not None]:
        if entity[key] not in doc[key]:
            doc[key].append(entity[key])
    doc['_id'] = entityColl.save(doc)
    return doc, updated


def ingestMessage(state, msg):
    """
    Check if we have already ingested a message.  If not ingest it.  This
    checks if the (service, user_id) is present in our database.  If not, we
    add it, possibly by converting (service, user_name) or
    (service, user_fullname).  Once the user is present, we check if this
    msg_id is listed in their known messages.  If it is, we are done.  If not,
    add it to the list and ensure that all referenced users are present, too.
    Update appropriate graph edges for referenced users.

    :param state: includes the database connection.
    :param msg: our standard message format.
    :returns: True if ingested, False if already present, None if we cannot
              ingest this sort of record.
    """
    if not msg.get('service', None) or not msg.get('user_id', None):
        pprint.pprint(msg)
        sys.exit(0)
        return None
    curtime = time.time()
    entityColl = getDb('entity', state)
    # Assume if we have processed this message, then we have everything we care
    # about in our database.  This might not be true -- a message could get
    # reposted with new information.
    if entityColl.find_one({'msgs': {'$elemMatch': {
            'service': msg['service'], 'msg_id': msg['msg_id'],
            'subset': msg['subset'],
            }}}, {'_id': True}, limit=1, timeout=False):
        return False
    entity, changed = getEntityByName(state, {
        'service': msg['service'],
        'user_id': msg['user_id'],
        'name': msg.get('user_name', None),
        'fullname': msg.get('user_fullname', None),
    })

    found = False
    for knownMsg in entity['msgs']:
        if (knownMsg['service'] == msg['service'] and
                knownMsg['msg_id'] == msg['msg_id']):
            if msg['subset'] not in knownMsg['subset']:
                knownMsg['subset'].append(msg['subset'])
                entity['date_updated'] = curtime
                entityColl.save(entity)
            found = True
            break
    if found and not changed:
        return False
    if not found:
        newmsg = {
            'service': msg['service'],
            'subset': [msg['subset']],
            'msg_id': msg['msg_id'],
            'latitude': msg.get('latitude', None),
            'longitude': msg.get('longitude', None),
            'date': msg['msg_date']
        }
        for key in ('latitude', 'longitude', 'source'):
            if msg.get(key, None) is not None:
                newmsg[key] = msg[key]
        entity['msgs'].append(newmsg)
        entity['date_updated'] = curtime
        # update neighbors and edges
        ingestMessageEdges(state, entity, msg)
        entityColl.save(entity)
    # Mark descendants as dirty (for when we merge nodes)
    # ##DWM::
    return True


def ingestMessageEdges(state, entity, msg):
    """
    Update all of the edges associated with a message.  Add any new neighbors
    to the entity's neighbor list.

    :param state: includes the database connection.
    :param entity: the entity document.  Changed.
    :param msg: our standard message format.
    """
    entityId = castObjectId(entity)
    entityColl = getDb('entity', state)
    linkColl = getDb('link', state)
    for (linktype, linkdir) in [('mentions', 'out'), ('likes', 'in'),
                                ('comments', 'in'), ('replies', 'out')]:
        if linktype not in msg:
            continue
        links = msg[linktype]
        if isinstance(links, dict):
            links = [{
                'service': entity['service'],
                'user_id': key,
                'name': (links[key]['user_name'].lower()
                         if links[key].get('user_name', None) is not None else
                         None),
                'fullname': links[key].get('user_fullname', None),
            } for key in links if key != entity.get('user_id', None)]
        else:
            links = [{
                'service': entity['service'],
                'name': key
            } for key in links]
        for link in links:
            link['neighbors'] = [entityId]
            linkEntity, linkChanged = getEntityByName(state, link)
            linkId = castObjectId(linkEntity)
            isNew = linkChanged == 'new'
            # Don't link to ourselves
            if linkId == entityId:
                continue
            if linkId not in entity['neighbors']:
                entity['neighbors'].append(linkId)
            if not isNew:
                # The linked item is now a neighbor
                updateResult = entityColl.update({
                    '_id': linkId,
                    'neighbors': {'$ne': entityId},
                }, {
                    '$set': {'date_updated': time.time()},
                    '$addToSet': {'neighbors': entityId},
                })
                # If we added this link as a neighbor, then we know the edges
                # are new edges and not increased weights to existing edges.
                if updateResult['nModified']:
                    isNew = True
            # We are currently bidirectional on everything
            addLink(linkColl, entityId, linkId, linktype, isNew=isNew,
                    bidir=True)


def addLink(linkColl, ga, gb, linktype=None, weight=1, isNew=False,
            bidir=False):
    """
    Add a link or increase its weight.

    :param linkColl: mongo collection for links.
    :param ga: ga _id of the link.
    :param gb: gb _id of the link.
    :param linktype: named type of the link.
    :param weight: weight to add to the link.  If the link doesn't exist, this
                   will be the entire weight.
    :param isNew: if True, the link doesn't exist yet.  If False, the link may
                  or may not already exist.
    :param bidir: True to add a bidirectional link.  False to only add a single
                  direction.
    """
    curtime = time.time()
    if isNew:
        docs = [{
            'ga': ga, 'gb': gb, 'linktype': linktype,
            'date_updated': curtime, 'weight': weight
        }]
        if bidir:
            docs.append({
                'ga': gb, 'gb': ga, 'linktype': linktype,
                'date_updated': curtime, 'weight': weight
            })
        linkColl.insert(docs)
    else:
        if bidir:
            query = {'linktype': linktype, '$or': [
                {'ga': ga, 'gb': gb}, {'ga': gb, 'gb': ga}]}
        else:
            query = {'ga': ga, 'gb': gb, 'linktype': linktype}
        linkColl.update(
            query, {
                '$set': {'date_updated': curtime},
                '$inc': {'weight': weight}
            }, upsert=True, multi=True)


def loadConfig(filename=None):
    """
    Load the config file.  This will load an arbitrary json file, then ensure
    that certain minimum standards are met.

    :param filename: the name of the file to load.  None to load conf.json
                     in the script directory.
    :return: a config dictionary.
    """
    if not filename:
        filename = os.path.join(os.path.realpath(sys.path[0]), 'conf.json')
    config = json.load(open(filename))
    return config


def mergeEntities(state, mainId, secondId):
    """
    Merge two entity records by discarding the secondary record and converting
    all references to the secondary record to the main record.  All such
    records are marked as updated (dirty).

    :param state: includes the database connection.
    :param mainId: the main entity _id.
    :param secondId: the secondary entity _id.
    """
    entityColl = getDb('entity', state)
    mainId = castObjectId(mainId)
    secondId = castObjectId(secondId)
    if state['args']['verbose'] >= 2:
        print 'merge:', mainId, secondId
    main = entityColl.find_one({'_id': mainId}, timeout=False)
    second = entityColl.find_one({'_id': secondId}, timeout=False)
    main['msgs'].extend(second['msgs'])
    main['date_updated'] = time.time()
    if secondId in main['neighbors']:
        main['neighbors'].remove(secondId)
    entityColl.save(main)
    # update everyone's neighbors that include secondId to mainId
    entityColl.update(
        {'neighbors': secondId}, {'$addToSet': {'neighbors': mainId}},
        multi=True)
    entityColl.update(
        {'neighbors': secondId}, {'$pull': {'neighbors': secondId}},
        multi=True)
    # update links
    linkColl = getDb('link', state)
    for link in linkColl.find({'ga': secondId}, timeout=False):
        addLink(linkColl, mainId, link['gb'], link['linktype'], link['weight'])
    linkColl.remove({'ga': secondId})
    for link in linkColl.find({'gb': secondId}, timeout=False):
        addLink(linkColl, link['ga'], mainId, link['linktype'], link['weight'])
    linkColl.remove({'gb': secondId})
    # Don't allow self link
    linkColl.remove({'ga': mainId, 'gb': mainId})
    # Find all descendants and convert to the mainId and mark them as dirty
    # ##DWM::
    entityColl.remove({'_id': secondId})


# -------- Functions for stand-alone use --------

def checkForDuplicateNames(state):
    """
    Use a brute-force appoach to see if any service has duplicate user names.

    :param state: a state object used for passing config information, database
                  connections, and other data.
    """
    entityColl = getDb('entity', state)
    names = {}
    for entity in entityColl.find({}, timeout=False):
        service = entity['service']
        if service not in names:
            names[service] = {}
        for name in entity['name']:
            if (name in names[service] and
                    entity['_id'] != names[service][name]):
                print 'Duplicate name %s %r %r' % (name, names[service][name],
                                                   entity['_id'])
            else:
                names[service][name] = entity['_id']


def ingestInstagramFile(filename, state, region=None):
    """
    Ingest an Instagram file.  The files are expected to be in the
    elasticsearch output format with lines of json, each of which contains a
    _source key that contains the instagram data.

    :param filename: a file to ingest.  This may be compressed with gzip or
                     bzip2.
    :param state: a state object used for passing config information, database
                  connections, and other data.
    :param region: if not None, the region to use for this data.
    """
    state['filesProcessed'] = state.get('filesProcessed', 0) + 1
    linesProcessed = state.get('linesProcessed', 0)
    linesIngested = state.get('linesIngested', 0)
    fptr = openFile(filename)
    for line in fptr:
        line = line.strip().strip(',[]')
        if not len(line):
            continue
        showProgress(linesProcessed, state, filename)
        linesProcessed += 1
        try:
            inst = json.loads(line)
        except ValueError:
            continue
        msg = convertInstagramESToMsg(inst.get('_source', {}),
                                      inst.get('_type', 'unknown'))
        if not msg:
            continue
        if region is not None:
            msg['subset'] = region
        for retry in xrange(3):
            try:
                if ingestMessage(state, msg):
                    linesIngested += 1
                break
            except pymongo.errors.OperationFailure:
                if state['args']['verbose'] >= 1:
                    print 'retrying'
    state['linesProcessed'] = linesProcessed
    state['linesIngested'] = linesIngested


def ingestTwitterFile(filename, state, region=None):
    """
    Ingest a Twitter file.  The file may contain gnip or firehose json.

    :param filename: a file to ingest.  This may be compressed with gzip or
                     bzip2.
    :param state: a state object used for passing config information, database
                  connections, and other data.
    :param region: if not None, the region to use for this data.
    """
    state['filesProcessed'] = state.get('filesProcessed', 0) + 1
    linesProcessed = state.get('linesProcessed', 0)
    linesIngested = state.get('linesIngested', 0)
    fptr = openFile(filename)
    for line in fptr:
        line = line.strip().strip(',[]')
        if not len(line):
            continue
        showProgress(linesProcessed, state, filename)
        linesProcessed += 1
        try:
            twit = json.loads(line)
        except ValueError:
            continue
        if 'gnip' in twit:
            msg = convertTwitterGNIPToMsg(twit)
        else:
            msg = convertTwitterJSONToMsg(twit)
        if not msg:
            continue
        msg['subset'] = region if region is not None else msg.get(
            'subset', 'unknown')
        for retry in xrange(3):
            try:
                if ingestMessage(state, msg):
                    linesIngested += 1
                break
            except pymongo.errors.OperationFailure:
                if state['args']['verbose'] >= 1:
                    print 'retrying'
    state['linesProcessed'] = linesProcessed
    state['linesIngested'] = linesIngested


def logarithmicBin(items):
    """
    Convert a dictionary of the form (key): (sum) where the keys are all non-
    negative integers into a binned dictionary with logarithmic-based bins.

    :param items: the dictionary of initial bins.
    :return: the binned dictionary.
    """
    bins = {}
    for val in items:
        if val <= 5:
            bin = val
        else:
            logval = math.log10(val)
            frac = 10 ** (logval - math.floor(logval))
            for start in [10, 9, 8, 7, 6, 5, 4, 3, 2, 1.5, 1]:
                if frac >= start:
                    bin = int(10 ** math.floor(logval) * start)
                    break
        bins[bin] = bins.get(bin, 0) + items[val]
    return bins


def openFile(filename):
    """
    Check if a file is gzip or bzip2 and open it with decompression.  If not,
    just open it.

    :param filename: name of the file to open.
    :returns: a stream pointer.
    """
    fileHeaders = {
        '\x1f\x8b\x08': 'gunzip < %s',  # gzip.open could be used
        '\x42\x5a\x68': bz2.BZ2File,
    }
    filename = os.path.realpath(os.path.expanduser(filename))
    start = open(filename, 'rb').read(max(len(key) for key in fileHeaders))
    for key in fileHeaders:
        if start[:len(key)] == key:
            if isinstance(fileHeaders[key], basestring):
                return os.popen(fileHeaders[key] % filename)
            return fileHeaders[key](filename)
    # Reopen it, since we may not be able to rewind it
    return open(filename, 'rb')


def showEntityStatistics(entityColl):
    """
    Report on distributions and statistics of the entity collection.

    :param entityColl: the entity collection.
    """
    counts = entityColl.aggregate([
        {'$project': {'count': {'$size': '$msgs'}}},
        {'$group': {'_id': '$count', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ])
    msgs = {count['_id']: count['count'] for count in counts['result']}
    msgCount = sum([key * msgs[key] for key in msgs])
    msgs = logarithmicBin(msgs)
    print 'Message distribution:'
    pprint.pprint(msgs)
    counts = entityColl.aggregate([
        {'$project': {'count': {'$size': '$neighbors'}}},
        {'$group': {'_id': '$count', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ])
    neighbors = {count['_id']: count['count'] for count in counts['result']}
    neighbors = logarithmicBin(neighbors)
    print 'Neighbor distribution:'
    pprint.pprint(neighbors)
    senders = sum(msgs.values()) - msgs.get(0, 0)
    total = entityColl.count()
    if total and msgCount and senders:
        print '%d senders (%4.2f%%), %5.3f msg/sender, %5.3f entities/msg' % (
            senders, 100.0 * senders / total, float(msgCount) / senders,
            float(total) / msgCount)
        print '%d messages, %d entities' % (msgCount, total)


def showProgress(linesProcessed, state, filename):
    """
    Show progress if the verbosity is appropriate.

    :param linesProcessed: the number of lines processed.
    :param state: a state object used for passing config information, database
                  connections, and other data.
    :param filename: filename to report.
    """
    if state['args']['verbose'] < 1 or linesProcessed % 1000:
        return
    if 'starttime' not in state:
        state['starttime'] = time.time()
    if (state['args']['verbose'] >= 2 and
            filename != state.get('lastFilename', None)):
        print filename
        state['lastFilename'] = filename
    entityColl = getDb('entity', state)
    linkColl = getDb('link', state)
    state['lastcounts'] = {
        'entity': entityColl.count(), 'link': linkColl.count()
    }
    print('%d %d %d %5.3f' % (
        linesProcessed, state['lastcounts']['entity'],
        state['lastcounts']['link'], time.time() - state['starttime']))
    if state['args']['verbose'] >= 2 and not linesProcessed % 100000:
        if state.get('laststatcounts', {}) != state['lastcounts']:
            showEntityStatistics(entityColl)
        state['laststatcounts'] = state['lastcounts']


def timer(name, action='toggle', report='auto', data=None):
    """
    Track timing of functions to help optimize code.

    :param name: name of the timer.  Required.
    :param action: 'start': start the timer, 'stop': stop the timer, 'toggle':
                   switch between start and stop, anything else doesn't affect
                   the timer (can be used for reporting).
    :param report: 'auto' to report all timer states no more than once every 10
                   seconds, otherwise 'all' to report all timer states, True to
                   report just the specified timer, or anything else to not
                   report time.
    :param data: if present, store this as some example data for the process.
    """
    curtime = time.time()
    if name not in Timers and action in ('start', 'stop', 'toggle'):
        Timers[name] = {'count': 0, 'tally': 0, 'start': 0, 'data': None}
    if action == 'start' or (action == 'toggle' and not Timers[name]['start']):
        Timers[name]['start'] = curtime
    elif (action == 'stop' and Timers[name]['start']) or action == 'toggle':
        Timers[name]['count'] += 1
        Timers[name]['tally'] += curtime - Timers[name]['start']
        Timers[name]['start'] = 0
    if name in Timers and data is not None:
        Timers[name]['data'] = data
    if report == 'auto':
        if curtime - Timers['lastreport'] > 10:
            report = 'all'
    if report == 'all' or report is True:
        keys = sorted(Timers.keys())
        for key in keys:
            if (key != 'lastreport' and (report == 'all' or key == name) and
                    Timers[key]['count']):
                data = ''
                if Timers[key]['data'] is not None:
                    data = ' ' + str(Timers[key]['data'])
                print ('%s %d %5.3f %8.6f%s' % (
                    key, Timers[key]['count'], Timers[key]['tally'],
                    Timers[key]['tally'] / Timers[key]['count'], data))
        if report == 'all':
            Timers['lastreport'] = curtime


class AppendRegionAction(argparse.Action):
    """Append an item to a list with the current value of region."""
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(AppendRegionAction, self).__init__(
            option_strings=option_strings, dest=dest, nargs=nargs, const=const,
            default=default, type=type, choices=choices, required=required,
            help=help, metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        items = argparse._copy.copy(argparse._ensure_value(
            namespace, self.dest, []))
        items.append((values, getattr(namespace, 'region', None)))
        setattr(namespace, self.dest, items)


# -------- stand-alone program --------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load messages into the entity graph database')
    parser.add_argument(
        '--calculate', '--calc', '-c', help='Calculate metrics.',
        action='store_true', dest='calc')
    parser.add_argument(
        '--config', '--conf', help='The path to the config file')
    parser.add_argument(
        '--checknames', help='Check for duplicate names.', action='store_true')
    parser.add_argument(
        '--instagram', '-i', '--inst',
        help='Ingest one or more files that contain Instagram messages in the '
        'elasticsearch format.  These may be compressed with gzip or bzip2, '
        'and names with wildcards are allowed.  The file is expected to '
        'contain one record per line.  Those records with _source keys are '
        'ingested.', action=AppendRegionAction, dest='inst')
    parser.add_argument(
        '--metric', '-m', help='Explicitly choose which metrics are '
        'calculated.  Multiple metrics may be specified.  Multiple processes '
        'can be run in parallel with different metrics to increase overall '
        'processing speed.', action='append')
    parser.add_argument(
        '--region', '-r', help='Subsequent input files will use this as '
        'their region or subset.  Set to blank to revert to parsing regions '
        'if possible.')
    parser.add_argument(
        '--twitter', '-t', '--twit',
        help='Ingest one or more files that contain Twitter messages in '
        'either gnip or firehose json format.  These may be compressed with '
        'gzip or bzip2, and names with wildcards are allowed.',
        action=AppendRegionAction, dest='twit')
    parser.add_argument('--verbose', '-v', help='Increase verbosity',
                        action='count')
    args = vars(parser.parse_args())
    state = {
        'args': args,
        'config': loadConfig(args['config'])
    }
    if args.get('checknames', False):
        checkForDuplicateNames(state)
    if args.get('inst', None):
        for filespec, region in args['inst']:
            for filename in sorted(glob.iglob(os.path.expanduser(filespec))):
                ingestInstagramFile(filename, state, region)
    if args.get('twit', None):
        for filespec, region in args['twit']:
            for filename in sorted(glob.iglob(os.path.expanduser(filespec))):
                ingestTwitterFile(filename, state, region)
    if args.get('calc', False):
        calculateMetrics(state)
    if state['args']['verbose'] >= 1:
        pprint.pprint(state)
