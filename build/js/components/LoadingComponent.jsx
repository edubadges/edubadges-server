var React = require('react');


var LoadingComponent = React.createClass({
  render: function() {
    return (
          <span className="status_">{this.props.label || "Loading …"}</span>
    );
  }
});


module.exports = LoadingComponent;
