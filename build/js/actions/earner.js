var appDispatcher = require("../dispatcher/appDispatcher");


var submitEarnerBadgeForm = function(data, image) {
  console.log("ACTION CREATOR: SUBMIT_EARNER_BADGE_FORM image");
  console.log(image);
  console.log(image == null);
  console.log(typeof image);
  appDispatcher.dispatch({ action: {
      type: 'SUBMIT_EARNER_BADGE_FORM',
      data: data, 
      image: image
    }});
}


module.exports.submitEarnerBadgeForm = submitEarnerBadgeForm;
