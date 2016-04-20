/* globals $, d3 */

var lineUpConfig = {
  interaction: {
    tooltips: false
  },
  renderingOptions: {
    animation: true,
    stacked: false
  },
  header: {
    headerHeight: 24
  },
  body: {  /* was called svgLayout */
    mode: 'separate',
    rowHeight: 18,
    rowPadding: 2.0 / 18
  },
  manipulative: true  /* false to previce removing columns and other actions */
};
var lineup = {};
var lineupCol = {};
var lineupRankWidth = 50;

/* Create or recreate a lineup control.
 *
 * @param elem: selector to the parent div wrapper for the control.
 * @param name: name of the control.
 * @param desc: column description.
 * @param dataset: dataset to load.
 * @param lineupObj: old lineup object to replace.
 * @param sort: if specified, sort by this column.
 * @param selectCallback: if present, bind 'selected' to this function.
 * @returns: a lineup control object.
 */
function createLineup (elem, name, desc, dataset, lineupObj, sort,
                       selectCallback) {
  var lineupjs = window.LineUpJS || window.LineUp;
  /* This has been parroted from the demo. */
  var spec = {};
  spec.name = name;
  spec.dataspec = desc;
  delete spec.dataspec.file;
  delete spec.dataspec.separator;
  spec.dataspec.data = dataset;
  spec.storage = lineupjs.createLocalStorage(dataset, lineupjs.deriveColors(
      desc.columns));

  var config = ((lineupObj ? lineupObj.config : $.extend(
    {}, lineUpConfig)) || {});
  if (!config.renderingOptions) {
    config.renderingOptions = {};
  }
  var oldAnimation = config.renderingOptions.animation;
  config.renderingOptions.animation = false;
  var columnFixed = 5;
  var scale = createLineupAdjustWidth(elem, name, spec, columnFixed);
  /* Never take the first branch if we always want to regenerate the lineup
   * container.  There is a bug where the columns are not clipped properly,
   * and regeneration works around it.  Both cases bleed memory, I think, and
   * regeneration is worse than update. */
  if (lineupObj && 0) {
    // untested after refactor
    lineupObj.changeDataStorage(spec.storage, desc);
  } else {
    $(elem).empty();
    /* Lineup takes a d3 element */
    lineupObj = lineupjs.create(spec.storage, d3.select(elem), lineUpConfig);
    lineupObj.restore(desc);
    config = lineupObj.config;
    lineupObj.header.dragHandler.on('dragend.lineupWidget', function (evt) {
      lineupDragColumnEnd(name, evt);
    });
  }
  lineupObj['column-scale'] = scale;
  lineupObj['column-fixed'] = columnFixed;
  lineupObj['lineup-key'] = name;
  $(elem).attr('lineup-key', name);
  if (sort) {
    lineupObj.sortBy(sort);
  }
  lineupObj.changeRenderingOption('animation', oldAnimation);
  var fixTooltips = function () {
    for (var i = 0; i < desc.columns.length; i += 1) {
      if (desc.columns[i].description) {
        var label = (desc.columns[i].label || desc.columns[i].column);
        $('title', $(elem + ' .lu-header text.headerLabel:contains("' + label + '")').parent()).text(
                label + ': ' + desc.columns[i].description);
      }
    }
  };
  if (selectCallback) {
    lineupObj.on('selectionChanged.lineupWidget', null);
    lineupObj.on('selectionChanged.lineupWidget', function (row) {
      selectCallback(dataset[row]);
    });
  }
  /* Try twice to work around some issues */
  window.setTimeout(fixTooltips, 1);
  window.setTimeout(fixTooltips, 1000);
  lineup[name] = lineupObj;
  return lineupObj;
}

/* Adjust the width of the columns in lineup to (a) use the available space,
 * and (b) use the weights selected by the user.
 *
 * @param elem: the element where the lineup is placed.
 * @param name: the name used for this lineup.  Used for tracking user widths.
 * @param spec: the specification for the lineup.  Modified.
 * @param fixed: fixed width used in each column.
 * @returns: relative scale of lineup to available space.
 */
function createLineupAdjustWidth (elem, name, spec, fixed) {
  var rankWidth = 0;
  var total = 0;
  var count = 0;
  var c1, c2;
  var width = $(elem)[0].getBoundingClientRect().width - $.scrollbarWidth() - fixed;
  var col = spec.dataspec.layout.primary;
  for (c1 = 0; c1 < col.length; c1 += 1) {
    if (col[c1].children) {
      for (c2 = 0; c2 < col[c1].children.length; c2 += 1) {
        count += 1;
        total += lineupGetColumnWidth(name, col[c1].children[c2], fixed);
      }
    } else {
      if (col[c1].type === 'rank') { /* LineUp wants this to be 50 */
        rankWidth = lineupRankWidth + fixed;
        continue;
      }
      count += 1;
      total += lineupGetColumnWidth(name, col[c1], fixed);
    }
  }
  var avail = width - count * fixed - rankWidth;
  avail -= count + (rankWidth ? 1 : 0); // I'm not sure why this is necessary
  var scale = avail / total;
  for (c1 = 0; c1 < col.length; c1 += 1) {
    if (col[c1].children) {
      for (c2 = 0; c2 < col[c1].children.length; c2 += 1) {
        col[c1].children[c2].width = fixed + col[c1].children[c2].widthBasis * scale;
      }
    } else {
      col[c1].width = fixed + col[c1].widthBasis * scale;
      if (col[c1].type === 'rank') { /* LineUp wants this to be fixed */
        col[c1].width = lineupRankWidth + fixed;
      }
    }
  }
  return scale;
}

/* After a column is resized in lineup, record the size it became relative to
 * the scaling we are using.
 *
 * @param name: name of the lineup record we have adjusted.
 */
function lineupDragColumnEnd (name) {
  var c1, c2;
  if (!lineupCol[name]) {
    lineupCol[name] = {};
  }
  var record = lineupCol[name];
  var col = lineup[name].dump().rankings[0].columns;
  var scale = lineup[name]['column-scale'];
  var fixed = lineup[name]['column-fixed'];
  for (c1 = 0; c1 < col.length; c1 += 1) {
    if (col[c1].children) {
      for (c2 = 0; c2 < col[c1].children.length; c2 += 1) {
        record[col[c1].children[c2].desc.split('@')[1]] = (col[c1].children[c2].width - fixed) / scale;
      }
    } else {
      record[col[c1].desc.label ? 'rank' : col[c1].desc.split('@')[1]] = (col[c1].width - fixed) / scale;
    }
  }
}

/* Get the width of a column.  If the user has changed the width, scale based
 * on that activity.
 *
 * @param name: name of the lineup.  Used for user settings.
 * @param col: column specification.
 * @param fixed: minimum width for a column.
 */
function lineupGetColumnWidth (name, col, fixed) {
  var width = col.width || 0;
  var colname = col.column || col.type;
  /* Get the column scaling based on the user settings, if available */
  if (lineupCol && lineupCol[name] && lineupCol[name][colname]) {
    width = lineupCol[name][colname] + fixed;
  }
  var colWidth = width < fixed ? 0 : (width - fixed);
  if (col === 'rank') {  /* defined in LineUp */
    colWidth = lineupRankWidth;
  }
  col.widthBasis = colWidth;
  col.widthFixed = fixed;
  return col.widthBasis;
}

/* Add a function to jquery to calculate the width of a scroll bar.
 *
 * @returns: the width of the scroll bar.
 */
$.scrollbarWidth = function () {
  var parent, child, width;

  if (width === undefined) {
    parent = $('<div style="width:50px;height:50px;overflow:auto"><div/></div>').appendTo('body');
    child = parent.children();
    width = child.innerWidth() - child.height(99).innerWidth();
    parent.remove();
  }
  return width;
};

/* exports */
!(function () {
  this.createLineup = createLineup;
  this.lineup = lineup;
})();
