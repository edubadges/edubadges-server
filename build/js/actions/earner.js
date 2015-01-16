var appDispatcher = require("../dispatcher/appDispatcher");


var submitEarnerBadgeForm = function(data, image) {
  appDispatcher.dispatch({ action: {
      type: 'SUBMIT_EARNER_BADGE_FORM',
      data: data, 
      image: image
    }});
}


module.exports.submitEarnerBadgeForm = submitEarnerBadgeForm;
