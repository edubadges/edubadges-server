var _ = require("underscore");

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

APIStore.data = {};
APIStore.getRequests = [];
APIStore.activeGetRequests = {};


APIStore.collectionsExist = function(collections){
  for (var index in collections){
    if (!APIStore.data.hasOwnProperty(collections[index]))
      return false;
  }
  return true;
};
APIStore.getCollection = function(collectionType) {
  if (APIStore.data.hasOwnProperty(collectionType))
    return APIStore.data[collectionType];
  else
    return [];
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
  if (!!collection && collection.length > 0) {
    for (var i=0; i<collection.length; i++){
      if (collection[i].hasOwnProperty(propName) && collection[i][propName] == value){
        return collection[i];
      }
    }
  }
  return {};
};
APIStore.filter = function(collectionType, propName, value){
  if (!APIStore.data.hasOwnProperty(collectionType)){
    APIStore.data[collectionType] = [];
  }
  var collection = APIStore.getCollection(collectionType);
  function match(el, index, collection){
    if (Array.isArray(value))
      return (el.hasOwnProperty(propName) && value.indexOf(el[propName]) > -1);
    else
      return (el.hasOwnProperty(propName) && el[propName] == value);
  }

  if (!!collection && collection.length > 0){
    return collection.filter(match);
  }
  else
    return [];
};

APIStore.addCollectionItem = function(collectionKey, item, isNew){
  if (!APIStore.data.hasOwnProperty(collectionKey))
    APIStore.data[collectionKey] = [];
  if (!isNew)
    APIStore.data[collectionKey].push(item);
  else
    return APIStore.replaceCollectionItem(collectionKey, item);
  return item;
}

APIStore.replaceCollectionItem = function(collectionKey, item){
  var key;
  if (collectionKey == 'earner_collections'){
    key = 'slug';
  }
  else {
    key = 'id';
  }

  foundIndex = _.findIndex(APIStore.data[collectionKey], function(el){ return el[key] == item[key]; });
  if (foundIndex != undefined)
    APIStore.data[collectionKey][foundIndex] = item;
  else
    APIStore.data[collectionKey].push(item);
  return item;
};

APIStore.partialUpdateCollectionItem = function(collectionKey, searchKey, searchValue, updateKey, updateValue){
  var foundIndex = _.findIndex(APIStore.data[collectionKey], function(el){ return el[searchKey] == searchValue; });
  if (foundIndex != undefined){
    APIStore.data[collectionKey][foundIndex][updateKey] = updateValue;
    return APIStore.data[collectionKey][foundIndex]
  }
};

APIStore.hasAlreadyRequested = function(path){
  return (APIStore.getRequests.indexOf(path) > -1);
};

APIStore.resolveActiveGet = function(collectionKey){
  if (APIStore.activeGetRequests.hasOwnProperty(collectionKey))
    delete APIStore.activeGetRequests[collectionKey];
};


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
    for (var key in _initialData){
      APIStore.data[key] = _initialData[key]
    }
  }
};


APIStore.fetchCollections = function(collectionKeys){
  var actionUrl, key;
  contexts = {
    earner_badges: {
      actionUrl: '/v1/earner/badges',
      successfulHttpStatus: [200],
      apiCollectionKey: 'earner_badges',
      replaceCollection: true
    },
    earner_collections: {
      actionUrl: '/v1/earner/collections',
      successfulHttpStatus: [200],
      apiCollectionKey: 'earner_collections',
      replaceCollection: true
    },
    issuer_issuers: {
      actionUrl: '/v1/issuer/issuers',
      successfulHttpStatus: [200],
      apiCollectionKey: 'issuer_issuers',
      replaceCollection: true
    },
    issuer_badgeclasses: {
      actionUrl: '/v1/issuer/all-badges',
      successfulHttpStatus: [200],
      apiCollectionKey: 'issuer_badgeclasses',
      replaceCollection: true
    },
  };
  for (var index in collectionKeys){
    key = collectionKeys[index];
    if (!contexts.hasOwnProperty(key))
      continue;
    actionUrl = contexts[key].actionUrl;
    if (APIStore.activeGetRequests.hasOwnProperty(key))
      continue;
    APIStore.activeGetRequests[actionUrl] = true;
    APIStore.getData(contexts[key]);
  }
};

/* getData(): a common function for GETting needed data from the API so
 * that views may be rendered.
 * Params:
 *   context: a dictionary providing information about the API endpoint,
 *            expected return results and what to do with it.
 *       - actionUrl: the path starting with / to request from
 *       - successfulHttpStatus: [200] an array of success status codes
 *       - apiCollectionKey: where to put the retrieved data
*/
APIStore.getData = function(context){
  APIStore.getRequests.push(context.actionUrl);

  var req = request.get(context.actionUrl)
    .set('X-CSRFToken', getCookie('csrftoken'))
    .accept('application/json');

  req.end(function(error, response){
    APIStore.resolveActiveGet(context.apiCollectionKey);
    console.log(response);
    if (error){
      console.log("THERE WAS SOME KIND OF API REQUEST ERROR.");
      console.log(error);
      APIStore.emit('API_STORE_FAILURE');
    }
    else if (context.successfulHttpStatus.indexOf(response.status) == -1){
      console.log("API REQUEST PROBLEM:");
      console.log(response.text);
      APIActions.APIGetResultFailure({
        message: {type: 'danger', content: response.status + " Error getting data: " + response.text}
      });
    }
    else {
      if (!APIStore.collectionsExist(context.apiCollectionKey) || context['replaceCollection']){
        APIStore.data[context.apiCollectionKey] = [];
      }

      if (Array.isArray(response.body)){
        response.body.map(function(el, i, array){
          APIStore.addCollectionItem(context.apiCollectionKey, el);
        });
      }
      else {
        APIStore.addCollectionItem(context.apiCollectionKey,response.body);
      }
      APIStore.emit('DATA_UPDATED');
    }
  });

  return req;
};


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
  for (var field in fields) {
    if (["text", "textarea", "select", "checkbox"].indexOf(fields[field].inputType) > -1 && values[field])
      req.field(field, values[field]);
    else if (["image", "file"].indexOf(fields[field].inputType) > -1 && values[field] != null)
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
      console.log("API Error: " + response.status);
      console.log(response.text);
      APIActions.APIFormResultFailure({
        formId: context.formId,
        message: {type: 'danger', content: response.status + " Error submitting form: " + response.text}
      });
    }
    else{
      var newObject = APIStore.addCollectionItem(context.apiCollectionKey, JSON.parse(response.text), (context.method == 'PUT'));
      if (newObject){
        APIStore.emit('DATA_UPDATED');
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


/* requestData: a method of making partial updates to collection records based on
 * an API interaction.
*/
APIStore.requestData = function(data, context){
  var req;
  if (context.method == 'POST')
    req = request.post(context.actionUrl);
  else if (context.method == 'DELETE')
    req = request.del(context.actionUrl);
  else if (context.method == 'PUT')
    req = request.put(context.actionUrl);
  else if (context.method == 'GET')
    req = request.get(context.actionUrl);

  req.set('X-CSRFToken', getCookie('csrftoken'))
  .accept('application/json')

  if (data)
    req.type('application/json');

  req.send(data);

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
      APIStore.emit("API_RESULT")
    }
    else{
      var newValue = typeof response.text == 'string' && response.text ? JSON.parse(response.text) : '';
      var newObject = APIStore.partialUpdateCollectionItem(context.apiCollectionKey, context.apiSearchKey, context.apiSearchValue, context.apiUpdateKey, newValue);
      if (newObject){
        APIStore.emit('DATA_UPDATED');
        APIStore.emit('DATA_UPDATED_' + context.formId);
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

      if (FormStore.genericFormTypes.indexOf(action.formType) > -1){
        var formData = FormStore.getFormData(action.formId);
        APIStore.postForm(formData.fieldsMeta, formData.formState, formData.apiContext);
      }
      else
        console.log("Unidentified form type to submit: " + action.formId);
      break;

    case 'API_SUBMIT_DATA':
      APIStore.requestData(action.apiData, action.apiContext);
      break;

    case 'API_GET_DATA':
      APIStore.getData(action.apiContext);
      break;

    case 'API_FETCH_COLLECTIONS':
      APIStore.fetchCollections(action.collectionIds);
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  addListener: APIStore.addListener,
  removeListener: APIStore.removeListener,
  hasAlreadyRequested: APIStore.hasAlreadyRequested,
  collectionsExist: APIStore.collectionsExist,
  getCollection: APIStore.getCollection,
  getCollectionLastItem: APIStore.getCollectionLastItem,
  getFirstItemByPropertyValue: APIStore.getFirstItemByPropertyValue,
  filter: APIStore.filter,
  fetchCollection: APIStore.fetchCollection
}
