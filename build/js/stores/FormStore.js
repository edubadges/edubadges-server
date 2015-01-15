var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');



var FormStore = assign({}, EventEmitter.prototype);

FormStore.data = {}
FormStore.formIds = [
  "earnerBadgeCreate"
]

FormStore.idValid = function(id){
  return (typeof id == "string" && FormStore.formIds.indexOf(id) > -1);
};

FormStore.getFormData = function(id){
  if (!FormStore.idValid(id) || !id in FormStore.data)
    return {};
  else
    return FormStore.data[id];
};

FormStore.setFormData = function(id, data){
  if (FormStore.idValid(id) && data instanceof Object && !(data instanceof Array) )
    formStore.data[id] = data;
};

FormStore.patchFormData = function(id, propName, value){
  if (FormStore.idValid(id) && FormStore.data.hasOwnProperty(propName))
    formstore.data[id][propName] = value;
};


// listener utils
FormStore.addListener = function(type, callback) {
  FormStore.on(type, callback);
};

// FormStore.removeListener = function(type, callback) {
//   FormStore.removeListener(type, callback);
// };





// Register with the dispatcher
FormStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      FormStore.storeInitialData()
      FormStore.emit('INITIAL_DATA_LOADED');
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: FormStore.addListener,
  getCollection: FormStore.getCollection
}
