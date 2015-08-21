var appDispatcher = require("../dispatcher/appDispatcher");

var createOffMenuClickAction = function(target) {
  appDispatcher.dispatch({ action: {
      type: 'CLICK_CLOSE_MENU',
      target: target
    }});
};

var createCloseModalAction = function(target) {
  appDispatcher.dispatch({ action: {
      type: 'CLOSE_MODAL',
      target: target
    }});
};

var createLinkClickAction = function(target){
  function detect_local(href){
    if (href.match(/^[\w\d]+:[\/]{0,2}/i) || href == '#')
      return false;
    return true;
  }

  var href = target.getAttribute('href');
  if (detect_local(href)){
    appDispatcher.dispatch({ action: {
        type: 'ROUTE_CHANGED',
        href: href
      }
    });
    return true;
  }
  return false;
};

var navigateLocalPath = function(path){
  appDispatcher.dispatch({
    action:{
      type: 'ROUTE_CHANGED',
      href: path
    }
  });
};

var navigateOut = function(path){
  window.location.assign(path);
};


module.exports = {
  createOffMenuClickAction: createOffMenuClickAction,
  createCloseModalAction: createCloseModalAction,
  createLinkClickAction: createLinkClickAction,
  navigateLocalPath: navigateLocalPath,
  navigateOut: navigateOut
};