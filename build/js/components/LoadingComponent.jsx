var React = require('react');


var LoadingComponent = React.createClass({
  render: function() {
    return (
      <div className="loading-component-spinner clearfix">
        <p>{this.props.label || "Loading..."}</p>
        <p><img src="/static/images/ajax-loader.gif" alt="Please wait while the necessary content loads." /></p>
      </div>
    );
  }
});


module.exports = LoadingComponent;
