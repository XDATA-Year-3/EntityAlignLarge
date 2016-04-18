(function (clique, $, _, Backbone) {
  'use strict';

  function processNode (response) {
    var result = {};
    delete response.type;
    _.each(response, function (value, key) {
      if (key === '_id') {
        result.key = value.$oid;
      } else {
        result[key] = value;
      }
    });
    return result;
  }

  function processLink (response) {
    var result = {};
    delete response.type;
    _.each(response, function (value, key) {
      if (key === '_id') {
        result.key = value.$oid;
      } else if ((key === 'source' || key === 'target') && value.$oid) {
        result[key] = value.$oid;
      } else {
        result[key] = value;
      }
      if (key === 'source' || key === 'target') {
        result[key] = {key: result[key]};
      }
    });
    return result;
  }

  if (!clique.adapter) {
    clique.adapter = {};
  }

  clique.adapter.Mongo = function (cfg) {
    if (!(this instanceof clique.adapter.Mongo)) {
      return new clique.adapter.Mongo(cfg);
    }
    /* Extend clique.default.adapter.Adapter.  I'm sure there is a better way
     * to do this, but the more common methods seem to be prohibited from the
     * ES6 transpiled code. */
    var adapter = new clique.default.adapter.Adapter();
    var m_this = this;
    _.each(Object.getOwnPropertyNames(adapter), function (key) {
      m_this[key] = adapter[key];
    });
    _.each(Object.getOwnPropertyNames(Object.getPrototypeOf(adapter)), function (key) {
      m_this[key] = adapter[key];
    });

    this.mongoStore = {
      host: cfg.host || 'localhost',
      db: cfg.database,
      coll: cfg.collection
    };

    this.findNodesRaw = function (spec, offset, limit) {
      var data;

      data = _.extend({
        spec: JSON.stringify(spec || {}),
        offset: offset || 0,
        limit: limit || 0
      }, this.mongoStore);

      return $.getJSON('service/findNodes', data)
              .then(_.partial(_.map, _, processNode, undefined));
    };

    this.findLinksRaw = function (spec, source, target, directed, offset, limit) {
      var data;

      data = _.extend({
        spec: JSON.stringify(spec || {}),
        source: source,
        target: target,
        directed: JSON.stringify(_.isUndefined(directed) ? null : directed),
        offset: offset || 0,
        limit: limit || 0
      }, this.mongoStore);

      return $.getJSON('service/findLinks', data)
              .then(_.partial(_.map, _, processLink, undefined));
    };

    this.neighborLinksRaw = function (node, types, offset, limit) {
      var data;

      types = types || {};
      data = _.extend({
        node: node.key(),
        outgoing: _.isUndefined(types.outgoing) ? true : types.outgoing,
        incoming: _.isUndefined(types.incoming) ? true : types.incoming,
        undirected: _.isUndefined(types.undirected) ? true : types.undirected,
        offset: offset || 0,
        limit: limit || 0
      }, this.mongoStore);

      return $.getJSON('service/neighborLinks', data)
              .then(_.partial(_.map, _, processLink, undefined));
    };

    this.neighborLinkCount = function (node, opts) {
      var data;

      opts = opts || {};
      data = _.extend({
        node: node.key(),
        outgoing: _.isUndefined(opts.outgoing) ? true : opts.outgoing,
        incoming: _.isUndefined(opts.incoming) ? true : opts.incoming,
        undirected: _.isUndefined(opts.undirected) ? true : opts.undirected
      }, this.mongoStore);

      return $.getJSON('service/neighborLinkCount', data);
    };

    this.neighborCount = function (node, opts) {
      var data;

      opts = opts || {};
      data = _.extend({
        node: node.key(),
        outgoing: _.isUndefined(opts.outgoing) ? true : opts.outgoing,
        incoming: _.isUndefined(opts.incoming) ? true : opts.incoming,
        undirected: _.isUndefined(opts.undirected) ? true : opts.undirected
      }, this.mongoStore);

      return $.getJSON('service/neighborCount', data);
    };

    this.neighborhood = function (node, radius, linklimit) {
      var data = _.extend({
        start_key: node.key(),
        radius: radius,
        linklimit: linklimit
      }, this.mongoStore);

      return $.getJSON('service/neighborhood', data);
    };

    return this;

    /*
    var findNodesService = 'service/findNodes';
    var mutators = {};
    var mongoStore = {
      host: cfg.host || 'localhost',
      db: cfg.database,
      coll: cfg.collection
    };

    return _.extend({
      findNodes: function (spec) {
        var data = _.extend({
          spec: JSON.stringify(spec)
        }, mongoStore);

        return $.getJSON(findNodesService, data)
                   .then(_.partial(_.map, _, _.bind(this.getMutator, this)));
      },

      findNode: function (spec) {
        var data = _.extend({
          spec: JSON.stringify(spec),
          singleton: JSON.stringify(true)
        }, mongoStore);

        return $.getJSON(findNodesService, data)
                .then(_.bind(function (result) {
                  var def = new $.Deferred();

                  if (result) {
                    result = this.getMutator(result);
                  }

                  def.resolve(result);
                  return def;
                }, this));
      },

      neighborNodes: function (node, types, slice) {
        var options = {};
        return this.neighborhood($.extend(options, node, {radius: 1}));
      },

      neighborLinks: function (node) {
        var options = {};
        return this.neighborhood($.extend(options, {center: node}, {radius: 1}), true);
      },

      neighborhood: function (options, returnLinks) {
        console.log(options); //DWM::
        options = _.clone(options);
        options.center = options.center.key();
        options = _.extend(options, mongoStore);

        return $.getJSON('service/neighborhood', options)
               .then(_.bind(function (results) {
                 var def = new $.Deferred();

                 _.each(results.nodes, _.bind(function (node, i) {
                   var mut = this.getMutator(node);

                   if (mut.key() === options.center) {
                     mut.setTransient('root', true);
                   }

                   results.nodes[i] = mut.getTarget();
                 }, this));
                 if (returnLinks) {
                   var links = [];
                   _.each(results.links, function (link) {
                     links.push({
                       key: function () {
                         return link.source + '_' + link.target;
                       },
                       source: function () { return link.source; },
                       target: function () { return link.target; },
                       getAttribute: function (prop) {
                         return prop === 'undirected';
                       },
                       getRaw: function () { return link; }
                     });
                   });
                   results = links;
                 }
                 def.resolve(results);
                 return def;
               }, this));
      },

      sync: function () {
        var def = new $.Deferred();
        def.resolve();
        return def;
      },

      getMutator: function (mongoRec) {
        var key = mongoRec._id.$oid;
        var mut = {target: {data: mongoRec.data}};
        mut.getTarget = function () {
          return mut.target;
        };
        mut.key = mut.target.key = function () {
          return key;
        };
        mut.clearAttribute = function (prop) {
          delete mut.target[prop];
        };
        mut.setTransient = function (prop, value) {
          mut.target[prop] = value;
        };
        mut.target.getRaw = function () {
          return mut.target.data;
        };
        mutators[key] = mut;
        return mut;
      },

      getAccessor: function (key) {
        if (mutators[key]) {
          return mutators[key];
        }
        return {
          clearAttribute: function () {}
        };
      }
    }, Backbone.Events);
    */
  };
}(window.clique, window.jQuery, window._, window.Backbone));
