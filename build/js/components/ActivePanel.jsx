var React = require('react');
var EarnerBadge = require('./BadgeDisplay.jsx').EarnerBadge;
var EarnerBadgeForm = require('./Form.jsx').EarnerBadgeForm;
var FormStore = require('../stores/FormStore');

var ActivePanel = React.createClass({
  updateActivePanel: function(update){
    this.props.updateActivePanel(this.props.viewId, update);
  },
  clearActivePanel: function(){
    this.props.clearActivePanel(this.props.viewId);
  },
  render: function() {
    if (!('type' in this.props))
      return <div className="active-panel empty" />;

    // TODO: refactor for "EarnerBadgeDisplay" instead of "OpenBadgeDisplay"
    if (this.props.type == "OpenBadgeDisplay"){
      return (
        <div className="active-panel open-badge-display clearfix">
          <EarnerBadge 
            key={"active-badge-" + this.props.badgeId}
            id={this.props.badgeId}
            display={this.props.detailLevel}
            badge={this.props.badge.badge} 
            earner={this.props.badge.badge.recipient_input}
            isActive={true}
            setActiveBadgeId={this.clearActivePanel}
          />

        </div>
      );
    }

    if (this.props.type == "EarnerBadgeForm"){
      defaultFormState = {
        recipient_input: this.props.recipientIds[0], 
        earner_description: '' 
      }
      return (
        <div className="active-panel earner-badge-form clearfix">
          <EarnerBadgeForm
            formId={this.props.type}
            recipientIds={this.props.recipientIds}
            pk={typeof this.props.badgeId !== 'undefined' ? this.props.badgeId : 0}
            initialState={FormStore.getOrInitFormData(this.props.type, defaultFormState)}
          />
        </div>
      );
    }

    // Catch unknown view types
    return <div className="active-panel empty" />;
  }
});


module.exports = ActivePanel;
