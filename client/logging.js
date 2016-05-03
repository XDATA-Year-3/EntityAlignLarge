 // incorporate Draper's user logging API so this app generates logs

    // send the message
function log(msg) {
    //msg = extend(defaultMsg, msg);
    ale2.log(msg);
}

function logCliqueNodeDrag() {
    console.log('drag detected')
    _.throttle( function () {
       var msg = {
                activity: 'alter',
                action: 'CLICK',
                elementId:  'UNK',
                elementType: 'treeview',
                elementGroup: 'clique_group',
                source: 'system',
                tags: ['render']
            };
            log(msg);
        }, 250);
}

function logCliqueRenderAction() {
    console.log('clique render action');
    var msg = {
                activity: 'alter',
                action: 'CLICK',
                elementId:  'UNK',
                elementType: 'treeview',
                elementGroup: 'clique_group',
                source: 'system',
                tags: ['render']
            };
            log(msg);
}

function  logExpandNodeAction(node) {
      var msg = {
                activity: 'add',
                action: 'CLICK',
                elementId:  'UNK',
                elementType: 'treeview',
                elementGroup: 'clique_group',
                source: 'user',
                tags: ['node','expand']
            };
            log(msg);
            console.log('expand node action')
}

// log the button when the user is satisfied with a pairings list and wants to 'publish this list'
function logPublishPairings() {
      var msg = {
                activity: 'perform',
                action: 'CLICK',
                elementId: 'publish-parings-button',
                elementType: 'button',
                elementGroup: 'pairings_group',
                source: 'user',
                tags: ['pairing','publish']
            };
            log(msg);
            console.log('pubish pairing logged')
}

function logOpenTwitterWindow() {
      var msg = {
                activity: 'SHOW',
                action: 'CLICK',
                elementId: 'graph1-graph2-homepage',
                elementType: 'button',
                elementGroup: 'system_group',
                source: 'system',
                tags: ['window','homepage']
            };
            log(msg);
            console.log('open twitter window logged')
}

function logOpenInstagramWindow() {
      var msg = {
                activity: 'SHOW',
                action: 'CLICK',
                elementId: 'graph1-graph2-homepage',
                elementType: 'button',
                elementGroup: 'system_group',
                source: 'system',
                tags: ['window','homepage']
            };
            log(msg);
            console.log('open instagram window logged')
}

function logSetupLineUp() {
    var msg = {
                activity: 'SHOW',
                action: 'CREATE',
                elementId: 'lugui-wrapper',
                elementType: 'DATAGRID',
                elementGroup: 'lineup_group',
                source: 'system',
                tags: ['lineup']
            };
            log(msg);
            console.log('lineupSetup')
}
// this is called when the user selects a particular row of LineUp for the graphB neighborhood
// to be explored

function logSelectLineUpEntry() {
    var msg = {
                activity: 'select',
                action: 'CLICK',
                elementId: 'lugui-wrapper',
                elementType: 'DATAGRID',
                elementGroup: 'lineup_group',
                source: 'user',
                tags: ['lineup']
            };
            log(msg);
    var msg = {
                activity: 'perform',
                action: 'CLICK',
                elementId: 'lugui-wrapper',
                elementType: 'DATAGRID',
                elementGroup: 'lineup_group',
                source: 'system',
                tags: ['lineup']
            };
            log(msg);        
}

function initializeLoggingFramework(defaults) {

     extend = function() {
            var i, key, len, object, objects, out, value;
            objects = 1 <= arguments.length ? slice.call(arguments, 0) : [];
            out = {};
            for (i = 0, len = objects.length; i < len; i++) {
                object = objects[i];
                for (key in object) {
                    value = object[key];
                    out[key] = value;
                }
            }
            return out;
        };

    var defaultMsg = {
            activity: null,
            action: null,
            elementId: '',
            elementType: '',
            elementGroup: '',
            elementSub: '',
            source: null,
            tags: [],
            meta: {}
        };
      
      // instantiate a logging client and set the server location     
     var ale2 = new userale(
            {
            loggingUrl: defaults.loggingUrl,
            toolName: 'resonant-entity-alignment',
            toolVersion: defaults.toolVersion,
            elementGroups: [
                'graph_A_group',
                'graph_B_group',
                'pairings_group',
                'clique_group',
                'lineup_group',
                'system_group'
            ],
            workerUrl: 'cache/userale-worker.js',
            debug: true,
            sendLogs: defaults.sendLogs
        });
     console.log('logger instantiated');

    // register the logging system
    window.ale2 = ale2;
    ale2.register();


    // **** graph A group ***************

    $('#graph1-selector')
        .mouseover(function () {
            var msg = {
                activity: 'inspect',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'inspect',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_A_group',

                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'OPEN_CLOSE',
                action: 'CLICK',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        });

 $('#ga-name')
        .mouseover(function () {
            var msg = {
                activity: 'alter',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'textbox',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','handle']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'alter',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'textbox',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','handle']
            };
            log(msg);
        })
        .keyup(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'alter',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'textbox',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','handle']
            };
            log(msg);
        });

 $('#onehop-button')
        .mouseover(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','explore']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','explore']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'select',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','explore']
            };
            log(msg);
        });

 $('#graph1-homepage')
        .mouseover(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'select',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_A_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        });       

    // **** graph B group ***************

   $('#graph2-selector')
        .mouseover(function () {
            var msg = {
                activity: 'inspect',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'inspect',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_B_group',

                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        })
        .click(function () {
            var msg = {
                activity: 'OPEN_CLOSE',
                action: 'CLICK',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'dropdownlist',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['grapha','dataset']
            };
            log(msg);
        });

    $('#accept-button')
        .mouseover(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['pairing']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['pairing']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'select',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['pairing','accept']
            };
            log(msg);
        });

$('#graph2-homepage')
        .mouseover(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'select',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'select',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['grapha','homepage']
            };
            log(msg);
        });       


        // ***** pairings_group *************

        // log when the pairings panel is opened
        $('#seed-panel').on('shown', function() {
        var msg = {
                activity: 'OPEN_CLOSE',
                action: 'SHOW',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'MODALWINDOW',
                elementGroup: 'pairings_group',
                source: 'user',
                tags: ['pairing']
            };
            log(msg);
        })

    $('#change-seeds')
        .mouseover(function () {
            var msg = {
                activity: 'perform',
                action: 'MOUSEOVER',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['pairing']
            };
            log(msg);
        })
        .mouseout(function () {
            var msg = {
                activity: 'perform',
                action: 'MOUSEOUT',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'user',
                tags: ['pairing']
            };
            log(msg);
        })
        .click(function () {
            //console.log($(this).parent().hasClass('open'))
            var msg = {
                activity: 'perform',
                action: 'KEYUP',
                elementId: this.getAttribute('id') || 'UNK',
                elementType: 'button',
                elementGroup: 'graph_B_group',
                source: 'system',
                tags: ['pairing','accept']
            };
            log(msg);
        });




}