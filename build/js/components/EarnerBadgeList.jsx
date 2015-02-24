var React = require('react');

// Components
var OpenBadgeList = require('./OpenBadgeList.jsx');

/* 
  Earner Badge List: A wrapper around OpenBadgeList that updates active badge
  within an activePanel through a passed in setter.
*/
var EarnerBadgeList = React.createClass({
  setActiveBadgeId: function(id){
    this.props.updateActivePanel(
      this.props.viewId,
      { type: "OpenBadgeDisplay", content: { badgeId: id, detailLevel: 'detail' }}
    );
  },
  activateUploadForm: function(){
    actionCreator.updateActiveAction(
      this.props.viewId,
      { type: "EarnerBadgeForm", content: { badgeId: null } }
    );
  },
  clearActiveAction: function(){
    actionCreator.clearActiveAction(this.props.viewId);
  },
  render: function() {
    return (
      <div className="earner-badges-list">
        <OpenBadgeList badgeList={this.props.earnerBadges} activeBadgeId={this.props.activeBadgeId} setActiveBadgeId={this.setActiveBadgeId} />
      </div>
    );
  }
});


module.exports = EarnerBadgeList;
