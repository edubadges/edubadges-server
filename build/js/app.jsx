var React = require('react');
var Dispatcher = require('./dispatcher/appDispatcher');
var App = require('./components/App.jsx');
var clickActions = require('./actions/clicks');
require('./polyfills');

React.render(
  <App history={true} />,
  document.getElementById('app')
);
 

var clickHandler = function(e){
  var target = e.target;
  closestLink = target.closest('a');

  // Handle clicking links to either navigate within the single page app or make a fresh request
  if (closestLink) {
    clickActions.createLinkClickAction(closestLink)
    e.preventDefault();
    e.stopPropagation();
  }

  // Close any open menus.
  if (!target.closest('.closable'))
    clickActions.createOffMenuClickAction(target);
};
document.onclick = clickHandler;