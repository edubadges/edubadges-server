var React = require('react');


var MainComponent = React.createClass({
  render: function() {
    return (
      <div className="main-component clearfix">
        {this.props.children}
      </div>
    );
  }
});


module.exports = MainComponent;
