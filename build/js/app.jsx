var React = require('react');
var Dispatcher = require('./dispatcher/appDispatcher');
var App = require('./components/App.jsx');
var clickActions = require('./actions/clicks');


React.render(
  <App history={true} />,
  document.getElementById('app')
);
 
 
$('a').on('click', function(e){
  if(clickActions.createLinkClickAction(e.currentTarget)){
    e.preventDefault();
    e.stopPropagation();
  }
});

$(document).on('click', function(e){
  target = $(e.target);
  if (!target.closest("li.open").length)
    clickActions.createOffMenuClickAction(target);
}); 