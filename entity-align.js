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
// startup time from a defaults.json file. 

entityAlign.graphsDatabase= null
entityAlign.showMatchesEnabled = false


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
    updateGraph1_d3()
}


function updateGraph2() {
    updateGraph2_d3()
    //updateGraph2_vega()
}




function updateGraph2_vega() {
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

            var width = 500
            var height = 500

            parseVegaSpec("#graph2","force.json",graph)
        }
         
    });
}

 // bind data  with the vega spec and render in the element passed as a parameter.  This routine reads the
 // vega spec and connects to dynamic data. It can be repeatedly called during execution to change the rendering
 // driven by vega

    function parseVegaSpec(element, spec, dynamicData) {
            console.log("parsing vega spec"); 
       vg.parse.spec(spec, function(chart) { 
            vegaview = chart({
                    el: element, 
                    data: {links: dynamicData.links, nodes: dynamicData.nodes}
                })
                .update()
                .on("mouseover", function(event, item) {
                        console.log('item',item.mark.marktype,' detected')
                        if (item.mark.marktype === 'symbol') {
                            vegaview.update({
                                props: 'hover0',
                                items: item.cousin(1)
                            });
                        } 
                })
                .on("mouseout", function(event, item) {
                        if (item.mark.marktype === 'symbol') {
                            vegaview.update({
                                props: 'update0',
                                items: item.cousin(1)
                            });
                        }
                 })
                 });
   }



function updateGraph1_d3() {
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


    d3.select("#nodes1").selectAll("*").remove();
    d3.select("#links1").selectAll("*").remove();

    // Get the name of the graph dataset to render
    var graphPathname = d3.select("#graph1-selector").node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;

     var logText = "dataset1 select: start="+graphPathname;
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
            $('#graph1-drawing-canvas').remove();

            svg = d3.select("#graph1").append('svg')
                .attr("id","graph1-drawing-canvas")
                .attr("width",800)
                .attr("height",800)


            link = svg.selectAll(".link")
                .data(graph.edges)
                .enter()
                .append("line")
                .classed("link", true)
                .style("stroke-width", 2.0);


            node = svg.selectAll(".node")
                .data(graph.nodes, function (d) { return d.name; })
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
                        .style("fill", function (d) {
                            return color(1);
                        });


                    enter.call(entityAlign.force2.drag)
                        .append("title")
                        .text(function (d) {
                            return d.name || "(no username)";
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

                    entityAlign.force1.nodes(graph.nodes)
                        .links(graph.edges)
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
               entityAlign.force1.linkDistance(100);
            }
            entityAlign.force1.nodes(graph.nodes)
                .links(graph.edges)
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
    });
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
            .scaleExtent([1, 10])
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


                    enter.append("title")
                        //.call(entityAlign.force2.drag)
                        .text(function (d) {
                            return d.name || "(no username)";
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

   // set a watcher on the dataset selector so the query options are filled in
        // automatically when a dataset is selected.
        d3.select("#graph1-selector")
            .on("change", updateGraph1);
        d3.select("#graph2-selector")
            .on("change", updateGraph2); 

        d3.select("#align-button")
            .on("click", runGraphMatching);
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
}



window.onload = function ()  {
    firstTimeInitialize();
    // Fill out the dataset selectors with graph datasets that we can choose from  

};


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

// change the stagus of the global show matches 
function toggleShowMatches() {

}


function runGraphMatching() {
    console.log("do graph matching")
}

