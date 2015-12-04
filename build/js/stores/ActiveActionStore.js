var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');

var MenuStore = require('../stores/MenuStore');

/*
The concept of an ActiveAction is a task-and-context-oriented way 
to organize the application. 

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

ActiveActionStore.updateAction = function(viewId, update){
    ActiveActionStore.data[viewId] = update;
    ActiveActionStore.emit('ACTIVE_ACTION_UPDATED');
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
 ActiveActionStore.removeStoreListener = function(type, callback) {
   ActiveActionStore.removeListener(type, callback);
 };


// Register with the dispatcher
ActiveActionStore.dispatchToken = appDispatcher.register(function(payload){
  Dispatcher.waitFor([MenuStore.dispatchToken]);
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
  removeListener: ActiveActionStore.removeStoreListener,
  getActiveAction: ActiveActionStore.getActiveAction,
  getAllActiveActions: ActiveActionStore.getAllActiveActions
};
