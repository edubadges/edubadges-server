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
      this.props.setActive(null);
    }
    else {
      this.props.setActive(this.props.title );
    }
    event.stopPropagation();
  }, 
  render: function(){
    var anyChildren = ""
    if (this.props.children.length > 0) {
      anyChildren = <MenuList items={this.props.children} title={this.props.title} clName="nav nav-second-level" key='nested-menu' />
    }
    return (
      <li className={this.props.active ? 'nav-menu-item expanded-true active open' : 'nav-menu-item' }>
        <a href={this.props.url} onClick={this.handleClick} alt={this.title}><i className={'fa fa-fw ' + this.props.iconClass}></i> <i className='fa fa-fw fa-caret-down'></i></a>
          {anyChildren}
      </li>
    );
  }
});


var TopLinks = React.createClass({
  getDefaultProps: function() {
    return ItemsStore.getAllItems('topMenu');
  },
  getInitialState: function() {
    return {
      active: null 
    };
  },
  componentDidMount: function() {
    ItemsStore.addListener('uncaught_document_click', this._hideMenu);
  },
  setActive: function(key){
    this.setState({active: key});
  },
  render: function() {
    var firstLevelItems = this.props.items.map(function(item, i) {
      return (
          <FirstLevelItem 
            url={item.url} 
            key={'top-menu-' + i} 
            title={item.title} 
            iconClass={item.icon} 
            children={item.children} 
            active={ this.state.active == item.title ? true : false } 
            setActive={this.setActive} 
          />
        );
    }.bind(this));
    return (
      <ul className="nav navbar-top-links">
        {firstLevelItems}
      </ul>
      );
  },
  _hideMenu: function(){
    if (this.state.active != null)
      this.setState({active: null});
  }
});


module.exports = TopLinks;
