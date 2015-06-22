var _ = require('underscore')

var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');
var APIStore = require('../stores/APIStore');
var EarnerActions = require('../actions/earner');


var FormStore = assign({}, EventEmitter.prototype);

FormStore.requests = {};

FormStore.data = {}

FormStore.genericFormTypes = [
  'IssuerCreateUpdateForm',
  'BadgeClassCreateUpdateForm',
  'BadgeInstanceCreateUpdateForm',
  'EarnerBadgeImportForm',
  'EarnerCollectionCreateForm',
  'EarnerCollectionEditForm'
]

FormStore.idValid = function(formId){
  return (FormStore.data.hasOwnProperty(formId))
}

FormStore.getFormData = function(formId){
  if (!FormStore.idValid(formId))
    return {};
  else
    return FormStore.data[formId];
};
FormStore.getFormState = function(formId){
  if (!FormStore.idValid(formId))
    return {};
  else
    return FormStore.data[formId].formState;
};

FormStore.getOrInitFormData = function(formId, initialData){
  if (!FormStore.data.hasOwnProperty(formId))
    FormStore.data[formId] = initialData

  if (!FormStore.data[formId].formState)
    FormStore.data[formId].formState = _.clone(initialData.defaultValues);

  return FormStore.getFormData(formId);
}

FormStore.resetForm = function(formId){
  if (FormStore.idValid(formId))
    FormStore.data[formId].formState = _.clone(FormStore.data[formId].defaultValues);
};

FormStore.patchFormProperty = function(formId, propName, value){
  if (FormStore.idValid(formId)) // for state not specified in fieldsMeta
    FormStore.data[formId].formState[propName] = value;
  else
    console.log("Error: Could not patch form " + formId + " property " + propName);
};
FormStore.patchForm = function(id, data){
  for (key in data){
    FormStore.patchFormProperty(id, key, data[key]);
  }
};
FormStore.getFieldValue = function(formId, field){
  if (FormStore.idValid(formId) && field in FormStore.data[formId].fieldsMeta)
    return FormStore.data[formId][field];
}


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
      FormStore.resetForm(action.formId);
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
  getFormState: FormStore.getFormState,
  resetFormData: FormStore.resetFormData,
  getOrInitFormData: FormStore.getOrInitFormData,
  patchFormData: FormStore.patchFormProperty,
  getFieldValue: FormStore.getFieldValue,
  genericFormTypes: FormStore.genericFormTypes,
  listeners: FormStore.listeners,
  dispatchToken: FormStore.dispatchToken
}
