var React = require('react');


var ActivePanelUpdateButton = React.createClass({
  handleClick: function(){
    if (this.props.activePanel && this.props.activePanel.type == this.props.updateObject.type)
      this.props.clearActivePanel(this.props.viewId);
    else
      this.props.updateActivePanel(this.props.viewId, this.props.updateObject);
  },
  render: function() {
    var icon = (this.props.activePanel && this.props.activePanel.type == this.props.updateObject.type) ? 'fa-times' : this.props.icon;

    return (
      <button className={"btn btn-" + this.props.buttonType} onClick={this.handleClick}>
        <i className={'fa fa-fw ' + icon}></i>
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
            clearActivePanel={this.props.clearActivePanel}
            updateObject={item.activePanelCommand}
            activePanel={this.props.activePanel}
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


var HeadingBar = React.createClass({
  render: function() {
    return (
      <div className="action-bar clearfix">
        <div className="main-component-content-title col-xs-12">
          <h3>{this.props.title}</h3>
        </div>
      </div>
    );
  }
});


module.exports = {
  ActionBar: ActionBar,
  HeadingBar: HeadingBar
};
