var _ = require('lodash');
var appDispatcher = require("../dispatcher/appDispatcher");
var FormStore = require("../stores/FormStore");


var patchFormAction = function(formId, patch) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_DATA_PATCHED',
      formId: formId,
      update: patch
    }});
};


var submitFormAction = function(formId, formType, requestContext) {
  var formActionStatus = _.get(FormStore.getFormData(formId), 'formState.actionState');
  if (formActionStatus && formActionStatus !== "waiting")
      appDispatcher.dispatch({
          action: {
              type: 'FORM_SUBMIT',
              formId: formId,
              formType: formType,
              requestContext: requestContext
          }
      });
};


var resetFormAction = function(formId) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_RESET',
      formId: formId
    }});
};


module.exports.patchForm = patchFormAction;
module.exports.submitForm = submitFormAction;
module.exports.resetForm = resetFormAction;