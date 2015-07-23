var appDispatcher = require("../dispatcher/appDispatcher");

var patchFormAction = function(formId, patch) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_DATA_PATCHED',
      formId: formId,
      update: patch
    }});
}

var submitFormAction = function(formId, formType) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_SUBMIT',
      formId: formId,
      formType: formType
    }});
}

var resetFormAction = function(formId) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_RESET',
      formId: formId
    }});
}

module.exports.patchForm = patchFormAction;
module.exports.submitForm = submitFormAction;
module.exports.resetForm = resetFormAction;