import elasticsearch
import ingest
import pprint
import sys
import time
import urllib3
import xml.etree.ElementTree


def convertXMLToObject(node):
    """
    Convert an ElementTree node to a more pythonic object.

    :param node: the element to convert.
    :returns: a python object.
    """
    if hasattr(node, 'getroot'):
        node = node.getroot()
    value = None
    children = list(node)
    if children:
        value = {}
        for child in children:
            childval = convertXMLToObject(child)
            if childval is not None:
                if child.tag not in value:
                    value[child.tag] = []
                value[child.tag].append(childval)
        for tag in value:
            if len(value[tag]) == 1 and not isinstance(value[tag][0], dict):
                value[tag] = value[tag][0]
        if not len(value):
            value = None
    else:
        if node.text:
            value = node.text.strip()
        elif hasattr(node, 'attribute'):
            value = node.attribute
        if value is not None and not len(value):
            value = None
    return value


dbref = None


def getDb():
    """
    Get a connection to Elasticsearch.

    :returns: a database connection.
    :returns: the default index we want to use.
    """
    global dbref
    index = 'test1'
    if dbref is None:
        dbref = elasticsearch.Elasticsearch(hosts=[{
            'host': '127.0.0.1',
            'port': 9200,
            'url_prefix': '/',
            'timeout': urllib3.Timeout(read=150, connect=10)
        }])
    return dbref, index


def printAndStoreMetric(state, entity, metClass, metric):
    """
    Print and store the metrics we computed for an entity.

    :param state: the state dictionary.
    :param entity: the current entity.
    :param metClass: the metric class.
    :param metric: the computed metric value.
    """
    db, index = getDb()
    rankings = []
    for sub in ['name', 'fullname']:
        if sub not in metric['value']:
            continue
        metricName = metClass.name + '-' + sub
        kept = 0
        for met in metric['value'][sub]:
            if met[0] < 0.85 and kept >= 3:
                continue
            gb = entityColl.find_one(met[1])
            namelist = gb['name'][:]
            namelist.extend(gb['fullname'])
            ranking = {
                'entityId': [entity['id']],
                'documentId': gb['user_id'],
                'documentSource': 'twitter',
                'documentLink': 'http://twitter.com/intent/user?'
                                'user_id=' + gb['user_id'],
                'name': metricName,
                'entityNames': namelist,
                'score': met[0],
                'date_updated': time.time(),
                'info': {
                    'name': gb['name'],
                    'fullname': gb['fullname']
                }
            }
            # Not really necessary, but it lets me be lazy about deleting old
            # results
            id = entity['id'] + '-' + ranking['documentId']
            try:
                old = db.get(index=index, doc_type='ranking', id=id)
            except elasticsearch.NotFoundError:
                old = None
            if old is None or old['_source'] != ranking:
                db.index(index=index, doc_type='ranking', body=ranking, id=id)
                state['rankings'] = state.get('rankings', 0) + 1
            kept += 1
            rankings.append(ranking)
    if 'fullname' in metric['value']:
        met = metric['value']['fullname'][0]
        gb = entityColl.find_one(met[1])
        logstr = '%d %6.4f %r;%r %s %r;%r' % (
            state.get('rankings', 0), met[0], ','.join(entity['name']),
            ','.join(entity['fullname']), met[1], ','.join(gb['name']),
            ','.join(gb['fullname']))
        if met[0] > 0.85:
            print logstr
        sys.stderr.write(logstr + '\n')
    # sys.stderr.write('%r\n' % entity)
    sys.stderr.write(pprint.pformat(rankings) + 'n')
    sys.stderr.flush()
    del entity['metrics']


if __name__ == '__main__':  # noqa
    reverse = False
    offset = 0
    filename = None
    help = False
    for arg in sys.argv[1:]:
        if arg.startswith('--offset='):
            offset = int(arg.split('=', 1)[1])
        elif arg == '-r':
            reverse = True
        elif arg.startswith('-') or filename:
            help = True
        else:
            filename = arg
    if help or not filename:
        print """Load xml person list and compute metrics.

Syntax: xmlmetric.py (xml file) [-r] [--offet=(offset)]

-r reverse the processing order.
--offset skips entities at the beginning of the processing order.
"""
        sys.exit(0)
    starttime = lastupdate = time.time()
    metricDict = {
        'levenshtein-name': {
            'longname': 'Levenshtein User Name',
            'description': 'User name similarity based Levenshtein distance.  '
                           'This is based on the email user name, Twitter '
                           'handle, or other service name.',
            'version': '0.1'
        },
        'levenshtein-fullname': {
            'longname': 'Levenshtein Full Name',
            'description': 'Full name similarity based Levenshtein distance.',
            'version': '0.1'
        },
    }
    state = {
        'args': {
            'metric': ['levenshtein'],
            'verbose': 2,
        },
        'config': ingest.loadConfig(None)
    }
    tree = xml.etree.ElementTree.iterparse(filename)
    for _, el in tree:
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]
    root = tree.root
    print 'parsed'
    entityColl = ingest.getDb('entity', state)
    entities = []
    persons = []
    db, index = getDb()
    for key in metricDict:
        id = key
        metricDict[key]['name'] = key
        try:
            old = db.get(index=index, doc_type='metrics', id=id)
        except elasticsearch.NotFoundError:
            old = None
        if old is None or old['_source'] != metricDict[key]:
            db.index(index=index, doc_type='metrics', body=metricDict[key],
                     id=id)
    count = updated = 0
    for personNode in root.findall('Person'):
        person = convertXMLToObject(personNode)
        persons.append(person)

        id = person['PersonGUID']
        try:
            old = db.get(index=index, doc_type='entity', id=id)
        except elasticsearch.NotFoundError:
            old = None
        if old is None or old['_source'] != person:
            db.index(index=index, doc_type='entity', body=person, id=id)
            updated += 1
        entity = {
            'id': person['PersonGUID'],
            'name': [],
            'fullname': [],
            'service': 'xml',
        }
        for ident in person.get('Identity', []):
            for name in ident.get('Name', []):
                if ('FullName' in name and
                        name['FullName'] not in entity['fullname']):
                    entity['fullname'].append(name['FullName'])
            for email in ident.get('Email', []):
                if 'Username' in email:
                    namelower = email['Username'].lower()
                    if namelower not in entity['name']:
                        entity['name'].append(namelower)
        entities.append(entity)
        count += 1
        curtime = time.time()
        if curtime - lastupdate > 10:
            print '%d %d %4.2f' % (count, updated, curtime - starttime)
            lastupdate = curtime
    root = tree = None
    if reverse:
        entities.reverse()
    if offset:
        entities = entities[offset:]
    print 'start %4.2f' % (time.time() - starttime)
    ingest.calculateMetrics(state, None, entities, printAndStoreMetric)
