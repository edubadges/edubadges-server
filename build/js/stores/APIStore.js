var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');
var request = require('superagent');

var FormStore = require('../stores/FormStore');
var APIActions = require('../actions/api');

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var APIStore = assign({}, EventEmitter.prototype);

APIStore.data = {}
APIStore.collectionTypes = [
  "earnerBadges",
  "earnerBadgeCollections",
  "earnerNotifications",
  "issuerBadgeClasses",
  "issuerBadges",
  "consumerBadges",
  'issuer'
]

APIStore.getCollection = function(collectionType) {
  if (collectionType.indexOf(collectionType) > -1)
    return APIStore.data[collectionType];
  else {
    throw new TypeError(collectionType + " not supported by APIStore");
    return []
  }
};
APIStore.getCollectionLastItem = function(collectionType) {
  var collection = APIStore.getCollection(collectionType);
  if (collection.length > 0)
    return collection[collection.length -1];
  else
    return {};
};
APIStore.getFirstItemByPropertyValue = function(collectionType, propName, value){
  // Will return the first item that matches -- don't use for queries where you want multiple results.
  var collection = APIStore.getCollection(collectionType);
  if (collection.length > 0) {
    for (var i=0; i<collection.length; i++){
      if (collection[i].hasOwnProperty(propName) && collection[i][propName] == value){
        return collection[i];
      }
    }
  }
  return {};
}
APIStore.addCollectionItem = function(collectionKey, item) {
  if (APIStore.collectionTypes.indexOf(collectionKey) > -1){
    if (!APIStore.data.hasOwnProperty(collectionKey))
      APIStore.data[collectionKey] = [];
    APIStore.data[collectionKey].push(item);
    return item;
  }
  else
    return false;
}


// listener utils
APIStore.addListener = function(type, callback) {
  APIStore.on(type, callback);
};

// Part of eventemitter
// APIStore.removeListener = function(type, callback)


// on startup
APIStore.storeInitialData = function() {
  var _initialData;

  // try to load the variable declared as initialData in the view template
  if (initialData) {
    // TODO: Add validation of types?
    _initialData = initialData
    for (key in _initialData){
      if (APIStore.collectionTypes.indexOf(key) > -1) {
        APIStore.data[key] = _initialData[key]
      }
    }
  }
}


/* postForm(): a common function for POSTing forms and returning results
 * to the FormStore.
 * Params:
 *   context: a dictionary providing information about the API endpoint
 *            and expected return results.
 *   fields: the form data from the FormStore.
 * This function will interrogate the data and attach appropriate fields
 * to the post request.
*/
APIStore.postForm = function(fields, values, context){
  
  if (context.method == 'POST')
    var req = request.post(context.actionUrl);
  else if (context.method == 'DELETE')
    var req = request.delete(context.actionUrl);
  else if (context.method == 'PUT')
    var req = request.put(context.actionUrl);

  req.set('X-CSRFToken', getCookie('csrftoken'))
  .accept('application/json');

  // Attach data fields to request
  for (field in fields) {
    if (["text", "textarea", "select"].indexOf(fields[field].inputType) > -1 && values[field])
      req.field(field, values[field]);
    else if (["image", "file"].indexOf(fields[field].inputType) > -1 && values[field])
      req.attach(field, values[field], fields[field].filename);
  }

  req.end(function(error, response){
    console.log(response);
    if (error){
      console.log("THERE WAS SOME KIND OF API REQUEST ERROR.");
      console.log(error);
      APIStore.emit('API_STORE_FAILURE');
    }
    else if (context.successHttpStatus.indexOf(response.status) == -1){
      console.log("API REQUEST PROBLEM:");
      console.log(response.text);
      APIActions.APIFormResultFailure({
        formId: context.formId,
        message: {type: 'danger', content: response.status + " Error submitting form: " + response.text}
      });
    }
    else{
      var newObject = APIStore.addCollectionItem(context.apiCollectionKey, JSON.parse(response.text))
      if (newObject){
        APIStore.emit('DATA_UPDATED_' + context.apiCollectionKey);
        APIActions.APIFormResultSuccess({
          formId: context.formId, 
          message: {type: 'success', content: context.successMessage},
          result: newObject
        });
      }
      else {
        APIStore.emit('API_STORE_FAILURE');
        console.log("Failed to add " + response.text + " to " + context.apiCollectionKey);
      }
    } 
  });

  return req;
}




// Register with the dispatcher
APIStore.dispatchToken = Dispatcher.register(function(payload){
  
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      APIStore.storeInitialData()
      APIStore.emit('INITIAL_DATA_LOADED');
      break;

    case 'FORM_SUBMIT':
      // make sure form updates have occurred before processing submits
      Dispatcher.waitFor([FormStore.dispatchToken]);

      if (action.formId == "EarnerBadgeForm")
        APIStore.postEarnerBadgeForm(FormStore.getFormData(action.formId));
      else if (action.formId == "ConsumerBadgeForm")
        APIStore.postConsumerBadgeForm(FormStore.getFormData(action.formId));
      else if (action.formId == "IssuerNotificationForm")
        APIStore.postIssuerNotificationForm(FormStore.getFormData(action.formId));
      else if (FormStore.genericFormTypes.indexOf(action.formId) > -1){
        formData = FormStore.getFormData(action.formId);
        APIStore.postForm(formData.fieldsMeta, formData.formState, formData.apiContext);
      }
      else
        console.log("Unidentified form type to submit: " + action.formId);
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: APIStore.addListener,
  removeListener: APIStore.removeListener,
  getCollection: APIStore.getCollection,
  getCollectionLastItem: APIStore.getCollectionLastItem,
  getFirstItemByPropertyValue: APIStore.getFirstItemByPropertyValue
}
