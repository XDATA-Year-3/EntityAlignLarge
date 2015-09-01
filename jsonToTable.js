/* global entityAlign */
$(function () {
    function jsonToTable(spec) {
        var table = $('<table>').addClass('table'),
            rows = [],
            that = this,
            data = spec.data || [],
            parent = spec.parent,
            specialCases = spec.specialCases || {},
            keyTransform = spec.keyTransform || function (k) {
                return k;
            };

        this.outputRow = function (key, value) {
            rows.push([keyTransform(key), value]);
        };

        this.renderRow = function (key, value) {
            var row = $('<tr>'),
                k = $('<td>'),
                v = $('<td>');
            k.text(key);
            k.appendTo(row);
            v.text(value);
            v.appendTo(row);
            row.appendTo(table);
        };

        this.render = function () {
            $.each(rows, function (i, row) {
                that.renderRow(row[0], row[1]);
            });
        };

        this.traverseArray = function (prefix, arr) {
            $.each(arr, function (i, value) {
                that.traverse(prefix + ' ' + (i + 1), value);
            });
        };

        this.traverseObject = function (prefix, obj) {
            var nesting = true;
            $.each(obj, function (key, value) {
                if ($.isPlainObject(value) || $.isArray(value)) {
                    nesting = true;
                }
            });
            if (nesting) {
                $.each(obj, function (key, value) {
                    if (specialCases[key] === null) {
                        key = key; // Output nothing
                    } else if (specialCases[key]) {
                        specialCases[key].call(that, prefix, value);
                    } else {
                        that.traverse(prefix + ' ' + key, value);
                    }
                });
            } else {
                var combinedValue = '';
                $.each(obj, function (key, value) {
                    combinedValue += ' ' + value;
                });
                that.outputRow(prefix, combinedValue);
            }
        };

        this.traverse = function (prefix, value) {
            if ($.isPlainObject(value)) {
                this.traverseObject(prefix, value);
            } else if ($.isArray(value)) {
                this.traverseArray(prefix, value);
            } else {
                this.outputRow(prefix, value);
            }
        };

        this.traverse('', data);

        rows.sort(function (a, b) {
            if (a[0] < b[0]) {
                return -1;
            }
            if (a[0] > b[0]) {
                return 1;
            }
            return 0;
        });

        this.render();

        table.appendTo(parent);
    }


    entityAlign.jsonToTable = function (elem, data) {
        jsonToTable({
            data: data,
            parent: $(elem || 'body'),
            specialCases: {
                // Turn each Payload into a key-value pair
                Payload: function (prefix, arr) {
                    var that = this;
                    $.each(arr, function (idx, value) {
                        var k = value.PayloadName || '',
                            v = value.PayloadValue || '';
                        if (k === 'DATAITEM') {
                            k = 'DATA_ITEM';
                        }
                        if (k.length > 3) {
                            var parts = k.split('_'),
                                i = 0;
                            for (i = 0; i < parts.length; i += 1) {
                                parts[i] = parts[i].charAt(0) + parts[i].slice(1).toLowerCase();
                            }
                            k = parts.join(' ');
                        }
                        that.outputRow(prefix + ' ' + k, v);
                    });
                },

                // Assuming 1 identity, so do not append 'Identity 1' to prefix
                Identity: function (prefix, arr) {
                    var that = this;
                    $.each(arr, function (i, value) {
                        that.traverse(prefix, value);
                    });
                },

                // These fields simply duplicate other data
                Domain: null,
                Username: null,
                NameType: null
            },

            // Split apart CamelCase keys into words
            keyTransform: function (key) {
                var parts = key.replace(/_/g, ' ').split(' '),
                    i;
                for (i = 0; i < parts.length; i += 1) {
                    if (parts[i] !== parts[i].toUpperCase()) {
                        parts[i] = parts[i].replace(
                            /([a-z])([A-Z])/g, '$1 $2');
                    }
                }
                return parts.join(' ');
            }
        });
    };
});
