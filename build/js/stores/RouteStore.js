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

// FormStore.removeListener = function(type, callback) {
//   FormStore.removeListener(type, callback);
// };

// Register with the dispatcher
RouteStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'ROUTE_CHANGED':
      _previous = _current + '';
      _current = action.href;
      RouteStore.emit('ROUTE_CHANGED');
      break;

    default:
      // do naaathing.
  }
});


module.exports = {
  getCurrentRoute: RouteStore.getCurrentRoute,
  addListener: RouteStore.addListener,
  removeListener: RouteStore.removeListener
}
