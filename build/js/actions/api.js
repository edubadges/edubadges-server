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
      message: data.message
    }});
}

var APIGetData = function(apiContext) {
  appDispatcher.dispatch({ action: {
      type: 'API_GET_DATA',
      apiContext: apiContext
    }});
}

var APIGetResultFailure = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_GET_RESULT_FAILURE',
      message: data.message
    }});
}


module.exports = {
  APIFormResultSuccess: APIFormResultSuccess,
  APIFormResultFailure: APIFormResultFailure,
  APIGetResultFailure: APIGetResultFailure,
  APIGetData: APIGetData
}
