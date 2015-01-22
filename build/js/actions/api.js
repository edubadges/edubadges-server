var appDispatcher = require("../dispatcher/appDispatcher");

var APIFormResultSuccess = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_FORM_RESULT_SUCCESS',
      formId: data.formId,
      message: data.message,
      result: data.result
    }});
}

var APIFormResultFailure = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_FORM_RESULT_FAILURE',
      formId: data.formId,
      message: data.message,
    }});
}

module.exports.APIFormResultSuccess = APIFormResultSuccess;
module.exports.APIFormResultFailure = APIFormResultFailure;