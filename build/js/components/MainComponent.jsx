var React = require('react');
var LoadingComponent = require('../components/LoadingComponent.jsx');


var MainComponent = React.createClass({
  getDefaultProps: function() {
    return {
      dependenciesLoaded: true
    };
  },
  render: function() {
    var spinner = (<div className="message_" style={{marginTop: '50px'}}>
        <LoadingComponent/></div>);
    return (
      <div className={( ! this.props.className) ? "x-owner" : "x-owner "+ this.props.className}>
        {this.props.dependenciesLoaded ? this.props.children : spinner}
      </div>
    );
  }
});


module.exports = MainComponent;
