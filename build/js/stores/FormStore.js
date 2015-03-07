var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');
var APIStore = require('../stores/APIStore');
var EarnerActions = require('../actions/earner');


var FormStore = assign({}, EventEmitter.prototype);

FormStore.data = {};
FormStore.formIds = [
  "EarnerBadgeForm",
  "IssuerNotificationForm",
  "ConsumerBadgeForm"
];
FormStore.requests = {};


FormStore.idValid = function(id){
  return (typeof id == "string" && FormStore.formIds.indexOf(id) > -1);
};

FormStore.getFormData = function(id){
  if (!FormStore.idValid(id) || !FormStore.data.hasOwnProperty(id))
    return {};
  else
    return FormStore.data[id];
};
FormStore.defaultValues = {
  EarnerBadgeForm: {
    actionState: "ready"
  },
  ConsumerBadgeForm: {
    actionState: "ready"
  },
  IssuerNotificationForm: {
    email: "",
    url: "", 
    actionState: "ready"
  }
}
FormStore.getOrInitFormData = function(formId, initialData){
  var formData = FormStore.getFormData(formId);
  if (!formData)
    return initialData;
  if (Object.keys(formData).length === 0){
    FormStore.setFormData(
      formId, 
      assign( FormStore.defaultValues[formId], initialData )
    );
    return FormStore.getFormData(formId);
  }
  return formData;
}

FormStore.setFormData = function(id, data){
  if (FormStore.idValid(id) && data instanceof Object && !(data instanceof Array) )
    FormStore.data[id] = data;
};

FormStore.patchFormProperty = function(id, propName, value){
  console.log("Patching form property: " + id + ", " + propName + ", " + value);
  if (FormStore.idValid(id))
    FormStore.data[id][propName] = value;
};
FormStore.patchForm = function(id, data){
  for (key in data){
    FormStore.patchFormProperty(id, key, data[key]);
  }
};


// listener utils
FormStore.addListener = function(type, callback) {
  FormStore.on(type, callback);
};

// FormStore.removeListener = function(type, callback) {
//   FormStore.removeListener(type, callback);
// };





// Register with the dispatcher
FormStore.dispatchToken = Dispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'FORM_DATA_PATCHED':
      FormStore.patchForm(action.formId, action.update);
      FormStore.emit('FORM_DATA_UPDATED_' + action.formId);
      break;

    case 'FORM_SUBMIT':
      FormStore.patchForm(action.formId, {actionState: 'waiting'});
      FormStore.emit('FORM_DATA_UPDATED_' + action.formId);
      break;

    case 'FORM_RESET':
      FormStore.setFormData(action.formId, FormStore.defaultValues[action.formId]);
      FormStore.emit('FORM_DATA_UPDATED_' + action.formId);
      break;

    case 'API_FORM_RESULT_SUCCESS':
      FormStore.patchForm(
        action.formId, 
        { actionState: 'complete', message: action.message, result: action.result }
      );
      FormStore.emit('FORM_DATA_UPDATED_' + action.formId);
      break;

    case 'API_FORM_RESULT_FAILURE':
      FormStore.patchForm( action.formId, {
        actionState: 'ready', 
        message: action.message
      });
      FormStore.emit('FORM_DATA_UPDATED_' + action.formId);
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: FormStore.addListener,
  removeListener: FormStore.removeListener,
  getCollection: FormStore.getCollection,
  getFormData: FormStore.getFormData,
  getOrInitFormData: FormStore.getOrInitFormData,
  patchFormData: FormStore.patchFormProperty,
  listeners: FormStore.listeners,
  dispatchToken: FormStore.dispatchToken
}
