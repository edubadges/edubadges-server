var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');

var RouteStore = require('../stores/RouteStore');



var APIStore = assign({}, EventEmitter.prototype);

APIStore.data = {}
APIStore.collectionTypes = [
  "earnerBadges",
  "earnerBadgeCollections",
  "earnerNotifications",
  "issuerBadgeClasses",
  "issuerBadges"
]

APIStore.getCollection = function(collectionType) {
  if (collectionType.indexOf(collectionType) > -1)
    return APIStore.data[collectionType];
  else {
    throw new TypeError(collectionType + " not supported by APIStore");
    return []
  }
};


// listener utils
APIStore.addListener = function(type, callback) {
  APIStore.on(type, callback);
};

// APIStore.removeListener = function(type, callback) {
//   APIStore.removeListener(type, callback);
// };

// on startup
APIStore.storeInitialData = function() {
  var _initialData;

  // try to load the variable declared as initialData in the view template
  if (initialData) {
    // TODO: Add validation of types?
    _initialData = initialData
    for (key in _initialData){
      if (APIStore.collectionTypes.indexOf(key) > -1) {
        APIStore.data[key] = JSON.parse(_initialData[key])
      }
    }
    ;
  }
}



// Register with the dispatcher
APIStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      APIStore.storeInitialData()
      APIStore.emit('INITIAL_DATA_LOADED');
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: APIStore.addListener,
  getCollection: APIStore.getCollection
}
