var appDispatcher = require("../dispatcher/appDispatcher");

var createOffMenuClickAction = function(target) {
  appDispatcher.dispatch({ action: {
      type: 'CLICK_CLOSE_MENU',
      target: target
    }});
}

module.exports.createOffMenuClickAction = createOffMenuClickAction;