var React = require('react');
var LoadingComponent = require('../components/LoadingComponent.jsx');


var MainComponent = React.createClass({
  getDefaultProps: function() {
    return {
      dependenciesLoaded: true
    };
  },
  render: function() {
    var spinner = <LoadingComponent/>
    return (
      <div>
        {this.props.dependenciesLoaded ? this.props.children : spinner}
      </div>
    );
  }
});


module.exports = MainComponent;
