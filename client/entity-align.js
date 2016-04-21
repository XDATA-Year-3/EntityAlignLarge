/* globals $, _, console, d3, log, clique, createLineup,
   initializeLoggingFramework, logPublishPairings, logOpenTwitterWindow,
   logOpenInstagramWindow, logSetupLineUp, logSelectLineUpEntry */

var entityAlign = {};
entityAlign.force1 = null;
entityAlign.force2 = null;
entityAlign.host = null;
entityAlign.ac = null;
entityAlign.textmode = false;

var defaultCola = {
  linkDistance: 75,
  nodeRadius: 5,
  label: function (d) {
    return d.data ? (d.data.name || '') : '';
  }
};

// logging is handled largely in

function logSystemActivity (group, element, activityEnum, action, tags) {
  group = typeof group !== 'undefined' ? group : 'system_group';
  activityEnum = typeof activityEnum !== 'undefined' ? activityEnum : 'show';
  action = typeof action !== 'undefined' ? action : 'SHOW';
  tags = typeof tags !== 'undefined' ? tags : [];
  var msg = {
    activity: activityEnum,
    action: action,
    elementId: element,
    elementType: 'OTHER',
    elementGroup: group,
    source: 'system',
    tags: tags,
    meta: {
      element: element
    }
  };
  log(msg);
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
// "ga" and "gb" attribute, whose corresponding values are integers that match the node IDs.
entityAlign.currentMatches = [];
entityAlign.pairings = [];

// how far to go out on the default rendering of a local neighborhood
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

function updateGraph1 () {
  //updateGraph1_d3()
  //initGraph1FromDatastore()
  loadNodeNames('A');
  initGraphStats('A');
  // clear out the person name element
  document.getElementById('ga-name').value = '';
  document.getElementById('gb-name').value = '';
  emptyCliqueGraph(entityAlign.graph1);
  $('#graph1').empty();
  $('#info1').empty();
  entityAlign.graph1 = null;
}

function updateGraph2 () {
  //initGraph2FromDatastore()
  // this rendering call below is the old style rendering, which doesn't update.  comment this out in favor of using
  //updateGraph2_d3_afterLoad()
  //updateGraph2_d3()
  loadNodeNames('B');
  initGraphStats('B');
  // clear out the person name element
  document.getElementById('gb-name').value = '';
  emptyCliqueGraph(entityAlign.graph2);
  $('#graph2').empty();
  $('#info2').empty();
  entityAlign.graph2 = null;
}

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function initGraphStats (graphIndexString) {
  'use strict';
  var graphelement = (graphIndexString === 'A') ? '#graph1' : '#graph2';
  logSystemActivity('graph_' + graphIndexString + '_group', graphelement, 'inspect', 'OPEN');
  var data, selectedDataset;

  // Get the name of the graph dataset to render
  if (graphIndexString === 'A') {
    selectedDataset = $('#graph1-selector').val();
    // save the current dataset name for the graph
    entityAlign.graphA_dataset = selectedDataset;
  } else {
    selectedDataset = $('#graph2-selector').val();
    // save the current dataset name for the graph
    entityAlign.graphB_dataset = selectedDataset;
  }
  // logSystemActivity('Kitware entityAlign - '+logText);

  $.ajax({
    // generalized collection definition
    url: 'service/loadgraphsummary/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + selectedDataset,
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
        d3.select('#ga-linkCount').text(response.result.links.toString());
      } else {
        d3.select('#gb-nodeCount').text(response.result.nodes.toString());
        d3.select('#gb-linkCount').text(response.result.links.toString());
      }
    }

  });
}

// ----- start of autocomplete for users

// do a non-blocking call to a python service that returns all the names in the graph.  Assign this to a global variable
function loadNodeNames (graphIndexString) {
  var selectedDataset;

  // Get the name of the graph dataset to render
  if (graphIndexString === 'A') {
    selectedDataset = $('#graph1-selector').val();
  } else {
    selectedDataset = $('#graph2-selector').val();
  }

  // non-blocking call to initialize this
  var data;
  $.ajax({
    url: 'service/loadnodenames/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + selectedDataset,
    data: data,
    dataType: 'json',
    success: function (response) {
      if (response.error) {
        console.log('error: ' + response.error);
        return;
      }
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

$('#ga-name').autocomplete().keyup(function (evt) {
  console.log(evt);
  // respond to enter by starting a query
  if (evt.which === 13) {
    updateUserList(entityAlign.graphAnodeNames);
  }
});

// reset the user list on a new time range query
function resetUserList () {
  $('#ga-name').autocomplete({ source: [] });
}

// update the user list from a mongo response
function updateUserList (namelist) {
  resetUserList();

  // Update the user filter selection box
  // .slice(0, 10)
  $('#ga-name').autocomplete({source: namelist});
}

// ------ end of autocomplete users

/* Empty a clique graph of all nodes and cancel any pending requests.
 *
 * @param existing: optional existing graph information to update.
 */
function emptyCliqueGraph (existing) {
  if (existing) {
    if (existing.adapter) {
      /* Cancel old pending requests */
      existing.adapter.cancel();
    }
    if (existing.graph && existing.graph.nodes) {
      var oldNodes = [];
      $.each(existing.graph.nodes, function (node) {
        oldNodes.push(node);
      });
      existing.graph.removeNodes(oldNodes);
    }
  }
}

/* Create a clique graph for a particular element and dataset.
 *
 * @param selectedDataset: name of the collection to load from.
 * @param existing: optional existing graph information to update.
 * @param graphElement: name of the selector to place the graph (e.g.,
 *                      '#graph1')
 * @param infoElement: optional name of selector to place info element that is
 *                     shown when a node is selected.
 * @param linkInfoElement: optional name of selector to place link info element
 *                         that is shown when a link is selected.
 * @returns: an object with graph, view, info, linkinfo, and selectedDataset.
 */
function createCliqueGraph (selectedDataset, existing, graphElement, infoElement, linkInfoElement) {
  'use strict';

  emptyCliqueGraph(existing);
  if (existing && existing.selectedDataset === selectedDataset &&
      existing.graphElement === graphElement &&
      existing.infoElement === infoElement &&
      existing.linkInfoElement === linkInfoElement) {
    return existing;
  }

  var graph = {
    selectedDataset: selectedDataset,
    graphElement: graphElement,
    infoElement: infoElement,
    linkInfoElement: linkInfoElement
  };

  graph.adapter = clique.adapter.Mongo({
    host: entityAlign.host,
    database: entityAlign.graphsDatabase,
    collection: selectedDataset
  });
  graph.graph = new clique.default.model.Graph({
    adapter: graph.adapter
  });
  console.log('selectedDataset', selectedDataset);

  graph.view = new clique.default.view.Cola($.extend(
    {}, defaultCola, {
      model: graph.graph,
      el: graphElement
    }
  ));
  graph.view.mode = 'label';

  if (infoElement) {
    var SelectionInfo = clique.default.view.SelectionInfo;
    graph.info = new SelectionInfo({
      model: graph.view.selection,
      el: infoElement,
      graph: graph.graph
    });
    graph.info.render();
  }

  if (linkInfoElement) {
    graph.linkinfo = new clique.default.view.LinkInfo({
      model: graph.view.linkSelection,
      el: linkInfoElement,
      graph: graph.graph
    });
    graph.linkinfo.render();
  }

  /* Handle a context menu callback on the clicked-on node.  If multiple nodes
   * are selected and that selection includes the clicked node, process all of
   * the selected nodes.
   */
  function contextCallback (menu, evt) {
    var nodekey = d3.select(evt.$trigger.closest('.node')[0]).datum().key;
    var nodes;
    if (graph.view.selected.has(nodekey)) {
      nodes = Array.from(graph.view.selected);
    } else {
      nodes = [nodekey];
    }
    var func = {
      hide: SelectionInfo.hideNode,
      expand: SelectionInfo.expandNode
    }[menu];
    nodes.forEach(function (nodekey) {
      graph.adapter.findNodeByKey(nodekey).then(function (node) {
        _.bind(func, graph.info)(node);
      });
    });
  }

  $.contextMenu({
    selector: graphElement + ' g.node',
    position: function (evt, x, y) {
      var elem = evt.$trigger.closest('.node');
      var offset = elem.offset();
      evt.$menu.css({top: offset.top + 10, left: offset.left});
    },
    items: {
      hide: {name: 'Hide', callback: contextCallback},
      expand: {name: 'Expand', callback: contextCallback},
      toggle: {name: 'Toggle Labels', callback: function () {
        graph.view.toggleLabels();
      }}
    }
  });
  return graph;
}

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function initGraph1WithClique () {
  'use strict';
  // entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
  logSystemActivity('graph_A_group', '#graph1', 'INSPECT', 'SHOW', ['clique', 'neighborhood']);

  var selectedDataset = $('#graph1-selector').val();

  var centralHandle = document.getElementById('ga-name').value;
  console.log('doing one hop around', centralHandle);

  // logSystemActivity('Kitware entityAlign - '+logText);

  var graph = createCliqueGraph(selectedDataset, entityAlign.graph1, '#graph1',
                                '#info1');
  entityAlign.graph1 = graph;

  graph.graph.adapter.findNode({name: centralHandle}).then(function (center) {
    console.log('center:', center);
    if (center) {
      graph.graph.addNode(center);
      graph.graph.addNeighborhood(center);
    }
  });
}

function initGraph2WithClique () {
  'use strict';
  logSystemActivity('graph_B_group', '#graph2', 'INSPECT', 'SHOW', ['clique', 'neighborhood']);

  var selectedDataset = $('#graph2-selector').val();

  var centralHandle = document.getElementById('gb-name').value;
  console.log('doing one hop around', centralHandle);

  //logSystemActivity('Kitware entityAlign - '+logText);

  var graph = createCliqueGraph(selectedDataset, entityAlign.graph2, '#graph2',
                                '#info2');
  entityAlign.graph2 = graph;

  graph.graph.adapter.findNode({name: centralHandle}).then(function (center) {
    console.log('center:', center);
    if (center) {
      graph.graph.addNode(center);
      graph.graph.addNeighborhood(center);
    }
  });
}

function publishPairLists () {
  logPublishPairings();
  console.log('publishing');
}

// open the user homepages by clicking buttons on the UI.  This checks which way the association is going and opens
// the appropriate homepage.  The test had to examine
function openHompageGraph1 () {
  var selectedDataset = $('#graph1-selector').val();

  var handleName = document.getElementById('ga-name').value;
  console.log('slice:', selectedDataset);
  if (selectedDataset.slice(0, 7) === 'twitter') {
    //console.log('opening twitter')
    logOpenTwitterWindow();
    window.open('http://www.twitter.com/' + handleName);
  } else {
    //console.log('opening instagram')
    logOpenInstagramWindow();
    window.open('http://www.instagram.com/' + handleName);
  }
}

function openHompageGraph2 () {
  var selectedDataset = $('#graph2-selector').val();
  //console.log('homepage datatype:',graphB)
  var handleName = document.getElementById('gb-name').value;
  //console.log('handle was:',handleName)
  // *** Kludge,  why does this come back with the dataset name instead of Twitter or instagram? This test
  // will function only if the collection names starts with 'twitter_'
  //console.log('slice:',graphB.slice(0,7))
  if (selectedDataset.slice(0, 7) === 'twitter') {
    //console.log('opening twitter')
    logOpenTwitterWindow();
    window.open('http://www.twitter.com/' + handleName);
  } else {
    //console.log('opening instagram')
    logOpenInstagramWindow();
    window.open('http://www.instagram.com/' + handleName);
  }
}

/* Set the available datasets.  Pick the first one.  If there is only one, show
 * a fixed display rather than a control.
 *
 * @param datasets: a list of datasets.  Each entry is either a string (in which case the string is used as both the collection name and the display name), or an object with key and name, where 'key' is the collection name and 'name' is the display name.
 * @param selector: the seletor of the <select> element.
 * @param fixed: the selector of the fixed element.
 */
function setGraphDatasets (datasets, selector, fixed) {
  var first;
  $.each(datasets, function (idx, set) {
    if (!set.key) {
      set = {key: set, name: set};
    }
    $(selector).append(
        $('<option/>').text(set.name).attr('value', set.key));
    if (!idx) {
      $(fixed).text(set.name);
      first = set.key;
    }
  });
  if (datasets.length === 1) {
    $(selector).hide();
    $(fixed).show();
  }
  $(selector).val(first);
}

function firstTimeInitialize () {
  'use strict';

  // make the panel open & close over data content
  //$('#control-panel').controlPanel();

  d3.json('defaults.json', function (ignore_err, defaults) {
    defaults = defaults || {};

    // read default data collection names from config file
    entityAlign.host = defaults.mongoHost || 'localhost';
    entityAlign.graphsDatabase = defaults.graphsDatabase || 'year3_graphs';
    console.log('set graphs database: ', entityAlign.graphsDatabase);

    fillSeedList('#seed-selector');

    /*
    var width = $(window).width();
    var height = $(window).height();
    */

    // set up the keystroke and mouse logger
    initializeLoggingFramework(defaults);

    /*
    var color = d3.scale.category20();
    */
    //color = entityAlignDistanceFunction;

    fillLineUpSelector();
    // set a watcher on the dataset selector so datasets are filled in
    // automatically when the user selects it via UI selector elements.

    d3.select('#graph1-selector').on('change', updateGraph1);
    d3.select('#graph2-selector').on('change', updateGraph2);
    d3.select('#lineup-selector')
            .on('change', handleLineUpSelectorChange);
    d3.select('#show-pairings')
            .on('click', showPairings);
    d3.select('#onehop-button')
            .on('click', ExploreLocalGraphAregion);
    d3.select('#accept-button')
            .on('click', acceptListedPairing);
    d3.select('#graph1-homepage')
            .on('click', openHompageGraph1);
    d3.select('#graph2-homepage')
            .on('click', openHompageGraph2);
    d3.select('#show-matches-toggle')
            .attr('disabled', true)
            .on('click', function () {
              entityAlign.showMatchesEnabled = !entityAlign.showMatchesEnabled;
              console.log(entityAlign.showMatchesEnabled);
            });

    setGraphDatasets(defaults.graph1Datasets || ['twitter'], '#graph1-selector', '#graph1-selector-one');
    setGraphDatasets(defaults.graph2Datasets || ['instagram'], '#graph2-selector', '#graph2-selector-one');
    updateGraph1();
    updateGraph2();
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

window.onload = function () {
  firstTimeInitialize();    // Fill out the dataset selectors with graph datasets that we can choose from
};

// use a python service to search the datastore and return a list of available seed arrays to pick from.  This fills a GUI selector, so the user
// can see what datasets are available.

function fillSeedList (element) {
  d3.select(element).selectAll('a').remove();
  d3.json('service/listseeds/' + entityAlign.host + '/' + entityAlign.graphsDatabase, function (ignore_err, entities) {
    console.log(entities, '\n');
    // save in a temporary list so we can refer back during a click event
    d3.select(element).selectAll('option')
            .data(entities.result)
            .enter().append('option')
            .text(function (d) { return d; });
  });
}

function InitializeLineUpAroundEntity (handle) {
  logSetupLineUp();
  //InitializeLineUpJS();
  var graphA = $('#graph1-selector').val();
  var graphB = $('#graph2-selector').val();

  //var displaymodeselector = d3.select("#lineup-selector").node();
  //   var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;

  // setup the machinery to allow the interface to be used to introspect inside a single dataset or compare between the datasets
  // a displaymode selector (currently disabled) can be set to determine which mode the UI shuld be in.

  var displaymode = 'compare networks';
  d3.json('service/lineupdatasetdescription/' + displaymode, function (ignore_err, desc) {
    console.log('description:', desc);
    if (displaymode === 'compare networks') {
      console.log('comparing networks');
      d3.json('service/lineupdataset/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + graphB + '/' + handle + '/' + displaymode, function (ignore_err, dataset) {
        console.log('lineup loading description:', desc);
        console.log('lineup loading dataset for handle:', handle, dataset.result);
        createLineup('#lugui-wrapper', 'main', desc, dataset.result, undefined,
                     'Combined', selectEntityFromLineup);
      });
    } else {
      console.log('local network');
      d3.json('service/loadkhop/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle, function (ignore_err, response) {
        var encodedEntityList = JSON.stringify(response.nodes);
        d3.json('service/lineupdataset_neighborhood/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle + '/' + encodedEntityList + '/' + displaymode, function (ignore_err, dataset) {
          console.log('lineup loading description:', desc);
          console.log('lineup loading dataset for handle:', handle, dataset.result);
          createLineup('#lugui-wrapper', 'main', desc, dataset.result,
                       undefined, 'Combined', selectEntityFromLineup);
        });
      });
    }
  });
}

function ExploreLocalGraphAregion () {
  var centralHandle = document.getElementById('ga-name').value;
  //console.log('doing one hop around',centralHandle)
  //initGraph1FromDatastore();
  initGraph1WithClique();
  InitializeLineUpAroundEntity(centralHandle);

  // clear possible leftover state from a previous search
  document.getElementById('gb-name').value = '';
  emptyCliqueGraph(entityAlign.graph2);
}

function ExploreLocalGraphBregion (handle) {
  // set the UI to show who we are exploring around in graphB
  logSelectLineUpEntry();
  document.getElementById('gb-name').value = handle;
  initGraph2WithClique();
}

/* When a lineup row is selected, change what graph B is showing.
 *
 * @param row: the selected lineup row.
 */
function selectEntityFromLineup (row) {
  if (!row || !row.entity) {
    return;
  }
  ExploreLocalGraphBregion(row['entity']);
}

// this function resets lineup to the appropriate view whenever the focus selector is changed
function handleLineUpSelectorChange () {
  var displaymodeselector = d3.select('#lineup-selector').node();
  var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;
  if (displaymode === 'left network only') {
    ExploreLocalGraphAregion();
  } else if (displaymode === 'right network only') {
    ExploreLocalGraphBregion();
  } else {
    ExploreLocalGraphAregion();
  }
}

// this function is called on initialization and it just fills a selector with the three options of
// comparing datasets or focusing on the left or right one

// *** disable the lineup options until they work by having only one entry in the selector

function fillLineUpSelector () {
  d3.select('#lineup-selector').selectAll('option')
            .data(['compare networks', 'left network only', 'right network only'])
            .text(function (d) { return d; });
}

function acceptListedPairing () {
  var handleA = document.getElementById('ga-name').value;
  var handleB = document.getElementById('gb-name').value;

  var newPairing = {'twitter': handleA, 'instagram': handleB};

  var found = _.any(entityAlign.pairings, function (pair) {
    return (pair['twitter'] === handleA && pair['instagram'] === handleB);
  });
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

function showPairings () {

}
