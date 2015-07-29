var appDispatcher = require("../dispatcher/appDispatcher");

var APIFormResultSuccess = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_FORM_RESULT_SUCCESS',
      formId: data.formId,
      formType: data.formType,
      message: data.message,
      result: data.result
    }});
}

var APIFormResultFailure = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_FORM_RESULT_FAILURE',
      formId: data.formId,
      formType: data.formType,
      message: data.message
    }});
}

var APIGetData = function(apiContext, requestContext) {
  appDispatcher.dispatch({ action: {
      type: 'API_GET_DATA',
      apiContext: apiContext,
      requestContext: requestContext
    }});
}

var APISubmitData = function(data, apiContext, requestContext){
  appDispatcher.dispatch({ action: {
    type: 'API_SUBMIT_DATA',
    apiData: data,
    apiContext: apiContext,
    requestContext: requestContext
  }});
}

var APIGetResultFailure = function(data) {
  appDispatcher.dispatch({ action: {
      type: 'API_GET_RESULT_FAILURE',
      message: data.message
    }});
}

var APIFetchCollections = function(collectionKeys, requestContext) {
  appDispatcher.dispatch({ action: {
    type: 'API_FETCH_COLLECTIONS',
    collectionIds: collectionKeys,
    requestContext: requestContext
  }}); 
}


module.exports = {
  APIFormResultSuccess: APIFormResultSuccess,
  APIFormResultFailure: APIFormResultFailure,
  APIGetResultFailure: APIGetResultFailure,
  APIGetData: APIGetData,
  APIFetchCollections: APIFetchCollections,
  APISubmitData: APISubmitData
}
