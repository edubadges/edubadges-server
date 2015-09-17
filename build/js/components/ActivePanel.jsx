var React = require('react');
var EarnerBadge = require('./BadgeDisplay.jsx').EarnerBadge;
var BasicAPIForm = require('./Form.jsx').BasicAPIForm;

var Dispatcher = require('../dispatcher/appDispatcher');
var ClickActions = require('../actions/clicks');

var FormStore = require('../stores/FormStore');
var FormConfigStore = require('../stores/FormConfigStore');
var MenuStore = require('../stores/MenuStore');


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
  getDefaultProps: function(){
    return {
      modal: false
    };
  },
  getInitialState: function(){
    return {
      open: (!this.props.modal)
    };
  },
  componentDidMount: function(){
    if (this.props.modal)
      MenuStore.addListener('CLOSE_MODAL', this.clearActivePanel);
  },
  componentWillUnmount: function(){
    MenuStore.removeListener('CLOSE_MODAL', this.clearActivePanel);
  },
  componentDidUpdate(prevProps, prevState){
    if (!prevProps.type && this.props.type && this.isMounted()){
      this.setState({open: true});
    }
  },
  updateActivePanel: function(update){
    this.props.updateActivePanel(this.props.viewId, update);
  },
  clearActivePanel: function(){
    if (this.isMounted() && this.state.open) {
      this.setState({open: false});
      setTimeout(
          function(){this.props.clearActivePanel(this.props.viewId);}.bind(this), 0
      );
    }
  },
  render: function() {
    if (!this.state.open)
      return <div className="active-panel empty" />;

    var formProps = {};
    var closeAction = this.props.clearActivePanel ? {
      onClick: this.clearActivePanel,
      label: "Close",
      buttonClass: "btn-default"
    } : null;
    var panelActions = [closeAction];

    var genericFormTypes = FormStore.genericFormTypes;

    if (genericFormTypes.indexOf(this.props.type) > -1){
      var formProps = FormConfigStore.getConfig(
        this.props.type,
        {
          formId: this.props.type + this.props.formKey,
          formType: this.props.type,
          handleCloseForm: this.props.clearActivePanel ? this.clearActivePanel : null,
          submitImmediately: this.props.submitImmediately
        },
        this.props
      );


      FormStore.getOrInitFormData(this.props.type + this.props.formKey, formProps);
      var wrapperClass = "active-panel api-form image-upload-form clearfix";

      if (this.props.modal){
        return (
          <div className="modal" style={{display: "block"}}>
            <div className={wrapperClass + ' modal-dialog'}>
              <div className="modal-content closable">
                <div className="modal-body container-fluid">
                  {this.props.title ? (<h3>{this.props.title}</h3>) : null}
                  <BasicAPIForm {...formProps} />
                </div>
              </div>
            </div>
          </div>
        );
      }


      return (
        <div className={wrapperClass + ' non-modal'}>
          <div className="container-fluid">
            <BasicAPIForm {...formProps} />
          </div>
        </div>
      );
    }

    else if (this.props.type == "ChildComponent"){
      return (
          <div className="modal" style={{display: "block"}}>
            <div className={wrapperClass + ' modal-dialog'}>
              <div className="modal-content closable">
                <div className="modal-body container-fluid">
                  <button className="dialog_-x-close" onClick={this.clearActivePanel}>
                    <span className="icon_ icon_-notext icon_-close">Close</span>
                  </button>

                  {this.props.title ? (<h3>{this.props.title}</h3>) : null}
                  {this.props.content.children}
                  <div className="control_">
                    <button className="button_ button_-secondary" onClick={this.clearActivePanel}>Close</button>
                  </div>
                  {this.props.content.actions}
                </div>
              </div>
            </div>
          </div>
        );
    }


    // Catch unknown view types
    return <div className="active-panel empty" />;
  }
});


module.exports = ActivePanel;
