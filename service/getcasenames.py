import json
import tangelo

tangelo.paths(".")
import elasticsearchutils


def run(host, database, graphname, case):
    cases = elasticsearchutils.getCases(graphname)
    caseData = cases.get(case)
    if caseData:
        order = [(guid not in caseData.get('pa', {}),
                  guid not in caseData.get('used', {}),
                  caseData['guids'][guid],
                  guid) for guid in caseData['guids']]
        order.sort()
        caseData['order'] = [entry[-1] for entry in order]
    response = {'result': caseData}

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
