var React = require('react');

var ActivePanelUpdateButton = React.createClass({
  handleClick: function(){
    this.props.updateActivePanel(this.props.viewId, this.props.updateObject);
  },
  render: function() {
    return (
      <button className={"btn btn-" + this.props.buttonType} onClick={this.handleClick}>
        <i className={'fa fa-fw ' + this.props.icon}></i>
        {this.props.title}
      </button>
    );
  }
});

var ActionBar = React.createClass({
  render: function() {
    var items = this.props.items.map(function(item, index){
      return (
        <li className="action-bar-item" key={"action-bar-item-" + index}>
          <ActivePanelUpdateButton
            viewId={this.props.viewId}
            buttonType={item.buttonType}
            title={item.title}
            icon={item.icon}
            updateActivePanel={this.props.updateActivePanel}
            updateObject={item.activePanelCommand}
          />
        </li>
      );
    }.bind(this));
    return (
      <div className="action-bar clearfix">
        <div className="main-component-content-title col-xs-6">
          <h3>{this.props.title}</h3>
        </div>
        <ul className="col-xs-6">
          {items}
        </ul>
      </div>
    );
  }
});


module.exports = ActionBar;
