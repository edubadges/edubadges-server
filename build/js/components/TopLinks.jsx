var React = require('react');
var ItemsStore = require('../stores/MenuStore.js');
var Icon = require('../components/Icon.jsx').Icon;

var DropMenuItem = React.createClass({
  handleClick: function(event){
  },
  render: function() {
    return (
        <li className="dropdown_-x-item">
          <a href={this.props.url} onClick={this.handleClick}><i className={'fa fa-fw ' + this.props.iconClass}></i> {this.props.title}</a>
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
      <ul className={'dropdown_ dropdown_-toplinks dropdown_-' + this.props.title}>
        {secondLevelItems}
      </ul>
    );
  }
});


var FirstLevelItem = React.createClass({
  handleClick: function(event) {
    if ( this.props.active ){
      this.props.setOpen(null); // setOpen is a method passed in from App as a property
    }
    else {


      this.props.setOpen(this.props.title);
    }
    event.stopPropagation();
  }, 

  render: function(){
    var anyChildren = null, liClassName = '';
    if (this.props.children.length > 0) {
      anyChildren = (<MenuList items={this.props.children} title={this.props.title} clName="nav nav-second-level" key='nested-menu' />);
      liClassName = this.props.open ? 'is-open is-closable open closable' : 'closable is-closable';
    }
    var label = this.props.iconClass ? (<Icon iconName={this.props.iconClass} position="right" size="small">{this.props.label}</Icon>) : this.props.label;

    return (
      <li className={liClassName}>
        <a href={this.props.url} className={this.props.active ? 'is-active' : ''} onClick={this.handleClick} alt={this.title}>
          {label}
        </a>
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
      <ul>
        {firstLevelItems}
      </ul>
      );
  }
});


module.exports = TopLinks;
