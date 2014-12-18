var React = require('react');
var Dispatcher = require('./dispatcher/appDispatcher');
var TopLinks = require('./components/TopLinks.jsx');
var SideBarNav = require('./components/SideBarNav.jsx');
var clickActions = require('./actions/clicks');

React.render(
  <TopLinks />,
  document.getElementById('top-links')
);


React.render(
  <SideBarNav />,
  document.getElementById('sidebar')
);
 
 
$(document).on('click', function(e){
  if (!$(e.target).closest("li.open").length)
    clickActions.createOffMenuClickAction($(e.target));
}); 