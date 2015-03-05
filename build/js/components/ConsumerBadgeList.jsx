var React = require('react');

// Components
var OpenBadgeList = require('./OpenBadgeList.jsx');

/* 
  Earner Badge List: A wrapper around OpenBadgeList that updates active badge
  within an activePanel through a passed in setter.
*/
var ConsumerBadgeList = React.createClass({
  setActiveBadgeId: function(id){
    this.props.updateActivePanel(
      this.props.viewId,
      { type: "OpenBadgeDisplay", content: { badgeId: id, detailLevel: 'full' }}
    );
  },
  activateUploadForm: function(){
    actionCreator.updateActiveAction(
      this.props.viewId,
      { type: "ConsumerBadgeForm", content: { badgeId: null } }
    );
  },
  clearActiveAction: function(){
    actionCreator.clearActiveAction(this.props.viewId);
  },
  render: function() {
    return (
      <div className="consumer-badges-list">
        <OpenBadgeList badgeList={this.props.consumerBadges} activeBadgeId={this.props.activeBadgeId} setActiveBadgeId={this.setActiveBadgeId} />
      </div>
    );
  }
});


module.exports = ConsumerBadgeList;
