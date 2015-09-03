/*jslint browser:true, unparam:true */
/*globals $, console, d3, log, loadDataImpl, lineup, logSetupLineUp, logOpenTwitterWindow, logOpenInstagramWindow, initializeLoggingFramework, logSelectLineUpEntry, logPublishPairings, LineUp */


var color = null;

//var graph = null;
//var svg = null;
var width = 0;
var height = 0;
//var transition_time;
//var translate = [0, 0];

var entityAlign = {};
entityAlign.force1 = null;
entityAlign.force2 = null;
entityAlign.host = null;
entityAlign.ac = null;
entityAlign.textmode = false;

var lineUpConfig = {
    svgLayout: {
        mode: 'separate'
    }
};
var lineup2;

/* All but the data element should be saved to recover the user state. */
var actionState = {data: {}};


// logging is handled largely in
function logSystemActivity(group, element, activityEnum, action, tags) {
    group = typeof group !== 'undefined' ? group : 'system_group';
    activityEnum = typeof activityEnum !== 'undefined' ? activityEnum : 'show';
    action = typeof action !== 'undefined' ? action : 'SHOW';
    tags = typeof tags !== 'undefined' ? tags : [];
    var msg = {
        activity: activityEnum,
        action: action,
        elementId:  element,
        elementType: 'OTHER',
        elementGroup: group,
        source: 'system',
        tags: tags
    };
    if (typeof log === 'function') {
        log(msg);
    }
}

entityAlign.dayColor = d3.scale.category10();
entityAlign.monthColor = d3.scale.category20();
entityAlign.dayName = d3.time.format('%a');
entityAlign.monthName = d3.time.format('%b');
entityAlign.dateformat = d3.time.format('%a %b %e, %Y (%H:%M:%S)');

// add globals for current collections to use.  Allows collection to be initialized at
// startup time from a defaults.json file.   A pointer to the global datastructures for each graph, are initialized empty as well.

entityAlign.graphsDatabase = null;
entityAlign.showMatchesEnabled = false;
entityAlign.graphA = null;
entityAlign.graphB = null;

entityAlign.graphA_dataset = null;
entityAlign.graphB_dataset = null;
entityAlign.graphAnodeNames = null;
entityAlign.graphBnodeNames = null;

// a backup copy of the files as read from the datastore is kept to send to the SGM algortihm.  The regular .graphA and .graphB entries
// are operated-on by D3, so the datastructures don't work passed back to networkX directly anymore.  So a backup is kepts and this pristine
// copy is used to initialize the SGM algorithm executed as a tangelo service.

entityAlign.SavedGraphA = null;
entityAlign.SavedGraphB = null;

// there is a global array corresponding to the current matches known between the two loaded graphs.  The matches are an array of JSON objects, each with a
// 'ga' and 'gb' attribute, whose corresponding values are integers that match the node IDs.
entityAlign.currentMatches = [];
entityAlign.pairings = [];

// how far to go out on the default rendering of a local neightborhood
entityAlign.numberHops = 2;

entityAlign.cliqueA = null;
entityAlign.cliqueB = null;

entityAlign.monthNames = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec'
];

entityAlign.dayNames = [
    'Sun',
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat'
];

// make alternating blue and tan colors gradually fading to background to add color gradient to network
// see http://en.wikipedia.org/wiki/Web_colors
entityAlign.nodeColorArray = [
    '#ff2f0e', '#1f77b4', '#cd853f', '#1e90b4', '#f5deb3', '#add8e6', '#fff8dc',
    '#b0e0e6', '#faf0e6', '#e0ffff', '#fff5e0', '#f0fff0'
];


/*
function stringifyDate(d) {
    'use strict';

    return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
}

function displayDate(d) {
    'use strict';

    return entityAlign.monthNames[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
}
*/


// This function is attached to the hover event for displayed d3 entities.  This means each rendered tweet has
// a logger installed so if a hover event occurs, a log of the user's visit to this entity is sent to the activity log

/*
function loggedVisitToEntry(d) {
    //console.log('mouseover of entry for ',d.user)
    //entityAlign.ac.logUserActivity('hover over entity: '+d.tweet, 'hover', entityAlign.ac.WF_EXPLORE);

}

function loggedDragVisitToEntry(d) {
    //console.log('mouseover of entry for ',d.user)
    //entityAlign.ac.logUserActivity('drag entity: '+d.tweet, 'hover', entityAlign.ac.WF_EXPLORE);
}
*/

function getDatasetName(label) {
    if (label === 'Twitter') {
        return entityAlign.twitter;
    } else if (label === 'Instagram') {
        return entityAlign.instagram;
    }
    return label;
}

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.
function initGraphStats(graphIndexString) {

    'use strict';
    var graphelement = (graphIndexString === 'A') ? '#graph1' : '#graph2';
    logSystemActivity('graph_' + graphIndexString + '_group', graphelement, 'inspect', 'OPEN');
    var data;
    var graphPathname, selectedDataset;

    // Get the name of the graph dataset to render
    if (graphIndexString === 'A') {
        graphPathname = $('#graph1-selector').val();
        selectedDataset = getDatasetName(graphPathname);
        // save the current dataset name for the graph
        entityAlign.graphA_dataset = selectedDataset;
    } else {
        graphPathname = d3.select('#graph2-selector').text();
        selectedDataset = getDatasetName(graphPathname);
        // save the current dataset name for the graph
        entityAlign.graphB_dataset = selectedDataset;
    }
    //var logText = 'dataset ' + graphIndexString + ' select: start=' + graphPathname;
    //logSystemActivity('Kitware entityAlign - '+logText);

    $.ajax({
        // generalized collection definition
        url: 'service/loadgraphsummary/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(selectedDataset),
        data: data,
        dataType: 'json',
        success: function (response) {

            if (response.error) {
                console.log('error: ' + response.error);
                return;
            }
            console.log('data returned:', response.result);
            if (graphIndexString === 'A') {
                d3.select('#ga-nodeCount').text(response.result.nodes.toString());
                //d3.select('#ga-linkCount').text(response.result.links.toString());
            } else {
                d3.select('#gb-nodeCount').text(response.result.nodes.toString());
                d3.select('#gb-linkCount').text(response.result.links.toString());
            }
        }

    });
}

// reset the user list on a new time range query
function resetUserList() {
    $('#ga-name').autocomplete({ source: [] });
}

/* Get the current setting of the cases control and populate the person list
 * based on it. */
function updatePersonList() {
    var casename = $('#ga-name').val();
    if ($('#person-list').attr('case') === casename) {
        return;
    }
    actionState['case'] = casename;
    $('#document-controls').css('display', 'none');
    $('#document-panel').css('display', 'none');
    $('#match-controls').css('display', 'block');
    $('#match-panel').css('display', 'block');
    //DWM:: clear person list, lineup, match data
    $('#person-list').attr('case', casename);
    var graphPathname = $('#graph1-selector').val();
    var selectedDataset = getDatasetName(graphPathname);
    $.ajax({
        url: 'service/getcasenames/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(selectedDataset) + '/' + casename,
        dataType: 'json',
        success: function (response) {
            var elem = $('#person-list select');
            elem.empty();
            var res = response.result;
            if (!res || !res.order) {
                return;
            }
            for (var i = 0; i < res.order.length; i += 1) {
                var guid = res.order[i];
                var text = res.guids[guid];
                if (text.indexOf(' - ') >= 0) {
                    text = text.substr(text.indexOf(' - ') + 3);
                }
                var opt = $('<option>').attr({
                    value: guid,
                    title: text
                }).text(text);
                if (!res.used[guid]) {
                    opt.addClass('no-documents');
                }
                elem.append(opt);
            }
        }
    });
}

// update the user list from a response
function updateUserList(namelist) {

    resetUserList();

    // Update the user filter selection box
    // .slice(0, 10)
    $('#ga-name').autocomplete({
        source: namelist,
        delay: 300,
        minLength: 0,
        select: function () {
            window.setTimeout(updatePersonList, 1);
        },
        change: updatePersonList
    });
}

// do a non-blocking call to a python service that returns all the names in the graph.  Assign this to a global variable
function loadNodeNames(graphIndexString) {
    var graphPathname, selectedDataset;

    // Get the name of the graph dataset to render
    if (graphIndexString === 'A') {
        graphPathname = $('#graph1-selector').val();
        selectedDataset = getDatasetName(graphPathname);
    } else {
        selectedDataset = d3.select('#graph2-selector').text();
    }

    selectedDataset = getDatasetName(selectedDataset);

    // non-blocking call to initialize this
    $.ajax({
        url: 'service/loadnodenames/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(selectedDataset),
        dataType: 'json',
        success: function (response) {
            console.log('data returned:', response.result);
            if (graphIndexString === 'A') {
                // copy the result into the array and enable name selection from the input field
                entityAlign.graphAnodeNames = response.result.nodes;
                var inputfield = d3.select('#ga-name');
                inputfield.attr('disabled', null);
                updateUserList(response.result.nodes);
            } else {
                entityAlign.graphBnodeNames = response.result.nodes;
            }
        }
    });
}

function emptyGraphBArea() {
    // clear possible leftover state from a previous search
    //document.getElementById('gb-name').value = '';
    $('#graph2').empty();
    $('#info2').empty();
    //DWM::
}

function updateGraph1() {
    var graph1opt = ($('#graph1-selector').val() ||
                     $('#graph1-selector option:selected').text());

    d3.select('#graph2-selector')
        .text(graph1opt === 'Twitter' ? 'Instagram' : 'Twitter');

    //updateGraph1_d3()
    //initGraph1FromDatastore()
    loadNodeNames('A');
    initGraphStats('A');
    // clear out the person name element
    document.getElementById('ga-name').value = '';
    emptyGraphBArea();
    $('#graph1').empty();
    $('#info1').empty();
    // below is too powerful, it clears the LineUp area, but LU doesn't work anymore
    //$('#lugui-wrapper').empty()
}


function updateGraph2() {
    //initGraph2FromDatastore()
    // this rendering call below is the old style rendering, which doesn't update.  comment this out in favor of using
    //updateGraph2_d3_afterLoad()
    //updateGraph2_d3()
    loadNodeNames('B');
    initGraphStats('B');
    // clear out the person name element
    document.getElementById('gb-name').value = '';
    $('#graph2').empty();
    $('#info2').empty();
    //$('#lugui-wrapper').empty()
}


/*
// define a key return function that makes sre nodes are matched up using their ID values.  Otherwise D3 might
// color the wrong nodes if the access order changes
function nodeKeyFunction(d) {
    return d.id;
}
*/

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.


/*
function initGraph1WithClique() {
    'use strict';
    //entityAlign.ac.logUserActivity('Update Rendering.', 'render', entityAlign.ac.WF_SEARCH);
    logSystemActivity('graph_A_group', '#graph1', 'EXAMINE', 'SHOW', ['clique', 'neightborhood']);
    var data,
        graphData,
        graph1,
        view1,
        info1;

    // Get the name of the graph dataset to render
    var graphPathname = d3.select('#graph1-selector').node();
    var selectedDataset = getDatasetName(graphPathname.options[graphPathname.selectedIndex].text);

    var centralHandle  = document.getElementById('ga-name').value;
    console.log('doing one hop around', centralHandle);

    var logText = 'dataset1 select: start=' + graphPathname;
    //logSystemActivity('Kitware entityAlign - '+logText);

    window.graph1 = graph1 = new clique.Graph({
            adapter: clique.adapter.Mongo,
            options: {
                host:  entityAlign.host,
                database: entityAlign.graphsDatabase,
                collection: selectedDataset
            }
        });

    console.log('selectedDataset', selectedDataset);

    graph1.adapter.findNode({username: centralHandle})
            .then(function (center) {
                console.log('center:', center);
                if (center) {
                    graph1.addNeighborhood({
                        center: center,
                        radius: 1,
                        deleted: false
                    });

                }
            });

    window.view1 = view1 = new clique.view.Cola({
        model: graph1,
        el: '#graph1'
    });

    window.info1 = info1 = new clique.view.SelectionInfo({
        model: view1.selection,
        el: '#info1',
        graph: graph1
    });
}


function initGraph2WithClique() {

    'use strict';
    logSystemActivity('graph_B_group', '#graph2', 'EXAMINE', 'SHOW', ['clique', 'neightborhood']);
    var data,
        graphData,
        graph2,
        view2,
        info2;

    // Get the name of the graph dataset to render
    var selectedDataset = getDatasetName(d3.select('#graph2-selector').text());

    var centralHandle  = document.getElementById('gb-name').value;
    console.log('doing one hop around', centralHandle);

    //var logText = 'dataset2 select: start='+graphPathname;
    //logSystemActivity('Kitware entityAlign - '+logText);

    window.graph2 = graph2 = new clique.Graph({
            adapter: clique.adapter.Mongo,
            options: {
                host:  entityAlign.host,
                database: entityAlign.graphsDatabase,
                collection: selectedDataset
            }
        });

    graph2.adapter.findNode({name: centralHandle})
            .then(function (center) {
                console.log('center:', center)
                if (center) {
                    graph2.addNeighborhood({
                        center: center,
                        radius: 1,
                        deleted: false
                    });

                }
            });

    window.view2 = view2 = new clique.view.Cola({
        model: graph2,
        el: '#graph2'
    });

    window.info2 = info2 = new clique.view.SelectionInfo({
        model: view2.selection,
        el: '#info2',
        graph: graph2
    });

}
*/

function publishPairLists() {
    logPublishPairings();
    console.log('publishing');
}

// open the user homepages by clicking buttons on the UI.  This checks which way the association is going and opens
// the appropriate homepage.  The test had to examine
function openHompageGraph1() {
    var graphPathname = d3.select('#graph1-selector').node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
    var handleName = document.getElementById('ga-name').value;
    console.log('slice:', selectedDataset);
    if (selectedDataset === 'Twitter') {
        //console.log('opening twitter')
        logOpenTwitterWindow();
        window.open('http://www.twitter.com/' + handleName);
    } else {
        //console.log('opening instagram')
        logOpenInstagramWindow();
        window.open('http://www.instagram.com/' + handleName);
        //var selectedDataset = getDatasetName(graphPathname);
    }
}


function openHompageGraph2() {
    var graphB = getDatasetName(d3.select('#graph2-selector').text());
    //console.log('homepage datatype:',graphB)
    var handleName = document.getElementById('gb-name').value;
    //console.log('handle was:',handleName)
    // *** Kludge,  why does this come back with the dataset name instead of Twitter or instagram? This test
    // will function only if the collection names starts with 'twitter_'
    //console.log('slice:',graphB.slice(0,7))
    if (graphB.slice(0, 7) === 'twitter') {
        //console.log('opening twitter')
        logOpenTwitterWindow();
        window.open('http://www.twitter.com/' + handleName);
    } else {
        //console.log('opening instagram')
        logOpenInstagramWindow();
        window.open('http://www.instagram.com/' + handleName);
        //var selectedDataset = getDatasetName(graphPathname);
    }
}

/* Select a row in lineup.
 *
 * @param row: the row of data we passed to lineup.
 */
function selectUserFromLineup(row) {
    logSelectLineUpEntry();

    if (!row || !row.id) {
        return;
    }
    var handle  = $('#person-list select').val();
    if (handle.indexOf(' - ') >= 0) {
        handle = handle.substr(0, handle.indexOf(' - '));
    }
    var graphPathname = $('#graph1-selector').val();
    var graphA = getDatasetName(graphPathname);
    d3.json('service/getpotentialuser/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(graphA) + '/' + encodeURIComponent(handle) + '/' + encodeURIComponent(row.id), function (err, response) {
        var match = response.result || row;
        $('#match #match-type span').text(match.type || 'Unknown');
        $('#match #match-id span').text(match.user_id || 'Unknown');
        $('#match #match-description span').text(match.description || '');
        var link, id = row.id;
        if (match.type === 'twitter_user') {
            link = 'http://twitter.com/' + match.user_id;
        }
        $('#match #match-link span').empty();
        if (link) {
            $('#match #match-link span').append($('<a/>').attr(
                'href', link).text(link));
        }
        actionState.currentMatch = id;
        actionState.data.lineuprow = row;
        if (!actionState.matches[id]) {
            actionState.matches[id] = {
                'check': null,
                'confidence': 50
            };
        }
        $('#match-enabled').prop('checked', actionState.matches[id].check);
        $('#match-enabled').prop(
            'indeterminate', actionState.matches[id].check === null);
        $('#match-confidence').bootstrapSlider(
            'setValue', actionState.matches[id].confidence);
    });
}

/* Create or recreate a lineup control.
 *
 * @param elem: selector to the parent div wrapper for the control.
 * @param name: name of the control.
 * @param desc: column description.
 * @param dataset: dataset to load.
 * @lineupObj: old lineup object to replace.
 * @returns: a lineup control object.
 */
function createLineup(elem, name, desc, dataset, lineupObj) {
    /* This has been parroted from th demo. */
    var spec = {};
    spec.name = name;
    spec.dataspec = desc;
    delete spec.dataspec.file;
    delete spec.dataspec.separator;
    spec.dataspec.data = dataset;
    spec.storage = LineUp.createLocalStorage(
        dataset, desc.columns, desc.layout, desc.primaryKey);

    if (lineupObj) {
        lineupObj.changeDataStorage(spec);
    } else {
        lineupObj = LineUp.create(
            spec, d3.select(elem), lineUpConfig);
    }
    return lineupObj;
}

function initializeLineUpAroundEntity(handle) {
    logSetupLineUp();
    //InitializeLineUpJS();
    var graphPathname = $('#graph1-selector').val();
    var graphA = getDatasetName(graphPathname);
    var graphB = getDatasetName(d3.select('#graph2-selector').text());

    //var displaymodeselector = d3.select('#lineup-selector').node();
    //var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;

    // setup the machinery to allow the interface to be used to introspect inside a single dataset or compare between the datasets
    // a displaymode selector (currently disabled) can be set to determine which mode the UI shuld be in.

    //var displaymode = 'compare networks'
    var displaymode = 'document rankings';
    if (displaymode === 'document rankings') {
        d3.json('service/lineupuser/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(graphA) + '/' + encodeURIComponent(handle), function (err, response) {
            var dataset = response.result, desc = response;
            actionState.data.lineup = response;
            actionState.matches = {};
            loadDataImpl('main', desc, dataset);
            lineup.sortBy('Combined');
            lineup.on('selected', selectUserFromLineup);
        });
        return;
    }
    d3.json('service/lineupdatasetdescription/' + displaymode + '/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(graphA) + '/' + encodeURIComponent(handle),  function (err, desc) {
        console.log('description:', desc);
        console.log(displaymode);
        if (displaymode === 'compare networks') {
            d3.json('service/lineupdataset/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + graphB + '/' + handle + '/' + displaymode, function (err, dataset) {
                console.log('lineup loading description:', desc);
                console.log('lineup loading dataset for handle:', handle, dataset.result);
                loadDataImpl('main', desc, dataset.result);
                lineup.sortBy('Combined');
            });
        } else {
            d3.json('service/loadkhop/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle, function (err, response) {
                var encodedEntityList = JSON.stringify(response.nodes);
                d3.json('service/lineupdataset_neighborhood/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle + '/' + encodedEntityList + '/' + displaymode, function (err, dataset) {
                        console.log('lineup loading description:', desc);
                        console.log('lineup loading dataset for handle:', handle, dataset.result);
                        loadDataImpl('main', desc, dataset.result);
                    });
            });
        }
    });
}

function getEntityJSON(handle) {
    var graphPathname = $('#graph1-selector').val();
    var graphA = getDatasetName(graphPathname);
    d3.json('service/loadentityrecord/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(graphA) + '/' + encodeURIComponent(handle), function (err, res) {
        $('#graph1-json-info').empty();
        /*
        var editor = new JSONEditor($('#graph1-json-info')[0],
                                    {'mode': 'text'}, res.result);
        if (editor.expandAll) {
            editor.expandAll();
        }
        $('#graph1-json-info textarea').prop('readonly', true);
        */
        entityAlign.jsonToTable('#graph1-json-info', res.result);
        var h = $('#graph1-header').closest('.container-fluid').innerHeight();
        h -= $('#graph1-json-info').position().top;
        h -= 5;
        $('#graph1-json-info').height(h + 'px');
    });
}

function exploreLocalGraphAregion() {
    //var centralHandle  = document.getElementById('ga-name').value;
    var centralHandle  = $('#person-list select').val();
    //console.log('doing one hop around',centralHandle)
    //initGraph1FromDatastore();
    //initGraph1WithClique()
    if (centralHandle.indexOf(' - ') >= 0) {
        centralHandle = centralHandle.substr(0, centralHandle.indexOf(' - '));
    }
    actionState.guid = centralHandle;
    $('#document-controls').css('display', 'none');
    $('#document-panel').css('display', 'none');
    $('#match-controls').css('display', 'block');
    $('#match-panel').css('display', 'block');
    //DWM:: clear match data
    initializeLineUpAroundEntity(centralHandle);
    getEntityJSON(centralHandle);

    emptyGraphBArea();
}

/* Get the current match options and store them for the current match so that
 * we can work with them later.
 */
function updateMatchOptions() {
    var enabledText = '';
    var matchState = actionState.matches[actionState.currentMatch];
    if (!$('#match-enabled').prop('indeterminate')) {
        matchState.check = $('#match-enabled').is(':checked');
        enabledText = matchState.check ? 'yes' : 'no';
    }
    matchState.confidence = $('#match-confidence').bootstrapSlider(
        'getValue');
    actionState.data.lineuprow.enabled = enabledText;
    actionState.data.lineuprow.confidence = (
        enabledText !== '' ? matchState.confidence : undefined);
    lineup.updateBody();
}

/* Use a python service to search the datastore and return a list of
 * available networks to pick from.  This fills a GUI selector, so the user
 * can see what datasets are available.
 */
function fillDatasetList(element) {
    d3.select(element).selectAll('a').remove();
    d3.json('service/listdatasets/' + entityAlign.host + '/' + entityAlign.graphsDatabase, function (error, entities) {
        $('option', element).remove();
        for (var i = 0; i < entities.result.length; i += 1) {
            var record = entities.result[i];
            var opt = $('<option/>').text(record.name).val(record.value);
            $(element).append(opt);
            if (!record.value) {
                opt.prop('disabled', true);
                opt.val('');
            }
        }
        if ($(element).val() === '') {
            $(element).val($('option', element).eq(0).val());
        }
        if ($(element).val() === '') {
            $(element).val($('option', element).eq(1).val());
        }
    });
}

function exploreLocalGraphBregion(handle) {
    // set the UI to show who we are exploring around in graphB
    logSelectLineUpEntry();
    handle = handle;  // ignore unused variable
    /*
    document.getElementById('gb-name').value = handle;
    initGraph2WithClique()
    */
}

// this function resets lineup to the appropriate view whenever the focus selector is changed
function handleLineUpSelectorChange() {
    var displaymodeselector = d3.select('#lineup-selector').node();
    var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;
    if (displaymode === 'left network only') {
        exploreLocalGraphAregion();
    } else if (displaymode === 'right network only') {
        exploreLocalGraphBregion();
    } else {
        exploreLocalGraphAregion();
    }
}

// this function is called on initialization and it just fills a selector with the three options of
// comparing datasets or focusing on the left or right one
// *** disable the lineup options until they work by having only one entry in the selector
function fillLineUpSelector() {
    d3.select('#lineup-selector').selectAll('option')
        .data(['compare networks', 'left network only', 'right network only', 'document rankings'])
        .text(function (d) {
            return d;
        });
}

function acceptListedPairing() {

    // these aren't set anymore in the streamlined UI
    //var graphPathname = d3.select('#graph1-selector').node();
    //var graphA = graphPathname.options[graphPathname.selectedIndex].text;
    //var graphPathname = d3.select('#graph2-selector').node();
    //var graphB = graphPathname.options[graphPathname.selectedIndex].text;

    var handleA  = document.getElementById('ga-name').value;
    var handleB  = document.getElementById('gb-name').value;

    var newPairing = {'twitter' : handleA, 'instagram': handleB};

    // store an entry only if the array doesn't already have the entry
    // tried $.inArray()  and .indexOf() unsuccessfully

    var found = false;
    for (var pair in entityAlign.pairings) {
        if ((pair.twitter === handleA) && (pair.instagram === handleB)) {
            found = true;
        }
    }
    if (found === false) {
        entityAlign.pairings.push(newPairing);
        console.log('new pairing: ', newPairing);
    }

    // this is the pairing (seed) display table which is in a modal popover.  This is used to
    // draw a nice table using Bootstrap an jQuery

    // update the table
    $('#pairings-table').bootstrapTable('hideLoading');
    $('#pairings-table').bootstrapTable('load', entityAlign.pairings);
}

function showPairings() {
}

/* Show the currently selected match, next and previous buttons as appropriate,
 * and fetch the lineup data for this set of documents.
 */
function updateDocumentLineup() {
    var row = actionState.data.matchedRows[actionState.currentRow];
    $('#doc-match-desc').text(row.row.description);
    $('#doc-match-confidence').text(row.match.confidence || 0);
    var graphPathname = $('#graph1-selector').val();
    var graphA = getDatasetName(graphPathname);
    d3.json('service/lineupuserdoc/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + encodeURIComponent(graphA) + '/' + encodeURIComponent(actionState.guid) + '/' + encodeURIComponent(row.id), function (err, response) {
        actionState.data.doclineup = response;
        console.log(response);
        var dataset = response.result, desc = response;
        lineup2 = createLineup(
            '#lugui2-wrapper', 'second', desc, dataset, lineup2);
        lineup2.sortBy('Combined');
        lineup2.on('selected', selectUserFromLineup);
    });
    //DWM::
}

/* Review the next possible match of documents in the list.
 */
function reviewNext() {
    var len = actionState.data.matchedRows.length;
    actionState.currentRow = (actionState.currentRow + 1) % len;
    updateDocumentLineup();
}

/* Review the previous possible match of documents in the list.
 */
function reviewPrevious() {
    var len = actionState.data.matchedRows.length;
    actionState.currentRow = (actionState.currentRow + len - 1) % len;
    updateDocumentLineup();
}

/* Given a selection of possible matches, show the documents for them.
 */
function reviewDocuments() {
    var docs = [];
    for (var i = 0; i < actionState.data.lineup.result.length; i += 1) {
        var row = actionState.data.lineup.result[i];
        if (actionState.matches[row.id] && actionState.matches[row.id].check) {
            docs.push({
                row: row, match: actionState.matches[row.id], id: row.id});
        }
    }
    if (!docs.length) {
        alert('No possible matches were indicated, therefore there are no documents to review.');
        return;
    }
    actionState.data.matchedRows = docs;
    actionState.currentRow = 0;
    $('#match-controls').css('display', 'none');
    $('#match-panel').css('display', 'none');
    $('#document-controls').css('display', 'block');
    $('#document-panel').css('display', 'block');
    $('#doc-prev-button').toggleClass('disabled', docs.length <= 1);
    $('#doc-next-button').toggleClass('disabled', docs.length <= 1);
    updateDocumentLineup();
}

function firstTimeInitialize() {
    'use strict';

    // make the panel open & close over data content
    //$('#control-panel').controlPanel();

    $('#ga-name').autocomplete().keyup(function (evt) {
        // respond to enter by starting a query
        if (evt.which === 13) {
            updateUserList(entityAlign.graphAnodeNames);
        }
    });

    d3.json('defaults.json', function (err, defaults) {
        defaults = defaults || {};

        for (var key in defaults) {
            if (defaults.hasOwnProperty(key)) {
                entityAlign[key] = defaults[key];
            }
        }

        fillDatasetList('#graph1-selector');
        // fillSeedList('#seed-selector')

        width = $(window).width();
        height = $(window).height();

        // set up the keystroke and mouse logger
        initializeLoggingFramework(defaults);

        color = d3.scale.category20();
        //color = entityAlignDistanceFunction;

        fillLineUpSelector();
        // set a watcher on the dataset selector so datasets are filled in
        // automatically when the user selects it via UI selector elements.

        d3.select('#graph1-selector')
            .on('change', function () {
                updateGraph1();
                updateGraph2();
            });
        d3.select('#lineup-selector')
            .on('change', handleLineUpSelectorChange);
        d3.select('#show-pairings')
            .on('click', showPairings);
        d3.select('#examine-button')
            .on('click', exploreLocalGraphAregion);
        d3.select('#review-button')
            .on('click', reviewDocuments);
        d3.select('#doc-prev-button').on('click', reviewPrevious);
        d3.select('#doc-next-button').on('click', reviewNext);
        //DWM::d3.select('#doc-report-button').on('click', reviewNext);
        d3.select('#accept-button')
            .on('click', acceptListedPairing);
        d3.select('#graph1-homepage')
            .on('click', openHompageGraph1);
        d3.select('#graph2-homepage')
            .on('click', openHompageGraph2);
        d3.select('#show-matches-toggle')
            .attr('disabled', true)
            .on('click',  function () {
                entityAlign.showMatchesEnabled = !entityAlign.showMatchesEnabled;
                console.log(entityAlign.showMatchesEnabled);
            });
        $('#match-confidence').bootstrapSlider();
        $('#match-confidence').on('change', updateMatchOptions);
        $('#match-enabled').on('change', updateMatchOptions);
        /* Process these functions after a short delay. */
        window.setTimeout(function () {
            updateGraph1();
        }, 1000);
        // block the contextmenu from coming up (often attached to right clicks). Since many
        // of the right clicks will be on the graph, this has to be at the document level so newly
        // added graph nodes are all covered by this handler.

        /**
         * No! Only block context menu on _specific_ elements!
         *
        $(document).bind('contextmenu', function(e){
            e.preventDefault();
            return false;
            });
        */

    });

    d3.select('#publish-parings-button')
        .on('click', publishPairLists);

    // declare a Boostrap table to display pairings made by the analyst

    $('#pairings-table').bootstrapTable({
        data: entityAlign.pairings,
        columns: [{
            field: 'twitter',
            title: 'Twitter Username'
        }, {
            field: 'instagram',
            title: 'Instagram Username'
        }]
    });

}


// *** initialization.  What do we do the first time the app is opened and the document is ready?

window.onload = function ()  {

    firstTimeInitialize();    // Fill out the dataset selectors with graph datasets that we can choose from

};

/*
// use a python service to search the datastore and return a list of available seed arrays to pick from.  This fills a GUI selector, so the user
// can see what datasets are available.
function fillSeedList(element) {
    d3.select(element).selectAll('a').remove();
    d3.json('service/listseeds/' + entityAlign.host + '/' + entityAlign.graphsDatabase, function (error, entities) {
        console.log(entities);
        // save in a temporary list so we can refer back during a click event
        d3.select(element).selectAll('option')
        .data(entities.result)
        .enter().append('option')
        .text(function (d) {
            return d;
        });
    });
}
*/
