var React = require('react');
var ItemsStore = require('../stores/MenuStore.js');
var Icon = require('../components/Icon.jsx').Icon;

var DropMenuItem = React.createClass({
  handleClick: function(event){
  },
  render: function() {
    return (
        <li>
          <a className="menu_-x-dropdownitem" href={this.props.url} onClick={this.handleClick}>{this.props.title}</a>
        </li>
      ); 
  }
});


var MenuList = React.createClass({
  render: function() {
    var secondLevelItems = this.props.items.map(function(item, i){
      return(<DropMenuItem url={item.url} title={item.title} iconClass={item.icon} key={item.title + '-item-' + i} />)
    }.bind(this));
    return (
      <div className={'menu_-x-dropdown menu_-x-dropdown-' + this.props.title}>
        <ul>
          {secondLevelItems}
        </ul>
      </div>
    );
  }
});


var FirstLevelItem = React.createClass({
  handleClick: function(event) {
    if (this.props.setOpen) {
        if ( this.props.active ){
          this.props.setOpen(null); // setOpen is a method passed in from App as a property
        }
        else {
          this.props.setOpen(this.props.title);
        }
    }
    event.stopPropagation();
  }, 

  render: function(){
    var anyChildren = null, liClassName = '', labelElement;
    var label = this.props.iconClass ? (<Icon iconName={this.props.iconClass} position="right" size="small">{this.props.label}</Icon>) : this.props.label;
    if (this.props.children.length > 0) {
      anyChildren = (<MenuList items={this.props.children} title={this.props.title} clName="nav nav-second-level" key='nested-menu' />);
      liClassName = this.props.open ? 'is-open is-closable open closable' : 'closable is-closable';
      labelElement = (<span
          className={this.props.active ? 'menu_-x-item is-active' : 'menu_-x-item'}
          onClick={this.handleClick} alt={this.title}>
        {label}
      </span>);
    }
    else {
      labelElement = (<a href={this.props.url} className={this.props.active ? 'menu_-x-item is-active' : 'menu_-x-item'} onClick={this.handleClick} alt={this.title}>
        {label}
      </a>);
    }

    return (
      <li className={liClassName}>
        {labelElement}
        {anyChildren}
      </li>
    );
  }
});


var TopLinks = React.createClass({
  render: function() {
    var firstLevelItems = this.props.items.map(function(item, i) {
      var label = this.props.showLabels ? item.title : "";
      return (
          <FirstLevelItem 
            url={item.url} 
            key={'top-menu-' + i} 
            title={item.title}
            label={label} 
            iconClass={item.icon} 
            children={item.children} 
            active={this.props.active == item.title ? true : false}
            open={this.props.open == item.title ? true : false}
            setOpen={this.props.setOpen}
          />
        );
    }.bind(this));
    return (
      <ul className="menu_">
        {firstLevelItems}
      </ul>
      );
  }
});


module.exports = TopLinks;
