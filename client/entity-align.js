/* globals $, _, console, d3, log, clique, createLineup, lineup,
   initializeLoggingFramework, logPublishPairings, logOpenTwitterWindow,
   logOpenInstagramWindow, logSetupLineUp, logSelectLineUpEntry */

var entityAlign = {
  host: null,
  graphsDatabase: null,
  maxFirstHopNodes: 100,
  nodesPerExpand: 100,
  /* Set to zero to disable timeout.  The graph timeout prevents large graphs
   * from consuming resources forever, but it is implemented crudely, and the
   * time doesn't reset on actions that occur while movement is still
   * happening.  This means that the graph will occasionally stop when it
   * shouldn't, but a nudge from the mouse would restart it.  Not ideal, but I
   * think it is better than making the app unusable on complicated graphs. */
  maxGraphActionTime: 10000
};

// there is a global array corresponding to the current matches known between the two loaded graphs.  The matches are an array of JSON objects, each with a
// "ga" and "gb" attribute, whose corresponding values are integers that match the node IDs.
entityAlign.pairings = [];

var defaultCola = {
  transitionTime: 0,
  linkDistance: 75,
  nodeRadius: 5,
  label: function (d) {
    return d.data ? (d.data.name || '') : '';
  },
  /* Show entities where we are certain there is no profile image with a
   * thinner border and a different color. */
  labelStrokeWidth: function (d) {
    return d.data && d.data.profile_image ? '2px' : '1px';
  },
  fill: function (d) {
    return d.data && d.data.profile_image ? 'blue' : 'green';
  },
  focusColor: 'yellow'
};
var unzoomCola = {
  linkDistance: 75
};
var zoomCola = {
  linkDistance: 125
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

function updateGraph1 () {
  initGraphStats('A');
  // enable selection
  $('#ga-name').prop('disabled', false);
  $('#ga-name').autocomplete({
    source: function (term, callback) {
      return autocompleteName('A', term, callback);
    },
    /* Change collisiont to 'fit' to prevent the list from being off screen if
     * it would fit. */
    position: {my: 'left top', at: 'left bottom', collision: 'none'}
  });
  // clear out the person name element
  document.getElementById('ga-name').value = '';
  document.getElementById('gb-name').value = '';
  emptyCliqueGraph(entityAlign.graph1);
  $('#graph1').empty();
  $('#info1').empty();
  entityAlign.graph1 = null;
}

function updateGraph2 () {
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
  } else {
    selectedDataset = $('#graph2-selector').val();
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
      if (graphIndexString === 'A' && !entityAlign.initialFocus) {
        entityAlign.initialFocus = true;
        $('#ga-name')[0].focus();
      }
    }
  });
}

/* Fetch the matching node names for a given graph.
 *
 * @param {string} graphIndex: 'A' or 'B'.
 * @param {object} term: an object with a term element with the string to
 *                       search for.
 * @param {function} callback: a function that takes an ordered array of
 *                             strings.
 */
function autocompleteName (graphIndex, term, callback) {
  var selectedDataset;

  if (graphIndex === 'A') {
    selectedDataset = $('#graph1-selector').val();
  } else {
    selectedDataset = $('#graph2-selector').val();
  }
  var url = 'service/loadnodenames/' + entityAlign.host + '/' + entityAlign.graphsDatabase + '/' + selectedDataset;
  $.getJSON({url: url, data: {
    term: term.term,
    list: 30
  }}).done(function (data) {
    callback(data.names);
  }).error(function () {
    callback([]);
  });
}

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

/* Resize the info element if we aren't showing anything beneath it.
 *
 * @param infoElement: optional name of selector to place info element that is
 *                     shown when a node is selected.
 * @param linkInfoElement: optional name of selector to place link info element
 *                         that is shown when a link is selected.
 */
function resizeInfoElement (infoElement, linkInfoElement) {
  if (!linkInfoElement) {
    var bodyRect = $('body')[0].getBoundingClientRect();
    var infoRect = $(infoElement)[0].getBoundingClientRect();
    $(infoElement).css('height', (bodyRect.bottom - infoRect.top - 5) + 'px');
  }
}

/* Add nodes to the neighborhood of another node.  This is identical to
 * graph.addNeighborrhood or selectionInfo.expandNode, except that the
 * maximum number of neighbors is limited.  Repeated calls will gradually add
 * all neighbors.
 *
 * @param {object} graph: an object that contains {graph: the graph that
 *      contains the central node, view: the cola layout}.
 * @param {object} center: the central node.
 */
function addNeighborhood (graph, center) {
  'use strict';
  if (!center.limit && entityAlign.maxFirstHopNodes) {
    center.limit = entityAlign.maxFirstHopNodes;
  } else if (center.limit && entityAlign.nodesPerExpand) {
    center.limit += entityAlign.nodesPerExpand;
  }
  graph.graph.addNeighborhood(center);
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

  if (existing && existing.actionTimeout) {
    window.clearTimeout(existing.actionTimeout);
  }
  emptyCliqueGraph(existing);
  if (existing && existing.selectedDataset === selectedDataset &&
      existing.graphElement === graphElement &&
      existing.infoElement === infoElement &&
      existing.linkInfoElement === linkInfoElement) {
    existing.viewOptions.transform.splice(0, 6, 1, 0, 0, 1, 0, 0);
    existing.view.updateTransform();
    resizeInfoElement(infoElement, linkInfoElement);
    return existing;
  }
  if (existing) {
    if (existing.infoObserver) {
      existing.infoObserver.disconnect();
    }
  }
  $(graphElement).parent().children('a').show();

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

  graph.viewOptions = $.extend(
    {}, defaultCola, {
      model: graph.graph,
      el: graphElement,
      transform: []
    }
  );
  graph.viewOptions.transform.splice(0, 6, 1, 0, 0, 1, 0, 0);
  graph.view = new clique.default.view.Cola(graph.viewOptions);
  graph.view.mode = 'label';

  if (infoElement) {
    var SelectionInfo = clique.default.view.SelectionInfo;
    graph.info = new SelectionInfo({
      model: graph.view.selection,
      el: infoElement,
      graph: graph.graph
    });
    graph.info.render();
    resizeInfoElement(infoElement, linkInfoElement);
    graph.infoObserver = new MutationObserver(function (mutations) {
      if ($('img', infoElement).length) {
        return;
      }
      $('table tr', infoElement).each(function (idx) {
        if ($('td>strong', this).text() === 'profile_image') {
          var row = $(this);
          var url = $('td:last', this).text();
          $('td:last', this).empty().append(
            $('<img class="profile_image">').attr('src', url).on(
              'error', function () {
                row.remove();
              }));
        }
      });
    });
    graph.infoObserver.observe($(infoElement)[0], {childList: true});
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
    var elem = evt.$trigger.closest('.node')[0];
    var nodekey = d3.select(elem).datum().key;
    var nodes;
    if (graph.view.selected.has(nodekey)) {
      nodes = Array.from(graph.view.selected);
    } else {
      nodes = [nodekey];
    }
    var func = {
      hide: SelectionInfo.hideNode,
      expand: function (node) {
        addNeighborhood(graph, node);
      },
      center: function (node) {
        if (!node.limit) {
          addNeighborhood(graph, node);
        }
        var elemBounds = $(elem)[0].getBoundingClientRect();
        var svgBounds = $(elem).closest('svg')[0].getBoundingClientRect();
        graph.viewOptions.transform[4] += (
            svgBounds.right + svgBounds.left -
            elemBounds.right - elemBounds.left) / 2;
        graph.viewOptions.transform[5] += (
            svgBounds.bottom + svgBounds.top -
            elemBounds.bottom - elemBounds.top) / 2;
        graph.view.updateTransform();
        if (graph.centerOnEntity) {
          graph.centerOnEntity.call(this, node);
        }
      }
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
      }},
      center: {name: 'Center on Entity', callback: contextCallback}
    }
  });

  if (entityAlign.maxGraphActionTime) {
    graph.view.cola.on('start', function () {
      if (graph.actionTimeout) {
        window.clearTimeout(graph.actionTimeout);
      }
      graph.actionTimeout = window.setTimeout(function () {
        graph.view.cola.stop();
        console.log('graph action stopped');
      }, entityAlign.maxGraphActionTime);
    });
    graph.view.cola.on('end', function () {
      if (graph.actionTimeout) {
        window.clearTimeout(graph.actionTimeout);
      }
      graph.actionTimeout = null;
    });
  }
  return graph;
}

// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function initGraph1WithClique () {
  'use strict';
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
      addNeighborhood(graph, center);
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
      addNeighborhood(graph, center);
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

/* Handle the zoom button on our clique graph.  This mostly toggles some CSS.
 *
 * @param {object} evt: jquyery event that triggered this call.
 */
function zoomClique (evt) {
  var elem = $(evt.target).closest('.clique');
  var graph = entityAlign[$('#graph1', elem).length ? 'graph1' : 'graph2'];
  if (!graph) {
    return;
  }
  var zoomIn = !elem.hasClass('enlarged');
  var origW = $(graph.graphElement).width();
  var origH = $(graph.graphElement).height();
  elem.toggleClass('enlarged', zoomIn);
  $(graph.infoElement).toggleClass('enlarged', zoomIn);
  var newW = $(graph.graphElement).width();
  var newH = $(graph.graphElement).height();
  if (zoomIn) {
    $(graph.infoElement).css('height', '');
    $.extend(graph.viewOptions, zoomCola);
  } else { /* zoom out */
    resizeInfoElement(graph.infoElement, graph.linkInfoElement);
    $.extend(graph.viewOptions, unzoomCola);
  }
  graph.viewOptions.transform[4] += (newW - origW) / 2;
  graph.viewOptions.transform[5] += (newH - origH) / 2;
  graph.view.updateTransform();
  graph.view.cola.start();
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

    // set up the keystroke and mouse logger
    initializeLoggingFramework(defaults);

    fillLineUpSelector();
    // set a watcher on the dataset selector so datasets are filled in
    // automatically when the user selects it via UI selector elements.

    d3.select('#graph1-selector').on('change', updateGraph1);
    d3.select('#graph2-selector').on('change', updateGraph2);
    d3.select('#lineup-selector')
            .on('change', handleLineUpSelectorChange);
    d3.select('#onehop-button')
            .on('click', ExploreLocalGraphAregion);
    d3.select('#accept-button')
            .on('click', acceptListedPairing);
    d3.select('#graph1-homepage')
            .on('click', openHompageGraph1);
    d3.select('#graph2-homepage')
            .on('click', openHompageGraph2);

    setGraphDatasets(defaults.graph1Datasets || ['twitter'], '#graph1-selector', '#graph1-selector-one');
    setGraphDatasets(defaults.graph2Datasets || ['instagram'], '#graph2-selector', '#graph2-selector-one');
    updateGraph1();
    updateGraph2();
  });

  d3.select('#publish-parings-button')
            .on('click', publishPairLists);

  $('.clique>a').on('click', zoomClique);

  // declare a Bootstrap table to display pairings made by the analyst

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

// *** initialization.

window.onload = function () {
  firstTimeInitialize();    // Fill out the dataset selectors with graph datasets that we can choose from
  $('#ga-name').keyup(function (event) {
    if (event.which === 13) {
      $('.ui-menu-item').closest('.ui-autocomplete').hide();
      ExploreLocalGraphAregion();
    }
  });
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
  var graphA = $('#graph1-selector').val();
  var graphB = $('#graph2-selector').val();

  // setup the machinery to allow the interface to be used to introspect inside a single dataset or compare between the datasets
  // a displaymode selector (currently disabled) can be set to determine which mode the UI shuld be in.

  var displaymode = 'compare networks';
  d3.json('service/lineupdatasetdescription/' + displaymode, function (ignore_err, desc) {
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

/* After an entity is selected to be centered, set the control to that entity's
 * name, and update the graph.
 *
 * @param {object} entity: the node object to center on.
 */
function centerOnGraph1Entity (entity) {
  if (!entity.getData || !entity.getData('name')) {
    return;
  }
  ExploreLocalGraphAregion('set', entity.getData('name'));
}

function ExploreLocalGraphAregion (action, centralHandle) {
  if (action === 'set') {
    $('#ga-name').val(centralHandle);
  } else {
    centralHandle = $('#ga-name').val();
    // console.log('doing one hop around', centralHandle)
    initGraph1WithClique();
    entityAlign.graph1.centerOnEntity = centerOnGraph1Entity;
  }

  InitializeLineUpAroundEntity(centralHandle);
  // clear possible leftover state from a previous search
  document.getElementById('gb-name').value = '';
  emptyCliqueGraph(entityAlign.graph2);
}

/* After an entity is selected to be centered, set the control to that entity's
 * name.  Select the entity in lineup if present.
 *
 * @param {object} entity: the node object to center on.
 */
function centerOnGraph2Entity (entity) {
  if (!entity.getData || !entity.getData('name')) {
    return;
  }
  var handle = entity.getData('name');
  $('#gb-name').val(handle);
  if (lineup && lineup.main && lineup.main.data &&
      lineup.main.data.clearSelection && lineup.main.data.data &&
      lineup.main.data.data.length) {
    lineup.main.data.clearSelection();
    var newSelection;
    for (var i = 0; i < lineup.main.data.data.length; i += 1) {
      if (handle === lineup.main.data.data[i].entity) {
        newSelection = i;
        break;
      }
    }
    if (newSelection !== undefined) {
      entityAlign.skipLineupSelection = newSelection;
      lineup.main.data.setSelection([newSelection]);
    }
  }
}

function ExploreLocalGraphBregion (handle) {
  // set the UI to show who we are exploring around in graphB
  logSelectLineUpEntry();
  $('#gb-name').val(handle);
  initGraph2WithClique();
  entityAlign.graph2.centerOnEntity = centerOnGraph2Entity;
}

/* When a lineup row is selected, change what graph B is showing.
 *
 * @param row: the selected lineup row.
 */
function selectEntityFromLineup (row) {
  if (entityAlign.skipLineupSelection !== undefined) {
    delete entityAlign.skipLineupSelection;
    return;
  }
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
