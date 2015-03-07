var React = require('react');
var EarnerBadge = require('./BadgeDisplay.jsx').EarnerBadge;
var BadgeUploadForm = require('./Form.jsx').BadgeUploadForm;
var FormStore = require('../stores/FormStore');

var PanelActions = React.createClass({
  /* Define a click handler, a label, and a class for each action.
  props = {
    onClick: this.clearActivePanel,
    label: "Close",
    buttonClass: "btn-default"
  }
  */
  render: function() {
    if (!this.props.actions)
      return null;
    console.log(this.props.actions);
    var actions = this.props.actions.map(function(item, i){
      return (
        <button className={'btn ' + item.buttonClass} onClick={item.onClick} key={"panel-action-" + i}>
          {item.label}
        </button>
      );
    });
    return (
      <div className='panel-actions clearfix'>
        {actions}
      </div>
    );
  }
});

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

    var closeAction = {
      onClick: this.clearActivePanel,
      label: "Close",
      buttonClass: "btn-default"
    };
    var panelActions = [closeAction];

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

          <PanelActions
            actions={panelActions}
          />
        </div>
      );
    }

    else if (this.props.type == "EarnerBadgeForm"){
      defaultFormState = {
        recipient_input: this.props.recipientIds[0], 
        earner_description: '' 
      }
      return (
        <div className="active-panel earner-badge-form clearfix">
          <BadgeUploadForm
            action='/api/earner/badges'
            formId={this.props.type}
            recipientIds={this.props.recipientIds}
            pk={typeof this.props.badgeId !== 'undefined' ? this.props.badgeId : 0}
            initialState={FormStore.getOrInitFormData(this.props.type, defaultFormState)}
          />
          <PanelActions
            actions={panelActions}
          />
        </div>
      );
    }

    else if (this.props.type == "IssuerNotificationForm"){
      var formProps = {
        formId: this.props.type
      }
      formProps['pk'] = 0; //typeof this.props.content['id'] === 'object' ? 0: parseInt(id);
      formProps['initialState'] = FormStore.getOrInitFormData(
        formProps.formId,
        { email: "", url: "", actionState: "ready" }
      );
      return (
        <div className="active-panel earner-badge-form clearfix">
          <div className="container-fluid">
            <IssuerNotificationForm {...formProps} />
          </div>
        </div>
      );
    }

    else if (this.props.type == "ConsumerBadgeForm"){
      defaultFormState = {
        recipient_input: ''
      }
      return (
        <div className="active-panel consumer-badge-form clearfix">
          <BadgeUploadForm
            formId={this.props.type}
            recipientIds={this.props.recipientIds}
            pk={typeof this.props.badgeId !== 'undefined' ? this.props.badgeId : 0}
            initialState={FormStore.getOrInitFormData(this.props.type, defaultFormState)}
          />
          <PanelActions
            actions={panelActions}
          />
        </div>
      );
    }

    // Catch unknown view types
    return <div className="active-panel empty" />;
  }
});


module.exports = ActivePanel;
