var appDispatcher = require("../dispatcher/appDispatcher");

var updateActiveAction = function(viewId, update) {
  appDispatcher.dispatch({ action: {
      type: 'ACTIVE_ACTION_UPDATED',
      viewId: viewId,
      update: update
    }});
}

var clearActiveAction = function(viewId) {
  appDispatcher.dispatch({ action: {
      type: 'ACTIVE_ACTION_CLEARED',
      viewId: viewId
    }});
}

module.exports.updateActiveAction = updateActiveAction;
module.exports.clearActiveAction = clearActiveAction;
