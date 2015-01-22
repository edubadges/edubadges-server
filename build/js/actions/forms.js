var appDispatcher = require("../dispatcher/appDispatcher");

var patchFormAction = function(formId, patch) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_DATA_PATCHED',
      formId: formId,
      update: patch
    }});
}

var submitFormAction = function(formId) {
  appDispatcher.dispatch({ action: {
      type: 'FORM_SUBMIT',
      formId: formId
    }});
}

module.exports.patchForm = patchFormAction;
module.exports.submitForm = submitFormAction;