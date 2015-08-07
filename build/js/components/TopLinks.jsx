var React = require('react');
var ItemsStore = require('../stores/MenuStore.js');

var DropMenuItem = React.createClass({
  handleClick: function(event){
  },
  render: function() {
    return (
        <li>
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
      <ul className={'dropdown-menu dropdown-' + this.props.title}>
        {secondLevelItems}
      </ul>
    );
  }
});


var FirstLevelItem = React.createClass({
  handleClick: function(event) {
    if ( this.props.active ){
      this.props.setActive(null); // setActive is a method passed in from App as a property
    }
    else {
      this.props.setActive(this.props.title);
    }
    event.stopPropagation();
  }, 

  render: function(){
    var anyChildren = "", downCaret = ""
    if (this.props.children.length > 0) {
      anyChildren = <MenuList items={this.props.children} title={this.props.title} clName="nav nav-second-level" key='nested-menu' />
      downCaret = (<i className='fa fa-fw fa-caret-down'></i>);
    }
    return (
      <li className={this.props.active ? 'nav-menu-item expanded-true active open' : 'nav-menu-item' }>
        <a href={this.props.url} onClick={this.handleClick} alt={this.title}>
          <label>{this.props.label}</label>
          {downCaret}
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
            setActive={this.props.setActive}
          />
        );
    }.bind(this));
    return (
      <ul className="nav navbar-top-links">
        {firstLevelItems}
      </ul>
      );
  }
});


module.exports = TopLinks;
