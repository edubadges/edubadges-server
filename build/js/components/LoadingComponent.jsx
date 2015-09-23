var React = require('react');


var LoadingComponent = React.createClass({
  render: function() {
    return (<p className="status_">{this.props.label || "Loading …"}</p>);
  }
});


module.exports = LoadingComponent;
