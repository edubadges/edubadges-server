var React = require('react');

var LoadingIcon = React.createClass({
  render: function(){
    return (
      <div className="loading-icon" >
        <span className='sr-only'>Loading...</span>
      </div>
    )
  }
});


module.exports = {
  LoadingIcon: LoadingIcon
}