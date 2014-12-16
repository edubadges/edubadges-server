React = require('react');

var MenuItem = React.createClass({
  getInitialState: function() {
    return {expanded: false, visible: true};
  },
  handleClick: function(event) {
    this.setState({expanded: !this.state.expanded});
  }, 
  render: function(){
    var anyChildren = ""
    var expandButton = ""
    if (this.props.children.length > 0) {
      expandButton = <span className="fa arrow"></span>
      anyChildren = <MenuList items={this.props.children} clName="nav nav-second-level" key='nested-menu' />
    }
    return (
      <li className={this.state.expanded ? 'nav-menu-item expanded-true active' : 'nav-menu-item expanded-false' }>
        <a href={this.props.url} onClick={this.handleClick}><i className={'fa fa-fw ' + this.props.iconClass}></i>{this.props.title}{expandButton}</a>
          {anyChildren}
      </li>
    );
  }
});


var MenuList = React.createClass({
  render: function(){
    var items = this.props.items.map(function(item, i) {
      return (<MenuItem url={item.url} key={'menu-item-' + i} title={item.title} iconClass={item.icon} children={item.children} />);
    }.bind(this))
    return (
      <ul className={this.props.clName}>
        {items}
      </ul>
    );
  }
});


var Menu = React.createClass({
  getDefaultProps: function() {
    return { 
      items: [
        { title: "Earn", url: "/earn", icon: "fa-certificate", children: [] },
        { title: "Issue", url: "#", icon: "fa-mail-forward", children: [
          { title: "Award Badges", url: "/issue", icon: "fa-bookmark", children: [] },
          { title: "Print Certificates", url: "/certificates", icon: "fa-photo", children: []}
        ]},
        { title: "Understand", url: "/understand", icon: "fa-info-circle", children: [] }
      ]
    }
  },
  render: function() {
    return (
      <div className="sidebar-nav navbar-collapse">
        <MenuList items={this.props.items} clName="nav" />
      </div>
    )
  }
});

React.render(
  <Menu />,
  document.getElementById('page-wrapper')
);