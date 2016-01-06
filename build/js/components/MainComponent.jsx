var React = require('react');
var LoadingComponent = require('../components/LoadingComponent.jsx');


var MainComponent = React.createClass({
  getDefaultProps: function() {
    return {
      dependenciesLoaded: true,
      mainClassName: "wrap_ wrap_-borderbottom l-wrapper l-wrapper-inset"
    };
  },
  render: function() {
    var spinner = (<div className="message_" style={{marginTop: '50px'}}>
        <LoadingComponent/></div>);
    return (
      <main className={this.props.mainClassName}>
        <div className={"x-owner " + this.props.className}>
          {this.props.dependenciesLoaded ? this.props.children : spinner}
        </div>
      </main>
    );
  }
});


module.exports = MainComponent;
