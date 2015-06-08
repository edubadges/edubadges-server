var React = require('react');

// Components
var OpenBadgeList = require('./OpenBadgeList.jsx');

/* 
  Earner Badge List: A wrapper around OpenBadgeList that updates active badge
  within an activePanel through a passed in setter.
*/
var EarnerBadgeList = React.createClass({
  render: function() {
    var badges, moreLink;
    if (this.props.perPage && this.props.badges.length > this.props.perPage){
      badges = this.props.badges.slice(0, this.props.perPage);
      moreLink = (<div className="more-link">
        (<a href={this.props.moreLink}>
          {this.props.badges.length - this.props.perPage} more...
        </a>)
      </div>);
    }
    else {
      badges = this.props.badges;
      moreLink = "";
    }

    return (
      <div className="earner-badges-list">
        <OpenBadgeList badges={badges} clickEmptyBadge={this.props.clickEmptyBadge}/>
        {moreLink}
      </div>
    );
  }
});


module.exports = EarnerBadgeList;
