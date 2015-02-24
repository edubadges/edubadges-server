var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');


/*
The concept of an ActiveAction is a task-and-context-oriented way 
to organize the application. Each view in known

*/
var ActiveActionStore = assign({}, EventEmitter.prototype);

/*
Example action data instance:
'viewKey': {
  type: 'EarnerBadgeForm',
  content: { badgeId: null }
}, 
'viewKey2': {
  type: "EarnerBadgeDisplay",
  content: { badgeId: 68 }
}
*/
ActiveActionStore.data = {};

// Different views that have the concept of an ActiveAction
ActiveActionStore.knownViews = [
  'earnerHome'
];

ActiveActionStore.updateAction = function(viewId, update){
  if (ActiveActionStore.knownViews.indexOf(viewId) > -1){
    ActiveActionStore.data[viewId] = update;
    ActiveActionStore.emit('ACTIVE_ACTION_UPDATED');
  }
};
ActiveActionStore.clearAction = function(viewId){
  delete ActiveActionStore.data[viewId];
  ActiveActionStore.emit('ACTIVE_ACTION_UPDATED');
}
ActiveActionStore.getActiveAction = function(viewId){
  if (viewId in ActiveActionStore.data)
    return ActiveActionStore.data[viewId];
  else
    return {};
};
ActiveActionStore.getAllActiveActions = function() {
  return ActiveActionStore.data;
}


// listener utils
ActiveActionStore.addListener = function(type, callback) {
  ActiveActionStore.on(type, callback);
};
// ActiveActionStore.removeListener = function(type, callback) {
//   ActiveActionStore.removeListener(type, callback);
// };


// Register with the dispatcher
ActiveActionStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'ACTIVE_ACTION_UPDATED':
      ActiveActionStore.updateAction(action.viewId, action.update);
      break;

    case 'ACTIVE_ACTION_CLEARED':
      ActiveActionStore.clearAction(action.viewId);
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: ActiveActionStore.addListener,
  removeListener: ActiveActionStore.removeListener,
  getActiveAction: ActiveActionStore.getActiveAction,
  getAllActiveActions: ActiveActionStore.getAllActiveActions
};
