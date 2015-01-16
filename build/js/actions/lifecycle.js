var appDispatcher = require("../dispatcher/appDispatcher");

var appWillMount = function() {
  appDispatcher.dispatch({ action: {
      type: 'APP_WILL_MOUNT'
    }});
}


module.exports.appWillMount = appWillMount;
