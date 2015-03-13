/*jslint browser:true, unparam:true */
/*globals $, console, d3, tangelo */

var color = null;
var force = null;
var graph = null;
var svg = null;
var width = 0;
var height = 0;
var transition_time;
var translate = [0, 0];

var entityAlign = {};
entityAlign.startDate = null;
entityAlign.endDate = null;
entityAlign.center = null;
entityAlign.degree = null;
entityAlign.history_length = null;
entityAlign.host = null;
entityAlign.ac = null;
entityAlign.textmode = true;
entityAlign.lastResponseLength = 0;

//should user click of node make this node the new center?
entityAlign.clickCausesFollow = false;

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
entityAlign.graphsCollection = null


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
        entityAlign.ac.logUserActivity("hover over entity: "+d.tweet, "hover", entityAlign.ac.WF_EXPLORE);
     
}

function loggedDragVisitToEntry(d) {
        //console.log("mouseover of entry for ",d.user)
        entityAlign.ac.logUserActivity("drag entity: "+d.tweet, "hover", entityAlign.ac.WF_EXPLORE);
}



function initializeQueryControls() {
    // Fill out the dataset selectors with graph datasets that we can choose from  
    fillDatassetList('#graph1-selector')
    fillDatassetList('#graph2-selector')
}





function updateGraph1() {
    "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - updateGraph 1 display executed');
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

     var logText = "dataset select: start="+graphPathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign - '+logText);

    $.ajax({
        // generalized collection definition
        url: "service/path2graph/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + entityAlign.graphsCollection,
        data: data,
        dataType: "json",
        success: function (response) {
            var angle,
                enter,
                link,
                map,
                newidx,
                node,
                tau;


            if (response.error || response.result.length === 0) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)

            transition_time = 600;

            link = svg.select("g#links1")
                .selectAll(".link")
                .data(graph.edges, function (d) {
                    return d.id;
                });

            link.enter().append("line")
                .classed("link", true)
                .style("opacity", 0.0)
                .style("stroke-width", 0.0)
                .transition()
                .duration(transition_time)
                .style("opacity", 0.6)
                .style("stroke","grey")
                .style("stroke-width", 1.0);

            link.exit()
                .transition()
                .duration(transition_time)
                .style("opacity", 0.0)
                .style("stroke-width", 0.0)
                .remove();

            node = svg.select("g#nodes1")
                .selectAll(".node")
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
                            centerOnClickedGraphNode(d.tweet);
                        });

                    enter.transition()
                        .duration(transition_time)
                        .attr("r", 12)
                        .style("opacity", 1.0)
                        .style("fill", function (d) {
                            return color(d.distance);
                        });


                    enter.call(force1.drag)
                        .append("title")
                        .text(function (d) {
                            return d.tweet || "(no username)";
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

                    force1.nodes(graph.nodes)
                        .links(graph.edges)
                        .start();

                    force1.on("tick", function () {
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
                        centerOnClickedGraphNode(d.tweet);
                    })

                    .datum(function (d) {
                        // Adjoin the bounding box to the element's bound data.
                        d.bbox = this.getBBox();
                        return d;
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

                force1.on("tick", function () {
                    link.attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });

                    node.attr("transform", function (d) {
                        return "translate(" + d.x + ", " + d.y + ")";
                    });
                });
               force1.linkDistance(100);
            }
            force1.nodes(graph.nodes)
                .links(graph.edges)
                .start();

        
            enter.call(force1.drag);

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



function updateGraph1_saved() {
    "use strict";
     //entityAlign.ac.logUserActivity("Update Rendering.", "render", entityAlign.ac.WF_SEARCH);
     entityAlign.ac.logSystemActivity('entityAlign - updateGraph display executed');
    var center,
        data,
        end_date,
        hops,
        change_button,
        start_date,
        update;

    d3.select("#nodes1").selectAll("*").remove();
    d3.select("#links1").selectAll("*").remove();

    // Get JavaScript Date objects for the start and end dates.
    var graphPathname = d3.select("#graph1-selector").node();
    var selectedDataset = graphPathname.options[graphPathname.selectedIndex].text;

     var logText = "dataset select: start="+graphPathname;
     entityAlign.ac.logSystemActivity('Kitware entityAlign Mention -'+logText);

    $.ajax({
        // generalized collection definition
        url: "service/path2graph/" + entityAlign.host + "/"+ entityAlign.graphsDatabase + "/" + entityAlign.graphsCollection,
        data: data,
        dataType: "json",
        success: function (response) {
            var angle,
                enter,
                link,
                map,
                newidx,
                node,
                tau;


            if (response.error || response.result.length === 0) {
                console.log("error: " + response.error);
                return;
            }
            console.log('data returned:',response.result)

            transition_time = 600;

            link = svg.select("g#links1")
                .selectAll(".link")
                .data(graph.edges, function (d) {
                    return d.id;
                });

            link.enter().append("line")
                .classed("link", true)
                .style("opacity", 0.0)
                .style("stroke-width", 0.0)
                .transition()
                .duration(transition_time)
                .style("opacity", 0.6)
                .style("stroke","grey")
                .style("stroke-width", 1.0);

            link.exit()
                .transition()
                .duration(transition_time)
                .style("opacity", 0.0)
                .style("stroke-width", 0.0)
                .remove();

            node = svg.select("g#nodes1")
                .selectAll(".node")
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
                            centerOnClickedGraphNode(d.tweet);
                        });

                    enter.transition()
                        .duration(transition_time)
                        .attr("r", 12)
                        .style("opacity", 1.0)
                        .style("fill", function (d) {
                            return color(d.distance);
                        });


                    enter.call(force1.drag)
                        .append("title")
                        .text(function (d) {
                            return d.tweet || "(no username)";
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

                    force1.nodes(graph.nodes)
                        .links(graph.edges)
                        .start();

                    force1.on("tick", function () {
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
                        centerOnClickedGraphNode(d.tweet);
                    })

                    .datum(function (d) {
                        // Adjoin the bounding box to the element's bound data.
                        d.bbox = this.getBBox();
                        return d;
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

                force1.on("tick", function () {
                    link.attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });

                    node.attr("transform", function (d) {
                        return "translate(" + d.x + ", " + d.y + ")";
                    });
                });
               force1.linkDistance(100);
            }
            force1.nodes(graph.nodes)
                .links(graph.edges)
                .start();

        
            enter.call(force1.drag);

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

function advanceTimer() {
    "use strict";

    var advance;

    advance = new Date(entityAlign.startDate.datepicker("getDate").getTime() + 86400e3);
    entityAlign.startDate.datepicker("setDate", advance);

    advance = new Date(entityAlign.endDate.datepicker("getDate").getTime() + 86400e3);
    entityAlign.endDate.datepicker("setDate", advance);

    // log action
    entityAlign.ac.logUserActivity("timer control updated", "date/time change", entityAlign.ac.WF_GETDATA);
    updateGraph();
}

var timeout = null;
function toggleAnimation() {
    "use strict";

    var anim, update;
    var graphAdjustTime, baseDelayTime;
    // log action

    anim = d3.select("#animate");
    update = d3.select("#update");

    if (anim.text() === "Animate") {
        anim.text("Stop animation")
            .classed("btn-success", false)
            .classed("btn-warning", true);
        update.attr("disabled", true);
        entityAlign.ac.logUserActivity("user enabled animation", "animation", entityAlign.ac.WF_EXPLORE);

        // slowed down the animation from 1.5x to 5.0x  and adding a component to delay for larger graphs
        baseDelayTime = transition_time *5.0;
        graphAdjustTime = (entityAlign.lastResponseLength * 20);
        if  (isNaN(graphAdjustTime)) { graphAdjustTime = 0; }
        //console.log(graphAdjustTime)

        timeout = setInterval(advanceTimer, parseInt(baseDelayTime + graphAdjustTime));
    } else {
        anim.text("Animate")
            .classed("btn-success", true)
            .classed("brn-warning", false);
        update.attr("disabled", null);
        entityAlign.ac.logUserActivity("user disabled animation", "animation", entityAlign.ac.WF_EXPLORE);

        clearInterval(timeout);
    }
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

        width = $(window).width();
        height = $(window).height();

        // 3/2014: changed link strength down from charge(-500), link(100) to charge(-2000)
        // to reduce the node overlap but still allow some node wandering animation without being too stiff

        force1 = d3.layout.force()
            .charge(-2000)
            .linkDistance(75)
            .gravity(0.2)
            .friction(0.6)
            .size([width/2, height/2]);

        force2 = d3.layout.force()
            .charge(-2000)
            .linkDistance(75)
            .gravity(0.2)
            .friction(0.6)
            .size([width/2, height/2]);

        color = d3.scale.category20();
        //color = entityAlignDistanceFunction;



        // respond to the allow click to cause follow operation being clicked
       d3.select("#clickfollow")
            .on("click", function () {
                entityAlign.clickCausesFollow = !entityAlign.clickCausesFollow;
                //console.log("clickfollow=",entityAlign.clickCausesFollow);
                entityAlign.ac.logUserActivity("user toggled click follow mode", "clickfollow", entityAlign.ac.WF_EXPLORE);
                // reload the graph with nodes that have or don't have events attached on them
                updateGraph();
            });   

        // block the contextmenu from coming up (often attached to right clicks). Since many 
        // of the right clicks will be on the graph, this has to be at the document level so newly
        // added graph nodes are all covered by this handler.

        $(document).bind('contextmenu', function(e){
            e.preventDefault();
            return false;
            });

        updateGraph();
        fillActiveEntitiesList();

    });
}




window.onload = function ()  {
    firstTimeInitialize();
};


function fillDatassetList(element) {
  d3.select(element).selectAll("a").remove();
        d3.json("service/listdatasets/"+ entityAlign.host + "/" + entityAlign.graphsDatabase, function (error, entities) {
            console.log(entities,"\n");
            // save in a temporary list so we can refer back during a click event
            d3.select(element).selectAll("option")
            .data(list.result)
            .enter().append("option")
            .text(function (d) { return d.name; });
        });
}
