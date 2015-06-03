var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');

// var UserActions = require('../actions/user');

// The UserStore keeps track of the current user's profile information
var UserStore = assign({}, EventEmitter.prototype);

UserStore.data = {}
PROFILE_KEYWORD = 'user';

UserStore.getProperty = function(profileKey) {
  if (profileKey in UserStore.data)
    return UserStore.data[profileKey];
  else {
    return undefined;
  }
};
UserStore.getProfile = function() {
  return UserStore.data;
}

// listener utils
UserStore.addListener = function(type, callback) {
  UserStore.on(type, callback);
};

// Part of eventemitter
// UserStore.removeListener = function(type, callback)


// on startup
UserStore.storeInitialData = function() {
  var _initialData;

  // try to load the variable declared as initialData in the view template
  if (initialData) {
    // TODO: Add validation of types?
    _initialData = initialData
    if (PROFILE_KEYWORD in _initialData){
      UserStore.data = _initialData[PROFILE_KEYWORD]
    }
  }
}



// Register with the dispatcher
UserStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      UserStore.storeInitialData();
      UserStore.emit('USER_DATA_LOADED');
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: UserStore.addListener,
  removeListener: UserStore.removeListener,
  getProperty: UserStore.getProperty,
  getProfile:UserStore.getProfile
}
