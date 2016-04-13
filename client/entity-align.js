/* globals $, console, d3, log, clique, lineup,
   initializeLoggingFramework, logPublishPairings, logOpenTwitterWindow,
   logOpenInstagramWindow, logSetupLineUp, logSelectLineUpEntry,
   loadDataImpl */

/* DWM::
var color = null;

var graph = null;
var svg = null;
var width = 0;
var height = 0;
var transition_time;
var translate = [0, 0];
*/

var entityAlign = {};
entityAlign.force1 = null;
entityAlign.force2 = null;
entityAlign.host = null;
entityAlign.ac = null;
entityAlign.textmode = false;

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
    tags: tags
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

function getDatasetName (label) {
  if (label === 'twitter_isil_36hours') {
    return entityAlign.twitter;
  } else if (label === 'twitter_isil_36hours') {
    return entityAlign.instagram;
  }
}

function updateGraph1 () {
  var graph1opt = d3.select('#graph1-selector').node();
  graph1opt = graph1opt.options[graph1opt.selectedIndex].text;

  d3.select('#graph2-selector')
        .text(graph1opt === 'Twitter' ? 'twitter_isil_36hours' : 'twitter_isil_36hours');
//        .text(graph1opt === "Twitter" ? "Instagram" : "Twitter");

  //updateGraph1_d3()
  //initGraph1FromDatastore()
  loadNodeNames('A');
  initGraphStats('A');
  // clear out the person name element
  document.getElementById('ga-name').value = '';
  document.getElementById('gb-name').value = '';
  $('#graph1').empty();
  $('#info1').empty();
  // below is too powerful, it clears the LineUp area, but LU doesn't work anymore
  //$('#lugui-wrapper').empty()
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
  $('#graph2').empty();
  $('#info2').empty();
  //$('#lugui-wrapper').empty()
}

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function initGraphStats (graphIndexString) {
  'use strict';
  var graphelement = (graphIndexString === 'A') ? '#graph1' : '#graph2';
  logSystemActivity('graph_' + graphIndexString + '_group', graphelement, 'inspect', 'OPEN');
  var data, graphPathname, selectedDataset;

  // Get the name of the graph dataset to render
  if (graphIndexString === 'A') {
    graphPathname = d3.select('#graph1-selector').node();
    selectedDataset = getDatasetName(graphPathname.options[graphPathname.selectedIndex].text);
    // save the current dataset name for the graph
    entityAlign.graphA_dataset = selectedDataset;
  } else {
    graphPathname = d3.select('#graph2-selector').text();
    selectedDataset = getDatasetName(graphPathname);
    // save the current dataset name for the graph
    entityAlign.graphB_dataset = selectedDataset;
  }
  // var logText = 'dataset ' + graphIndexString + ' select: start=' + graphPathname;
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
    var graphPathname = d3.select('#graph1-selector').node();
    selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
  } else {
    selectedDataset = d3.select('#graph2-selector').text();
  }

  selectedDataset = getDatasetName(selectedDataset);

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

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function initGraph1WithClique () {
  'use strict';
  // entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
  logSystemActivity('graph_A_group', '#graph1', 'EXAMINE', 'SHOW', ['clique', 'neightborhood']);
  var graph1, view1;

  // Get the name of the graph dataset to render
  var graphPathname = d3.select('#graph1-selector').node();
  var selectedDataset = getDatasetName(graphPathname.options[graphPathname.selectedIndex].text);

  var centralHandle = document.getElementById('ga-name').value;
  console.log('doing one hop around', centralHandle);

  // var logText = 'dataset1 select: start=' + graphPathname;
  // logSystemActivity('Kitware entityAlign - '+logText);

  window.graph1 = graph1 = new clique.Graph({
    adapter: clique.adapter.Mongo,
    options: {
      host: entityAlign.host,
      database: entityAlign.graphsDatabase,
      collection: selectedDataset
    }
  });

  console.log('selectedDataset', selectedDataset);

  graph1.adapter.findNode({name: centralHandle})
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

  window.info1 = new clique.view.SelectionInfo({
    model: view1.selection,
    el: '#info1',
    graph: graph1
  });
}

function initGraph2WithClique () {
  'use strict';
  logSystemActivity('graph_B_group', '#graph2', 'EXAMINE', 'SHOW', ['clique', 'neightborhood']);
  var graph2, view2;

  // Get the name of the graph dataset to render
  var selectedDataset = getDatasetName(d3.select('#graph2-selector').text());

  var centralHandle = document.getElementById('gb-name').value;
  console.log('doing one hop around', centralHandle);

  //var logText = "dataset2 select: start="+graphPathname;
  //logSystemActivity('Kitware entityAlign - '+logText);

  window.graph2 = graph2 = new clique.Graph({
    adapter: clique.adapter.Mongo,
    options: {
      host: entityAlign.host,
      database: entityAlign.graphsDatabase,
      collection: selectedDataset
    }
  });

  graph2.adapter.findNode({name: centralHandle})
            .then(function (center) {
              console.log('center:', center);
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

  window.info2 = new clique.view.SelectionInfo({
    model: view2.selection,
    el: '#info2',
    graph: graph2
  });
}
function publishPairLists () {
  logPublishPairings();
  console.log('publishing');
}

// open the user homepages by clicking buttons on the UI.  This checks which way the association is going and opens
// the appropriate homepage.  The test had to examine
function openHompageGraph1 () {
  var graphPathname = d3.select('#graph1-selector').node();
  var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
  var handleName = document.getElementById('ga-name').value;
  console.log('slice:', selectedDataset);
  if (selectedDataset === 'twitter_isil_36hours') {
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

function openHompageGraph2 () {
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

    entityAlign.twitter = defaults.twitter;
    entityAlign.instagram = defaults.instagram;

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

    d3.select('#graph1-selector')
            .on('change', function () {
              updateGraph1();
              updateGraph2();
            });
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
  var graphPathname = d3.select('#graph1-selector').node();
  var graphA = getDatasetName(graphPathname.options[graphPathname.selectedIndex].text);
  var graphB = getDatasetName(d3.select('#graph2-selector').text());

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
        loadDataImpl(name, desc, dataset.result);
        lineup.sortBy('Combined');
      });
    } else {
      console.log('local network');
      d3.json('service/loadkhop/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle, function (ignore_err, response) {
        var encodedEntityList = JSON.stringify(response.nodes);
        d3.json('service/lineupdataset_neighborhood/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + graphA + '/' + handle + '/' + encodedEntityList + '/' + displaymode, function (ignore_err, dataset) {
          console.log('lineup loading description:', desc);
          console.log('lineup loading dataset for handle:', handle, dataset.result);
          loadDataImpl(name, desc, dataset.result);
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
  $('#graph2').empty();
  $('#info2').empty();
}

function ExploreLocalGraphBregion (handle) {
  // set the UI to show who we are exploring around in graphB
  logSelectLineUpEntry();
  document.getElementById('gb-name').value = handle;
  initGraph2WithClique();
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
  // these aren't set anymore in the streamlined UI
  //var graphPathname = d3.select("#graph1-selector").node();
  //var graphA = graphPathname.options[graphPathname.selectedIndex].text;
  //var graphPathname = d3.select("#graph2-selector").node();
  //var graphB = graphPathname.options[graphPathname.selectedIndex].text;

  var handleA = document.getElementById('ga-name').value;
  var handleB = document.getElementById('gb-name').value;

  var newPairing = {'twitter': handleA, 'instagram': handleB};

  // store an entry only if the array doesn't already have the entry
  // tried $.inArray()  and .indexOf() unsuccessfully

  var found = false;
  for (var pair in entityAlign.pairings) {
    if (pair['twitter'] === handleA && pair['instagram'] === handleB) {
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

function showPairings () {

}
