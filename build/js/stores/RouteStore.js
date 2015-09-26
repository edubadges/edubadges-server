var appDispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');


var RouteStore = assign({}, EventEmitter.prototype);
 
// RouteStore State:
var _previous = null;
var _current = window.location.pathname; // "/something/something"
var _params = {};


RouteStore.getCurrentRoute = function() {
  return _current;
};

// listener utils
RouteStore.addListener = function(type, callback) {
  RouteStore.on(type, callback);
};

FormStore.removeStoreListener = function(type, callback) {
   FormStore.removeListener(type, callback);
 };

// Register with the dispatcher
RouteStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'ROUTE_CHANGED':
      _previous = _current + '';
      _current = action.href;
      // This event will trigger another action, so we need to break out
      // of the current dispatcher context w/setTimeout.
      setTimeout(function(){ RouteStore.emit('ROUTE_CHANGED'); }, 0);
      
      break;

    default:
      // do naaathing.
  }
});


module.exports = {
  getCurrentRoute: RouteStore.getCurrentRoute,
  addListener: RouteStore.addListener,
  removeListener: RouteStore.removeStoreListener
}
