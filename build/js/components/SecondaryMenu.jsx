var React = require('react');
var MenuList = require

var SecondaryMenu = React.createClass({
  render: function() {
    var items = this.props.items.map(function(item, index){
      return (
        <li className="nav-menu-item" key={"secondary-menu-item-" + index}>
          <a href={item.url}>
            <i className={'fa fa-fw ' + item.icon}></i>
            {item.title}
          </a>
        </li>
      );
    });
    return (
      <ul className="secondary-menu nav navbar navbar-top-links">
        {items}
      </ul>
    );
  }
});


module.exports = SecondaryMenu;
