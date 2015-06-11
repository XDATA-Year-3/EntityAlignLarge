/*jslint browser:true, unparam:true */
/*globals $, console, d3, tangelo */


var color = null;

var graph = null;
var svg = null;
var width = 0;
var height = 0;
var transition_time;
var translate = [0, 0];

var entityAlign = {};
entityAlign.force1 = null;
entityAlign.force2 = null;
entityAlign.host = null;
entityAlign.ac = null;
entityAlign.textmode = false;


//var LoggingLocation = "http://xd-draper.xdata.data-tactics-corp.com:1337"
var LoggingLocation = "http://10.1.90.46:1337/";
// testmode = false means logging is on
entityAlign.testMode = true;
entityAlign.echoLogsToConsole = false;
entityAlign.ac = new activityLogger().echo(entityAlign.echoLogsToConsole).testing(entityAlign.testMode);
ac = entityAlign.ac;
entityAlign.ac.registerActivityLogger(LoggingLocation, "Kitware_Entity_Alignment", "0.8");

entityAlign.dayColor = d3.scale.category10();
entityAlign.monthColor = d3.scale.category20();
entityAlign.dayName = d3.time.format("%a");
entityAlign.monthName = d3.time.format("%b");
entityAlign.dateformat = d3.time.format("%a %b %e, %Y (%H:%M:%S)");

// add globals for current collections to use.  Allows collection to be initialized at
// startup time from a defaults.json file.   A pointer to the global datastructures for each graph, are initialized empty as well.

entityAlign.graphsDatabase= null
entityAlign.showMatchesEnabled = false
entityAlign.graphA = null
entityAlign.graphB = null

entityAlign.graphA_dataset = null
entityAlign.graphB_dataset = null
entityAlign.graphAnodeNames = null
entityAlign.graphBnodeNames = null

// a backup copy of the files as read from the datastore is kept to send to the SGM algortihm.  The regular .graphA and .graphB entries 
// are operated-on by D3, so the datastructures don't work passed back to networkX directly anymore.  So a backup is kepts and this pristine
// copy is used to initialize the SGM algorithm executed as a tangelo service.

entityAlign.SavedGraphA = null
entityAlign.SavedGraphB = null

// there is a global array corresponding to the current matches known between the two loaded graphs.  The matches are an array of JSON objects, each with a 
// "ga" and "gb" attribute, whose corresponding values are integers that match the node IDs. 
entityAlign.currentMatches = []
entityAlign.pairings = []

// how far to go out on the default rendering of a local neightborhood
entityAlign.numberHops = 2

entityAlign.cliqueA = null
entityAlign.cliqueB = null


entityAlign.monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec"
];

entityAlign.dayNames = [
    "Sun",
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat"
];

// make alternating blue and tan colors gradually fading to background to add color gradient to network
// see http://en.wikipedia.org/wiki/Web_colors
entityAlign.nodeColorArray = [
        "#ff2f0e","#1f77b4","#cd853f","#1e90b4", "#f5deb3","#add8e6","#fff8dc",
        "#b0e0e6","#faf0e6","#e0ffff","#fff5e0","#f0fff0"
];



function stringifyDate(d) {
    "use strict";

    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}

function displayDate(d) {
    "use strict";

    return entityAlign.monthNames[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
}



// This function is attached to the hover event for displayed d3 entities.  This means each rendered tweet has
// a logger installed so if a hover event occurs, a log of the user's visit to this entity is sent to the activity log

function loggedVisitToEntry(d) {
        //console.log("mouseover of entry for ",d.user)
        //entityAlign.ac.logUserActivity("hover over entity: "+d.tweet, "hover", entityAlign.ac.WF_EXPLORE);
     
}

function loggedDragVisitToEntry(d) {
        //console.log("mouseover of entry for ",d.user)
        //entityAlign.ac.logUserActivity("drag entity: "+d.tweet, "hover", entityAlign.ac.WF_EXPLORE);
}



function updateGraph1() {
    //updateGraph1_d3()
    //initGraph1FromDatastore()
    loadNodeNames("A")
    initGraphStats("A")
    // clear out the person name element
    document.getElementById('ga-name').value = '';

}


function updateGraph2() {
    //initGraph2FromDatastore()
    // this rendering call below is the old style rendering, which doesn't update.  comment this out in favor of using
     //updateGraph2_d3_afterLoad() 
    //updateGraph2_d3()
    loadNodeNames("B")
    initGraphStats("B")
    // clear out the person name element
    document.getElementById('gb-name').value = '';
}


// define a key return function that makes sre nodes are matched up using their ID values.  Otherwise D3 might
// color the wrong nodes if the access order changes
function nodeKeyFunction(d) {
    return d.id
}



// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is 
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function   initGraphStats(graphIndexString)
{
 
  "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - initialize graph A executed');
    var data

    // Get the name of the graph dataset to render
    if (graphIndexString == "A") {
        var graphPathname = d3.select("#graph1-selector").node();
        var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
        // save the current dataset name for the graph
        entityAlign.graphA_dataset = selectedDataset
    } else {
        var graphPathname = d3.select("#graph2-selector").node();
        var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
        // save the current dataset name for the graph
        entityAlign.graphB_dataset = selectedDataset        
    }
     var logText = "dataset " + graphIndexString + " select: start="+graphPathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);

    $.ajax({
        // generalized collection definition
        url: "service/loadgraphsummary/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset,
        data: data,
        dataType: "json",
        success: function (response) {

            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)
            if (graphIndexString == 'A') {
                d3.select("#ga-nodeCount").text(response.result.nodes.toString());
                d3.select("#ga-linkCount").text(response.result.links.toString());
            } else {
                d3.select("#gb-nodeCount").text(response.result.nodes.toString());
                d3.select("#gb-linkCount").text(response.result.links.toString());            }
        }

    });
}

// ----- start of autocomplete for users 

// do a non-blocking call to a python service that returns all the names in the graph.  Assign this to a global variable
function loadNodeNames(graphIndexString)
{

  // Get the name of the graph dataset to render
    if (graphIndexString == "A") {
        var graphPathname = d3.select("#graph1-selector").node();
        var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;
    } else {
        var graphPathname = d3.select("#graph2-selector").node();
        var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;        
    }

    // non-blocking call to initialize this 
    var data
    $.ajax({
        url: "service/loadnodenames/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset,
        data: data,
        dataType: "json",
        success: function (response) {

            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)
            if (graphIndexString == 'A') {
                // copy the result into the array and enable name selection from the input field
                entityAlign.graphAnodeNames = response.result.nodes
                var inputfield = d3.select('#ga-name')
                inputfield.attr("disabled", null);
                updateUserList(response.result.nodes)
            } else {
                 entityAlign.graphBnodeNames = response.result.nodes
            }
        }
    });
}

$('#ga-name').autocomplete().keyup(function (evt) {
    console.log(evt)
    // respond to enter by starting a query
    if (evt.which === 13) {
        updateUserList(entityAlign.graphAnodeNames);
    }
});

// reset the user list on a new time range query
function resetUserList() {
    $('#ga-name').autocomplete({ source: [] });
}

// update the user list from a mongo response
function updateUserList(namelist) {

    resetUserList();

    // Update the user filter selection box
    // .slice(0, 10)
    $('#ga-name').autocomplete({ source: namelist});
}

// ------ end of autocomplete users 


// The InitGraph functions are called the first time a graph is loaded from the graph datastore.  The ajax call to load from the store
// is included here.  Globals variables are filled with the graph nodes and links.  No rendering is done in this method.  A method is 
// written for graph1 and graph2.  The only difference between the graph1 and graph2 methods is that they fill different global variables.

function   initGraph1FromDatastore()
{
 
  "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - initialize graph A executed');
    var center,
        data,
        end_date,
        hops,
        change_button,
        start_date,
        update;


    d3.select("#nodes1").selectAll("*").remove();
    d3.select("#links1").selectAll("*").remove();

    // Get the name of the graph dataset to render
    var graphPathname = d3.select("#graph1-selector").node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;

    var centralHandle  = document.getElementById('ga-name').value;
    console.log('doing one hop around',centralHandle)

    var logText = "dataset1 select: start="+graphPathname;
    entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);

     d3.json("service/loadkhop/"+ entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset+ "/" + centralHandle, function (err, response) {
        // host=None, db=None, coll=None, center=None, radius=None, deleted=json.dumps(False)):
        //url: "service/loadonehop/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset+ "/" + centralHandle,
        //data: data,
        //dataType: "json",
        //success: function (response) {
            var angle,
                enter,
                svg,
                svg2,
                link,
                map,
                newidx,
                node,
                tau;

            console.log('data returned:',response)
            entityAlign.graphA = {}
            // KLUDGE *** had to add shift() here because the graph stayed at 0,0 without this.  No edges show visibly now, but the nodes display
            entityAlign.graphA.edges = jQuery.extend(true, {}, response.links);
            entityAlign.graphA.nodes = jQuery.extend(true, {}, response.nodes);

            // save a copy to send to the tangelo service. D3 will change the original around, so lets 
            // clone the object before it is changed
            entityAlign.SavedGraphA = {}
            // KLUDGE *** had to add shift() here because the graph stayed at 0,0 without this.  No edges show visibly now, but the nodes display
            entityAlign.SavedGraphA.edges   = jQuery.extend(true, {}, response.links);
            entityAlign.SavedGraphA.nodes = jQuery.extend(true, {}, response.nodes);

            //updateGraph1_d3_afterLoad();
        });

}


function   initGraph2FromDatastore(centralHandle)
{
 
  "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - initialize graph A executed');
    var center,
        data,
        end_date,
        hops,
        change_button,
        start_date,
        update;


    d3.select("#nodes2").selectAll("*").remove();
    d3.select("#links2").selectAll("*").remove();

    // Get the name of the graph dataset to render
    var graphPathname = d3.select("#graph2-selector").node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;

     var logText = "dataset2 select: start="+graphPathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);

    $.ajax({
        // generalized collection definition
        url: "service/loadonehop/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset+ "/" + centralHandle,
        data: data,
        dataType: "json",
        success: function (response) {
            var angle,
                enter,
                svg,
                svg2,
                link,
                map,
                newidx,
                node,
                tau;


            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)

            // make a copy that will support the D3-based visualization
            entityAlign.graphB = {}
            entityAlign.graphB.edges = response.result.links.shift()
            entityAlign.graphB.nodes = response.result.nodes 

            // save a copy to send to the tangelo service. D3 will change the original around, so lets 
            // clone the object before it is changed
            entityAlign.SavedGraphB = {}
            entityAlign.SavedGraphB.edges   = jQuery.extend(true, {}, response.result.links.shift());
            entityAlign.SavedGraphB.nodes = jQuery.extend(true, {}, response.result.nodes);
            //updateGraph2_d3_afterLoad();
        }

    });
}

// The update_afterLoad routines are called whenever the graph should be visually refreshed from new state in the global variables:
// entityAlign.graphA and .graphB.   

function  updateGraph1_d3_afterLoad() {

    var enter;
    transition_time = 600;

            // remove any previous graph
            $('#graph1-drawing-canvas').remove();

            svg = d3.select("#graph1").append('svg')
                .attr("id","graph1-drawing-canvas")
                .attr("width",400)
                .attr("height",800)


            link = svg.selectAll(".link")
                .data(entityAlign.graphA.edges)
                .enter()
                .append("line")
                .classed("link", true)
                .style("stroke-width", 2.0);


            node = svg.selectAll(".node")
                .data(entityAlign.graphA.nodes, nodeKeyFunction)
                .on("mouseover", function(d) {
                        loggedVisitToEntry(d);
                });

            // support two different modes, where circular nodes are drawn for each entity or for where the
            // sender name is used inside a textbox. if entityAlign.textmode = true, then render text

            if (!entityAlign.textmode) {
                    enter = node.enter().append("circle")
                        .classed("node", true)
                        .attr("r", 5)
                        .style("opacity", 0.0)
                        .style("fill", "red")
                        .on("click", function(d) {
                            loggedVisitToEntry(d);
                            //centerOnClickedGraphNode(d.tweet);
                        });


                    enter.transition()
                        .duration(transition_time)
                        .attr("r", 12)
                        .style("opacity", 1.0)
                        .style("fill", 
                            function (d) {if (d.matched) {return "DarkRed"} else {return color(1)};}
                        );

                    enter.call(entityAlign.force1.drag)
                        .append("title")
                        .text(function (d) {
                            var returntext = ""
                            for (var attrib in d) {
                                // mask away the display of attributes not associated with the network.  Hide the D3 specific
                                // position and velocity stuff
                                if (!_.contains(['data','x','y','px','py'],attrib)) {
                                    returntext = returntext + attrib+":"+d[attrib]+"\n" 
                                }
                            }
                            return returntext;
                        })
                        .on("mouseover", function(d) {
                        loggedDragVisitToEntry(d);
                        });

                    // adjust the color according to the matched state. Make matched be dark red, otherwise pass the default color.
                    // should amend this to use the entity distance color, but the datasets don't currently 

                    node
                        .filter(function(d,i) { return d.id != 0})
                        .style("fill", function (d) {if (d.matched>-1) {return "DarkRed"} else {return color(1)}});

                    node
                        .filter(function(d,i) { return d.id == 0})
                        .style("fill", "orange");

                    node.exit()
                        .transition()
                        .duration(transition_time)
                        .style("opacity", 0.0)
                        .attr("r", 0.0)
                        .style("fill", "black")
                        .remove();

                    entityAlign.force1.nodes(entityAlign.graphA.nodes)
                        .links(entityAlign.graphA.edges)
                        .start();

                    entityAlign.force1.on("tick", function () {
                        link.attr("x1", function (d) { return d.source.x; })
                            .attr("y1", function (d) { return d.source.y; })
                            .attr("x2", function (d) { return d.target.x; })
                            .attr("y2", function (d) { return d.target.y; });

                        node.attr("cx", function (d) { return d.x; })
                            .attr("cy", function (d) { return d.y; });
                    });
            } else {

                enter = node.enter()
                    .append("g")
                    .classed("node", true);

                enter.append("text")
                    .text(function (d) {
                        return d.tweet;
                    })

                    // use the default cursor so the text doesn't look editable
                    .style('cursor', 'default')

                    // enable click to recenter
                    .on("click", function(d) {
                        loggedVisitToEntry(d);
                    });


                enter.insert("rect", ":first-child")
                    .attr("width", function (d) { return d.bbox.width + 4; })
                    .attr("height", function (d) { return d.bbox.height + 4; })
                    .attr("y", function (d) { return d.bbox.y - 2; })
                    .attr("x", function (d) { return d.bbox.x - 2; })
                    .attr('rx', 4)
                    .attr('ry', 4)
                    .style("stroke", function (d) {
                        return color(d.distance);
                    })
                    .style("stroke-width", "2px")
                    .style("fill", "#e5e5e5")
                    .style("fill-opacity", 0.8);

                entityAlign.force1.on("tick", function () {
                    link.attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });

                    node.attr("transform", function (d) {
                        return "translate(" + d.x + ", " + d.y + ")";
                    });
                });
               entityAlign.force1.linkDistance(100);
            }
            entityAlign.force1.nodes(entityAlign.graphA.nodes)
                .links(entityAlign.graphA.edges)
                .start();

        
            enter.call(entityAlign.force1.drag);

            node.exit()
                .transition()
                .duration(transition_time)
                .style("opacity", 0.0)
                .attr("r", 0.0)
                .style("fill", "black")
                .remove();
}


// this is still not being called yet, because of the zoom/translate differences and missing nodes.  

function  updateGraph2_d3_afterLoad() {

    var enter;
    transition_time = 600;

            // remove any previous graph
            $('#graph2-drawing-canvas').remove();

            svg = d3.select("#graph2").append('svg')
                .attr("id","graph2-drawing-canvas")
                .attr("width",800)
                .attr("height",800)


            link = svg.selectAll(".link")
                .data(entityAlign.graphB.edges)
                .enter()
                .append("line")
                .classed("link", true)
                .style("stroke-width", 2.0);


            node = svg.selectAll(".node")
                .data(entityAlign.graphB.nodes, nodeKeyFunction)
                .on("mouseover", function(d) {
                        loggedVisitToEntry(d);
                });

            // support two different modes, where circular nodes are drawn for each entity or for where the
            // sender name is used inside a textbox. if entityAlign.textmode = true, then render text

            if (!entityAlign.textmode) {
                    enter = node.enter().append("circle")
                        .classed("node", true)
                        .attr("r", 5)
                        .style("opacity", 0.0)
                        .style("fill", "red")
                        .on("click", function(d) {
                            loggedVisitToEntry(d);
                            //centerOnClickedGraphNode(d.tweet);
                        });


                    enter.transition()
                        .duration(transition_time)
                        .attr("r", 12)
                        .style("opacity", 1.0)
                        .style("fill", 
                            function (d) {if (d.matched) {return "DarkRed"} else {return color(1)};}
                        );

                    enter.call(entityAlign.force2.drag)
                        .append("title")
                        .text(function (d) {
                            var returntext = ""
                            for (var attrib in d) {
                                // mask away the display of attributes not associated with the network.  Hide the D3 specific
                                // position and velocity stuff
                                if (!_.contains(['data','x','y','px','py'],attrib)) {
                                    returntext = returntext + attrib+":"+d[attrib]+"\n" 
                                }
                            }
                            return returntext;
                        })
                        .on("mouseover", function(d) {
                        loggedDragVisitToEntry(d);
                        });

                    // adjust the color according to the matched state. Make matched be dark red, otherwise pass the default color.
                    // should amend this to use the entity distance color, but the datasets don't currently 

                    //node.style("fill", function (d) {if (d.matched) {return "DarkRed"} else {return color(1)}});

                    node.style("fill", function (d) {if (d.matched) {return "DarkRed"} else {return color(1)}});

                    node.exit()
                        .transition()
                        .duration(transition_time)
                        .style("opacity", 0.0)
                        .attr("r", 0.0)
                        .style("fill", "black")
                        .remove();

                    entityAlign.force2.nodes(entityAlign.graphB.nodes)
                        .links(entityAlign.graphB.edges)
                        .start();

                    entityAlign.force2.on("tick", function () {
                        link.attr("x1", function (d) { return d.source.x; })
                            .attr("y1", function (d) { return d.source.y; })
                            .attr("x2", function (d) { return d.target.x; })
                            .attr("y2", function (d) { return d.target.y; });

                        node.attr("cx", function (d) { return d.x; })
                            .attr("cy", function (d) { return d.y; });
                    });
            } else {

                enter = node.enter()
                    .append("g")
                    .classed("node", true);

                enter.append("text")
                    .text(function (d) {
                        return d.tweet;
                    })

                    // use the default cursor so the text doesn't look editable
                    .style('cursor', 'default')

                    // enable click to recenter
                    .on("click", function(d) {
                        loggedVisitToEntry(d);
                    });


                enter.insert("rect", ":first-child")
                    .attr("width", function (d) { return d.bbox.width + 4; })
                    .attr("height", function (d) { return d.bbox.height + 4; })
                    .attr("y", function (d) { return d.bbox.y - 2; })
                    .attr("x", function (d) { return d.bbox.x - 2; })
                    .attr('rx', 4)
                    .attr('ry', 4)
                    .style("stroke", function (d) {
                        return color(d.distance);
                    })
                    .style("stroke-width", "2px")
                    .style("fill", "#e5e5e5")
                    .style("fill-opacity", 0.8);

                entityAlign.force2.on("tick", function () {
                    link.attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });

                    node.attr("transform", function (d) {
                        return "translate(" + d.x + ", " + d.y + ")";
                    });
                });
               entityAlign.force2.linkDistance(100);
            }
            entityAlign.force2.nodes(entityAlign.graphB.nodes)
                .links(entityAlign.graphB.edges)
                .start();

        
            enter.call(entityAlign.force2.drag);

            node.exit()
                .transition()
                .duration(transition_time)
                .style("opacity", 0.0)
                .attr("r", 0.0)
                .style("fill", "black")
                .remove();
}


var drag = d3.behavior.drag()
    .origin(function(d) { return d; })
    .on("dragstart", dragstarted)
    .on("drag", dragged)
    .on("dragend", dragended);


function updateGraph2_d3() {
    "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - updateGraph 2 display executed');
    var center,
        data,
        end_date,
        hops,
        change_button,
        start_date,
        update;


    d3.select("#nodes2").selectAll("*").remove();
    d3.select("#links2").selectAll("*").remove();

    // Get the name of the graph dataset to render
    var graphPathname = d3.select("#graph2-selector").node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;

     var logText = "dataset2 select: start="+graphPathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);
     

    $.ajax({
        // generalized collection definition
        url: "service/loadgraph/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset,
        data: data,
        dataType: "json",
        success: function (response) {
            var angle,
                enter,
                svg,
                svg2,
                link,
                map,
                newidx,
                node,
                tau;


            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)
            graph = {}
            graph.edges = response.result.links
            graph.nodes = response.result.nodes

            transition_time = 600;

            // remove any previous graph
            $('#graph2-drawing-canvas').remove();

            var margin = {top: -5, right: -5, bottom: -5, left: -5},
            width = 820 - margin.left - margin.right,
            height = 820 - margin.top - margin.bottom;

        // adding logic for dragging & zooming

        var zoom = d3.behavior.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", zoomed);


        
        // added for drag & scale
        svg = d3.select("#graph2").append('svg')
            .attr("id","graph2-drawing-canvas")
            .attr("width",width + margin.left + margin.right)
            .attr("height",height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.right + ")")
            .call(zoom);

        var rect = svg.append("rect")
            .attr("width", width)
            .attr("height", height)
            .style("fill", "none")
            .style("pointer-events", "all");

        var container = svg.append("g");

   //For zooming the graph #2
        function zoomed() {
          container.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
        }

       
        // end of added for drag & scale

            link = container.selectAll(".link")
                .data(graph.edges)
                .enter()
                .append("line")
                .classed("link", true)
                .style("opacity",0.8)
                .style("color","red")
                .style("stroke-width", 2.0);



            node = container.selectAll(".node")
                .data(graph.nodes, function (d) { return d.name; })
                .on("mouseover", function(d) {
                        loggedVisitToEntry(d);
                });

            // support two different modes, where circular nodes are drawn for each entity or for where the
            // sender name is used inside a textbox. if entityAlign.textmode = true, then render text

            if (!entityAlign.textmode) {
                    enter = node.enter().append("circle")
                        .attr("r", 5)
                        .style("opacity", 0.0)
                        .style("fill", "orange")
                        .call(drag)
                        .on("click", function(d) {
                            loggedVisitToEntry(d);
                            //centerOnClickedGraphNode(d.tweet);
                        })


                    enter.transition()
                        .duration(transition_time)
                        .attr("r", 12)
                        .style("opacity", 1.0)
                        .style("fill", function (d) {
                            return color(2);
                        });

                    // add hover titles to the nodes.  the text is derived from the node attributes
                    enter.append("title")
                        //.call(entityAlign.force2.drag)
                        .text(function (d) {
                            var returntext = ""
                            // look through all the attributes in the node record and list them 
                            // in the textover field, except for the 'data' attribute, which is 
                            // currently a complex JSON object
                            for (var attrib in d) {
                                if (attrib != 'data') {
                                    returntext = returntext + attrib+":"+d[attrib]+"\n" 
                                }
                            }
                            return returntext;
                        })
                        .on("mouseover", function(d) {
                        loggedDragVisitToEntry(d);
                        });

                    node.exit()
                        .transition()
                        .duration(transition_time)
                        .style("opacity", 0.0)
                        .attr("r", 0.0)
                        .style("fill", "black")
                        .remove();

                    entityAlign.force2.nodes(graph.nodes)
                        .links(graph.edges)
                        .start();

                    entityAlign.force2.on("tick", function () {
                        link.attr("x1", function (d) { return d.source.x; })
                            .attr("y1", function (d) { return d.source.y; })
                            .attr("x2", function (d) { return d.target.x; })
                            .attr("y2", function (d) { return d.target.y; });

                        node.attr("cx", function (d) { return d.x; })
                            .attr("cy", function (d) { return d.y; });
                    });
            } else {

                enter = node.enter()
                    .append("g")
                    .classed("node", true)
                    .call(drag);

                enter.append("text")
                    .text(function (d) {
                        return d.tweet;
                    })

                    // use the default cursor so the text doesn't look editable
                    .style('cursor', 'default')

                    // enable click to recenter
                    .on("click", function(d) {
                        loggedVisitToEntry(d);
                    })


                enter.insert("rect", ":first-child")
                    .attr("width", function (d) { return d.bbox.width + 4; })
                    .attr("height", function (d) { return d.bbox.height + 4; })
                    .attr("y", function (d) { return d.bbox.y - 2; })
                    .attr("x", function (d) { return d.bbox.x - 2; })
                    .attr('rx', 4)
                    .attr('ry', 4)
                    .style("stroke", function (d) {
                        return color(d.distance);
                    })
                    .style("stroke-width", "2px")
                    .style("fill", "#e5e5e5")
                    .style("fill-opacity", 0.8);

                entityAlign.force2.on("tick", function () {
                    link.attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });

                    node.attr("transform", function (d) {
                        return "translate(" + d.x + ", " + d.y + ")";
                    });
                });
               entityAlign.force2.linkDistance(100);
            }
            entityAlign.force2.nodes(graph.nodes)
                .links(graph.edges)
                .start();

        
            enter.call(entityAlign.force2.drag);

            node.exit()
                .transition()
                .duration(transition_time)
                .style("opacity", 0.0)
                .attr("r", 0.0)
                .style("fill", "black")
                .remove();
        }
    });
}

// These three routines below handle dragging events so dragging can take place of zooming

function dragstarted(d) {
  d3.event.sourceEvent.stopPropagation();
  console.log("drag start")
  d3.select(this).classed("dragging", true);
}

function dragged(d) {
  d3.select(this).attr("cx", d.x = d3.event.x).attr("cy", d.y = d3.event.y);
}

function dragended(d) {
  d3.select(this).classed("dragging", false);
}


function entityAlignDistanceFunction( distance) {
        // make alternating blue and tan colors gradually fading to background to add color gradient to network
        // see http://en.wikipedia.org/wiki/Web_colors

        // for really far away distances, wrap the colors, avoid the red at the center.  This allows this algorithm to always
        // produce a cycle of acceptable colors
        if (distance > entityAlign.nodeColorArray.length-1)
                return entityAlign.nodeColorArray[(distance%(entityAlign.nodeColorArray.length-1))+1];
         else
                return entityAlign.nodeColorArray[distance];
}


function firstTimeInitialize() {
    "use strict";

    // make the panel open & close over data content
    //$('#control-panel').controlPanel();

    d3.json("defaults.json", function (err, defaults) {
        defaults = defaults || {};

        // read default data collection names from config file
        entityAlign.host = defaults.mongoHost || "localhost";
        entityAlign.graphsDatabase = defaults.graphsDatabase || "year3_graphs"
        console.log('set graphs database: ',entityAlign.graphsDatabase)

        fillDatassetList('#graph1-selector')
        fillDatassetList('#graph2-selector')
        fillSeedList('#seed-selector')

        width = $(window).width();
        height = $(window).height();

        // 3/2014: changed link strength down from charge(-500), link(100) to charge(-2000)
        // to reduce the node overlap but still allow some node wandering animation without being too stiff

        entityAlign.force1 = d3.layout.force()
            .charge(-200)
            .linkDistance(75)
            .gravity(0.2)
            .friction(0.6)
            .size([width/3, height/2]);

        entityAlign.force2 = d3.layout.force()
            .charge(-200)
            .linkDistance(75)
            .gravity(0.2)
            .friction(0.6)
            .size([width/3, height/2]);

        color = d3.scale.category20();
        //color = entityAlignDistanceFunction;

        fillLineUpSelector()
        // set a watcher on the dataset selector so datasets are filled in
        // automatically when the user selects it via UI selector elements. 

        d3.select("#graph1-selector")
            .on("change", updateGraph1);
        d3.select("#graph2-selector")
            .on("change", updateGraph2);
        d3.select("#lineup-selector")
            .on("change", handleLineUpSelectorChange);
        d3.select('#show-pairings')
            .on("click", showPairings);
        d3.select("#align-button")
            .on("click", runSeededGraphMatching);
        d3.select("#onehop-button")
            .on("click", ExploreLocalGraphAregion);
        d3.select("#accept-button")
            .on("click", acceptListedPairing);
        d3.select("#show-matches-toggle")
            .attr("disabled", true)
            .on("click",  function () { entityAlign.showMatchesEnabled = !entityAlign.showMatchesEnabled; 
                                        conole.log(entityAlign.showMatchesEnabled);
                                       });

        // block the contextmenu from coming up (often attached to right clicks). Since many 
        // of the right clicks will be on the graph, this has to be at the document level so newly
        // added graph nodes are all covered by this handler.

        $(document).bind('contextmenu', function(e){
            e.preventDefault();
            return false;
            });

    });


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


// use a python service to search the datastore and return a list of available networks to pick from.  This fills a GUI selector, so the user
// can see what datasets are available.

function fillDatassetList(element) {
  d3.select(element).selectAll("a").remove();
        d3.json("service/listdatasets/"+ entityAlign.host + "/" + entityAlign.graphsDatabase, function (error, entities) {
            console.log(entities,"\n");
            // save in a temporary list so we can refer back during a click event
            d3.select(element).selectAll("option")
            .data(entities.result)
            .enter().append("option")
            .text(function (d) { return d; });
        });
}

// use a python service to search the datastore and return a list of available seed arrays to pick from.  This fills a GUI selector, so the user
// can see what datasets are available.

function fillSeedList(element) {
  d3.select(element).selectAll("a").remove();
        d3.json("service/listseeds/"+ entityAlign.host + "/" + entityAlign.graphsDatabase, function (error, entities) {
            console.log(entities,"\n");
            // save in a temporary list so we can refer back during a click event
            d3.select(element).selectAll("option")
            .data(entities.result)
            .enter().append("option")
            .text(function (d) { return d; });
        });

}


// change the stagus of the global show matches 
function toggleShowMatches() {

}

// restore the graph to a state where there are no matches recorded for any nodes by deleting the matched properties on all nodes in the graphs.

function removeMatchingRecordsFromGraphs() {
    console.log('graphA:',entityAlign.graphA)
    for (node in entityAlign.graphA.nodes) {
        if (node.hasOwnProperty('matched')) {
            delete node.matched
        }
    }
    console.log('graphA after:',entityAlign.graphA)
    // repeat for graphB
    for (node in entityAlign.graphB.nodes) {
        if (node.matched != 'undefined') {
            delete node.matched
        }
    }
}

// this routine reads the dataset pointed to by the seed selector and reads the seeds out of the dataset using the "loadseeds" python service.  The seeds
// come across as an array of JSON objects.   It is assumed the seed objects have a "ga" and "gb" component. Once the data is read, it is loaded into a 
// currentMatches array, which may be augmented by the graph matching algorithm later.  The seeds function as the initial values in the matching array. 

function loadNewSeeds() {
    console.log("loading seeds");
    // re-initialize the matches to an empty set
    entityAlign.currentMatches = []
    removeMatchingRecordsFromGraphs()
    var pathname = d3.select("#seed-selector").node();
    var selectedDataset = pathname.options[pathname.selectedIndex].text;

     var logText = "seed select: "+pathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);

    $.ajax({
        // generalized collection definition
        url: "service/loadseeds/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + selectedDataset,
        dataType: "json",
        success: function (response) {

            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned: from seeds',response.result)
            for (seed in response.result.seeds) {
                //console.log( response.result.seeds[seed])
                entityAlign.currentMatches.push(response.result.seeds[seed])
            }
            // set the attributes in the graph nodes so color can show existing matches
            updateMatchingStatusInGraphs()
            updateGraph2_d3_afterLoad()
            // allow time for the layout of the first graph before doing the layout on the second.  This won't scale for large graphs,
            // but it works for our simple testcases.  
            setTimeout(function(){
                updateGraph1_d3_afterLoad()
            },1250);
            // this is turned off until we figure out why rendering graph2 confuses the layout of graph1

 
        }

    })
}

// this function is called after a new set of seeds are loaded.  Assuming there are graphs present, we traverse through the graphs and set
// the "matched" attribute to have the ID of the node in the opposing graph, which matches it. 

function updateMatchingStatusInGraphs() {
    clearMatchedStatusForGraph(entityAlign.graphA)
    clearMatchedStatusForGraph(entityAlign.graphB)
    for (match in  entityAlign.currentMatches) {
        // set matched attributes
        var match_record = entityAlign.currentMatches[match]
        //console.log('match',match,'match_record',match_record)
        var ga_index = match_record.ga
        var gb_index = match_record.gb
        //console.log('match',match,'ga',ga_index)
        var ga_node = entityAlign.graphA.nodes[ga_index]
        var gb_node = entityAlign.graphB.nodes[gb_index]
        ga_node.matched = match_record.gb
        gb_node.matched = match_record.ga
    }
}


function clearMatchedStatusForGraph(graph) {

}


function runSeededGraphMatching() {
    console.log("do graph matching")
    console.log(entityAlign.graphB,entityAlign.graphA)
    $.ajax({
        type: 'PUT',
        // generalized collection definition
        url: "service/jhu_seeded_graph_matching" ,
        // + "/" + entityAlign.currentMatches
        data: {
            graphAnodes: JSON.stringify(entityAlign.SavedGraphA.nodes),
            graphAedges: JSON.stringify(entityAlign.SavedGraphA.edges),    
            graphBnodes: JSON.stringify(entityAlign.SavedGraphB.nodes),         
            graphBedges: JSON.stringify(entityAlign.SavedGraphB.edges),
            seeds: JSON.stringify(entityAlign.currentMatches)
        },
        dataType: "json",
        success: function (response) {

            if (response.error ) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned: from SGM',response.result)
            entityAlign.currentMatches = []
            for (match in response.result.matches) {
                //console.log( response.result.seeds[seed])
                entityAlign.currentMatches.push(response.result.matches[match])
            }
            // set the attributes in the graph nodes so color can show existing matches
            updateMatchingStatusInGraphs()
            updateGraph2_d3_afterLoad()
            // allow time for the layout of the first graph before doing the layout on the second.  This won't scale for large graphs,
            // but it works for our simple testcases.       
            setTimeout(function(){
                updateGraph1_d3_afterLoad()
            },1250);
        }

    })
}

function InitializeLineUpAroundEntity(handle)
{
    //InitializeLineUpJS();
     var graphPathname = d3.select("#graph1-selector").node();
        var graphA = graphPathname.options[graphPathname.selectedIndex].text;
     var graphPathname = d3.select("#graph2-selector").node();
        var graphB = graphPathname.options[graphPathname.selectedIndex].text;

    //var displaymodeselector = d3.select("#lineup-selector").node();
     //   var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;

     var displaymode = 'compare networks'
    d3.json('service/lineupdatasetdescription/'+displaymode,  function (err, desc) {
        console.log('description:',desc)
        if (displaymode == 'compare networks') {
            console.log('comparing networks')
            d3.json('service/lineupdataset/'+ entityAlign.host + "/" + entityAlign.graphsDatabase + "/" +graphA+'/'+graphB+'/'+handle+'/'+displaymode,  function (err, dataset) {
                console.log('lineup loading description:',desc)
                console.log('lineup loading dataset for handle:',handle,dataset.result)
                loadDataImpl(name, desc, dataset.result);
                });
        } else {
            console.log('local network')
            d3.json("service/loadkhop/"+ entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + graphA+ "/" + handle, function (err, response) {
                var encodedEntityList = JSON.stringify(response.nodes)
                d3.json('service/lineupdataset_neighborhood/'+ entityAlign.host + "/" + entityAlign.graphsDatabase + "/" +graphA+'/'+handle+'/'+encodedEntityList+'/'+displaymode,  function (err, dataset) {
                    console.log('lineup loading description:',desc)
                    console.log('lineup loading dataset for handle:',handle,dataset.result)
                    loadDataImpl(name, desc, dataset.result);
                    });
            });
        }
    });
}



function ExploreLocalGraphAregion() {
    var centralHandle  = document.getElementById('ga-name').value;
    //console.log('doing one hop around',centralHandle)
    initGraph1FromDatastore();
    InitializeLineUpAroundEntity(centralHandle); 
}



function ExploreLocalGraphBregion(handle) {
    // set the UI to show who we are exploring around in graphB
    document.getElementById('gb-name').value = handle;
    initGraph2FromDatastore(handle);
}

// this function resets lineup to the appropriate view whenever the focus selector is changed
function handleLineUpSelectorChange() {
    var displaymodeselector = d3.select("#lineup-selector").node();
    var displaymode = displaymodeselector.options[displaymodeselector.selectedIndex].text;
    if (displaymode=='left network only') {
        ExploreLocalGraphAregion()
    }
    else if (displaymode=='right network only') {
        ExploreLocalGraphBregion()
    }
    else {
        ExploreLocalGraphAregion()
    }
}

// this function is called on initialization and it just fills a selector with the three options of 
// comparing datasets or focusing on the left or right one

// *** disable the lineup options until they work by having only one entry in the selector

function fillLineUpSelector() {
    d3.select('#lineup-selector').selectAll("option")
            .data(['compare networks','left network only','right network only'])
            .text(function (d) { return d; });
}


function acceptListedPairing() {

    var graphPathname = d3.select("#graph1-selector").node();
    var graphA = graphPathname.options[graphPathname.selectedIndex].text;
    var graphPathname = d3.select("#graph2-selector").node();
    var graphB = graphPathname.options[graphPathname.selectedIndex].text;
    var handleA  = document.getElementById('ga-name').value;
    var handleB  = document.getElementById('gb-name').value;

    newPairing = {'twitter' : handleA,'instagram':handleB}
    entityAlign.pairings.push(newPairing)
    console.log('new pairing: ',newPairing)

    // this is the pairing (seed) display table which is in a modal popover.  This is used to
    // draw a nice table using Bootstrap an jQuery


    // update the table
    $('#pairings-table').bootstrapTable('load', entityAlign.pairings);
}


function showPairings() {


}
