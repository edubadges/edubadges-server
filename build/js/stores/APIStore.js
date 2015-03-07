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
  "consumerBadges"
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

APIStore.postEarnerBadgeForm = function(data){
  var context = {
    formId: "EarnerBadgeForm",
    apiCollectionKey: "earnerBadges",
    actionUrl: "/api/earner/badges",
    successHttpStatus: [201],
    successMessage: "Successfully added badge to your collection."
  }
  return APIStore.postBadgeForm(data, context);
};

APIStore.postConsumerBadgeForm = function(data){
  var context = {
    formId: "ConsumerBadgeForm",
    apiCollectionKey: "consumerBadges",
    actionUrl: "/api/consumer/badges",
    successHttpStatus: [200, 201],
    successMessage: "Badge analysis successful"
  }
  return APIStore.postBadgeForm(data, context);
};

/* postBadgeForm(): a common function to communicate with various API endpoints
 * to post badges in various contexts. 
 * Params:
 *   context is a dictionary providing the API endpoint
 *   data is the form data from the FormStore
*/
APIStore.postBadgeForm = function(data, context){

  var req = request.post(context.actionUrl)
    .set('X-CSRFToken', getCookie('csrftoken'))
    .accept('application/json')
    .field('recipient_input',data['recipient_input']);

    if ('earner_description' in data)
      req.field('earner_description', data['earner_description']);


    req.attach('image', data['image'], 'earner_badge_upload.png');

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
          message: {type: 'danger', content: "Error adding badge: " + response.text}
        });
      }
      else{
        var newBadge = APIStore.addCollectionItem(context.apiCollectionKey, JSON.parse(response.text))
        if (newBadge){
          APIStore.emit('DATA_UPDATED_' + context.apiCollectionKey);
          APIActions.APIFormResultSuccess({
            formId: context.formId, 
            message: {type: 'success', content: context.successMessage}, 
            result: newBadge 
          });
        }
        else {
          APIStore.emit('API_STORE_FAILURE');
          console.log("Failed to add " + response.text + " to " + context.apiCollectionKey);
        }
      } 
    });
  return req;
};

APIStore.postIssuerNotificationForm = function(data){
  console.log("GOING TO POST THE ISSUER NOTIFICATION FORM WITH DATA:");
  console.log(data);
  var req = request.post('/api/issuer/notifications')
    .set('X-CSRFToken', getCookie('csrftoken'))
    .accept('application/json')
    .field('url',data['url'])
    .field('email', data['email'])
    .end(function(error, response){
      console.log(response);
      if (error){
        console.log("THERE WAS SOME KIND OF API REQUEST ERROR.");
        console.log(error);
        APIStore.emit('API_STORE_FAILURE');
      }
      else if (response.status != 201){
        console.log("API REQUEST PROBLEM:");
        console.log(response.text);
        APIActions.APIFormResultFailure({
          formId: 'IssuerNotificationForm',
          message: {type: 'danger', content: "Error notifying earner: " + response.text}
        });
      }
      else{
        APIStore.emit('DATA_UPDATED_issuerNotification');
        APIActions.APIFormResultSuccess({
          formId: 'IssuerNotificationForm', 
          message: {type: 'success', content: "Successfully notified earner " + data['email'] + "." }, 
          result: {}
        });
      } 
    });
  return req;
};

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
