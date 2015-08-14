var React = require('react');

Crumb = React.createClass({
  render: function() {
    return (
      <li className="crumb">
        <a href={this.props.url}>{this.props.name}</a>
      </li>
    );
  }
});
BreadCrumbs = React.createClass({
  getDefaultProps: function() {
    return {
      items: []
    };
  },
  render: function() {
    var crumbs = this.props.items.map(function(item, i){
      return(
        <Crumb name={item.name} url={item.url} key={'crumb-' + i} />
      );
    });
    return (
      <div className="breadcrumb-wrapper">
        <ul className="breadcrumb">
            {crumbs}
        </ul>
      </div>
    );
  }
});

module.exports = BreadCrumbs;