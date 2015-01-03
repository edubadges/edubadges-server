var appDispatcher = require("../dispatcher/appDispatcher");

var createOffMenuClickAction = function(target) {
  appDispatcher.dispatch({ action: {
      type: 'CLICK_CLOSE_MENU',
      target: target
    }});
}

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
}


module.exports.createOffMenuClickAction = createOffMenuClickAction;
module.exports.createLinkClickAction = createLinkClickAction;