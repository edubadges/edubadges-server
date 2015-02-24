var React = require('react');
var MenuList = require

var SecondaryMenu = React.createClass({
  render: function() {
    var items = this.props.items.map(function(item, index){
      return (
        <li className="menu-item" key={"secondary-menu-item-" + index}>
          <i className={'fa fa-fw ' + item.icon}></i>
          <a href={item.url}>{item.title}</a>
        </li>
      );
    });
    return (
      <ul className="secondary-menu">
        {items}
      </ul>
    );
  }
});


module.exports = SecondaryMenu;
