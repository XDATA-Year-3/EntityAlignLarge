(function (clique, $, _, Backbone, moment) {
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
    if (result.data) {
      _.each(result.data, function (value, key) {
        if (value && value.$date) {
          result.data[key] = moment.utc(value.$date).format(
            'YYYY-MM-DD HH:mm:ss');
        }
      });
    }
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
    var pendingRequests = {next: 0, requests: {}};

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

      return this.getJSON('service/findNodes', data)
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

      return this.getJSON('service/findLinks', data)
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

      return this.getJSON('service/neighborLinks', data)
              .then(_.partial(_.map, _, processLink, undefined));
    };

    /* This is a wrapper around jquery's getJSON that keeps track of the
     * request so that it can be aborted.
     */
    this.getJSON = function () {
      var req = $.getJSON.apply(this, arguments);
      req.requestNumber = pendingRequests.next;
      pendingRequests.next += 1;
      pendingRequests.requests[req.requestNumber] = req;
      req.always(function () {
        delete pendingRequests.requests[req.requestNumber];
      });
      return req;
    };

    /* Abort all pending requests. */
    this.cancel = function () {
      $.each(pendingRequests.requests, function (idx, req) {
        req.abort();
      });
      pendingRequests.requests = {};
    };

    return this;
  };
}(window.clique, window.jQuery, window._, window.Backbone, window.moment));
