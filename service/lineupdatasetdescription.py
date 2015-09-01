import json
import tangelo

tangelo.paths(".")
from lineupdataset import translate


def run(displaymode, *args, **kwargs):
    # Create an empty response object.
    response = {}

    if displaymode in ('left network only', 'right network only'):
        print 'displaying', displaymode
        # return fixed result to compare two datasets
        response['primaryKey'] = 'entity'
        response['separator'] = '\t'
        response['url'] = 'service/lineupdataset'
        response['columns'] = [
            {'column': 'entity', 'type': 'string'},
            {'column': '1hop', 'type': 'number', 'domain': [0, 1]},
            {'column': '2hop', 'type': 'number', 'domain': [0, 1]},
        ]
        response['layout'] = {'primary': [
            {'column': 'entity', 'width': 130},
            {'column': '1hop', 'width': 100},
            {'column': '2hop', 'width': 100},
            {"type": "stacked", "label": "Combined", "children": [
                {'column': '1hop', 'width': 75},
                {'column': '2hop', 'width': 75}
            ]}
        ]}
    elif displaymode == 'compare networks':
        # return fixed result to compare two datasets
        print 'displaying centered'
        response['primaryKey'] = 'entity'
        response['separator'] = '\t'
        response['url'] = 'service/lineupdataset'
        response['columns'] = [
            {'column': translate['entity'], 'type': 'string'},
            {'column': translate['selfreport'], 'type': 'number',
             'domain': [0, 1]},
            {'column': 'LSGM', 'type': 'number', 'domain': [0, 1]},
            {'column': translate['freq'], 'type': 'number', 'domain': [0, 1]},
            {'column': translate['area'], 'type': 'number', 'domain': [0, 1]},
            {'column': translate['lev'], 'type': 'number', 'domain': [0, 1]},
            {'column': translate['substring'], 'type': 'number',
             'domain': [0, 1]}
        ]
        response['layout'] = {'primary': [
            {'column': translate['entity'], 'width': 100},
            {"type": "stacked", "label": "Combined", "children": [
                {'column': translate['selfreport'], 'width': 150},
                {'column': 'LSGM', 'width': 50},
                {'column': translate['freq'], 'width': 50},
                {'column': translate['area'], 'width': 50},
                {'column': translate['lev'], 'width': 50},
                {'column': translate['substring'], 'width': 50}
            ]}
        ]}
    else:
        import elasticsearchutils

        print 'document rankings'
        response['primaryKey'] = 'dochash'
        response['separator'] = '\t'
        response['url'] = 'service/lineupdataset'
        response['columns'] = col = [{
            'column': 'dochash',
            'type': 'string',
        }, {
            'column': 'doc_type',
            'label': elasticsearchutils.ColumnLabels['doc_type'],
            'type': 'string',
        }, {
            'column': 'doc_id',
            'label': elasticsearchutils.ColumnLabels['doc_id'],
            'type': 'string',
        }, {
            'column': 'desc',
            'label': elasticsearchutils.ColumnLabels['desc'],
            'type': 'string',
        }]
        laycol = []
        response['layout'] = {'primary': [
            {'column': 'doc_type', 'width': 60},
            {'column': 'doc_id', 'width': 60},
            {'column': 'desc', 'width': 140},
            {"type": "stacked", "label": "Combined", "children": laycol}
        ]}
        host, database, graphA, handle = tuple((list(args) + [None] * 4)[:4])
        metrics = elasticsearchutils.getMetricList(graphA, handle)
        for metric in sorted(metrics):
            col.append({
                'column': metric,
                'type': 'number',
                'domain': metrics[metric].get('domain', [0, 1]),
            })
            laycol.append({'column': metric, 'width': 450./len(metrics)})

    # tangelo.log(str(response))
    return json.dumps(response)
