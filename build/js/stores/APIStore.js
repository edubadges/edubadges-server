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
  "issuerBadges"
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

  var req = request.post('/api/earner/badges')
    .set('X-CSRFToken', getCookie('csrftoken'))
    .accept('application/json')
    .field('recipient_input',data['recipient_input'])
    .field('earner_description', data['earner_description'])
    // .attach(image, {type: image.type})
    .attach('image', data['image'], 'earner_badge_upload.png')
    .end(function(error, response){
      console.log(response);
      if (error){
        console.log("THERE WAS SOME KIND OF API REQUEST ERROR.");
        console.log(error);
        APIStore.emit('API_STORE_FAILURE');
      }
      else if (response.status != 200){
        console.log("API REQUEST PROBLEM:");
        console.log(response.text);
        APIActions.APIFormResultFailure({
          formId: 'EarnerBadgeForm',
          message: {type: 'danger', content: "Error adding badge: " + response.text}
        });
      }
      else{
        console.log(newBadge);
        var newBadge = APIStore.addCollectionItem('earnerBadges', JSON.parse(response.text))
        if (newBadge){
          APIStore.emit('DATA_UPDATED_earnerBadges');
          APIActions.APIFormResultSuccess({
            formId: 'EarnerBadgeForm', 
            message: {type: 'success', content: "Successfully added badge to your collection."}, 
            result: newBadge 
          });
        }
        else {
          APIStore.emit('API_STORE_FAILURE');
          console.log("Failed to add " + response.text + " to earnerBadges");
        }
      } 
    });
  return req;
};

// Register with the dispatcher
APIStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      APIStore.storeInitialData()
      APIStore.emit('INITIAL_DATA_LOADED');
      break;

    case 'FORM_SUBMIT':
      if (action.formId == "EarnerBadgeForm")
        APIStore.postEarnerBadgeForm(FormStore.getFormData(action.formId));
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
