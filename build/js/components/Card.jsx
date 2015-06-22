var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

var CardActions = React.createClass({
  render: function() {
    var actions = this.props.actions.map(function(item, index){
      return (
        <div className={"card-action " + item.actionClass} key={"action-" + index}>
          <a href={item.actionUrl}>
            <i className={'fa fa-fw ' + item.iconClass}></i>
            {item.title}
          </a>
        </div>
      );
    }.bind(this));
    return (
      <div className='card-actions clearfix'>
        {actions}
      </div>
    );
  }
});


var Card = React.createClass({
  getDefaultProps: function() {
    return {
      title: '',
      actions: [],
      onClick: function(e){},
      columnClasses: "col-xs-6 col-sm-4 col-lg-3"
    };
  },
  render: function() {
    var headerImage = this.props.headerImageUrl ? (<div className="headerImage"><a href={this.props.titleUrl || "#"}><img src={this.props.headerImageUrl} /></a></div>) : '';
    var title = this.props.titleUrl ? this.props.title : (<a href={this.props.titleUrl}>{this.props.title}</a>);

    return (
      <div className={"card clearfix " + this.props.columnClasses} onClick={this.props.onClick}>
        {headerImage}
        <div className="title">{title}</div>
        <CardActions actions={this.props.actions} />
        <div className="content">
          {this.props.children}
        </div>
      </div>
    );
  }
});


module.exports = Card;
