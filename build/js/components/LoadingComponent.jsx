var React = require('react');


var LoadingComponent = React.createClass({
  getDefaultProps: function() {
      return {
          label: "Loading..."
      };
  },
  render: function() {
    return (
          <span className="status_">{this.props.label}</span>
    );
  }
});


module.exports = LoadingComponent;
