var React = require('react');
var _ = require('lodash');

// Stores
var FormStore = require('../stores/FormStore');

// Actions
var FormActions = require('../actions/forms');

/**
 * Usage:
 *


var dialog = (
 <Dialog dialogId="unique-dialog-id">
    <p>I am the contents of the dialog that will be shown</p>
 </Dialog>);

var button = (
 <DialogOpener dialog={dialog} dialogId="unique-dialog-id">
    <button>click me to open the dialog</button>
 </DialogOpener>);

 */




/*
 *
 * DialogElement js helper
 *
 */

// !!! NOTE: This is not a react component.  It's a plain js object that manages a react component

function DialogElement(reactComponent, dialogId, dialogClass) {
    this.reactComponent = reactComponent;
    this.dialogId = dialogId;

    this.domNode = document.createElement('dialog');
    this.domNode.className = ( ! dialogClass) ? "dialog_" : "dialog_ "+ dialogClass;
    this.domNode.id = dialogId;
    document.body.appendChild(this.domNode);

    if (!this.domNode.showModal)
        dialogPolyfill.registerDialog(this.domNode);
}
DialogElement.prototype.attach = function() {

}
DialogElement.prototype.update = function() {
    React.render(this.reactComponent, this.domNode, function() {});
};
DialogElement.prototype.destroy = function() {
    React.unmountComponentAtNode(this.domNode);
    this.domNode.parentNode.removeChild(this.domNode);
};
DialogElement.prototype.closeDialog = function() {
    this.domNode.close();
    this.domNode.classList.remove('is-visible');
};
DialogElement.prototype.showDialog = function() {
    this.domNode.showModal();
    this.domNode.classList.add('is-visible');
};


/*
 *
 * DialogOpener - React component that wraps the target that will open the dialog
 *
 */

var DialogOpener = React.createClass({
    propTypes: {
        dialog: React.PropTypes.node.isRequired,
        dialogId: React.PropTypes.string.isRequired,
        handleClick: React.PropTypes.func,
    },

    componentDidMount: function() {
        this.dialog = new DialogElement(this.props.dialog, this.props.dialogId, this.props.dialogClass);
        this.dialog.update();
    },

    componentWillUnmount: function() {
        this.dialog.destroy();
    },

    componentDidUpdate: function(prevProps, prevState) {
        this.dialog.update();
    },

    handleClick: function(e) {
        this.dialog.showDialog();

        if (this.props.handleClick) {
            this.props.handleClick(e);
        }
    },

    render: function() {
        var divProps = _.omit(this.props, 'dialog', 'dialogId');
        return (
            <div onClick={this.handleClick} {...divProps}>
                {this.props.children}
            </div>);
    }
});

var Dialog = React.createClass({
    propTypes: {
        dialogId: React.PropTypes.string.isRequired,
        hideControls: React.PropTypes.bool,
        formId: React.PropTypes.string,
        handleCloseDialog: React.PropTypes.func,
    },

    getInitialState: function() {
        return {
            formWasCompleted: false,
        };
    },

    componentDidMount: function() {
        if (this.props.formId) {
            FormStore.addListener('FORM_DATA_UPDATED_'+ this.props.formId, this.handleFormDataUpdated);
        }
    },

    componentWillUnmount: function() {
        if (this.props.formId) {
            FormStore.removeListener('FORM_DATA_UPDATED_'+ this.props.formId, this.handleFormDataUpdated);
        }
    },

    handleFormDataUpdated: function() {
        var formData = FormStore.getFormData(this.props.formId);
        if (formData.formState.actionState === "complete") {
            this.setState({'formWasCompleted': true});
        }
    },

    closeDialog: function() {
        var formData = FormStore.getFormData(this.props.formId);
        var messageType = _.get(formData, 'formState.message.type');
        if (this.state.formWasCompleted || messageType === 'danger') {
            FormActions.resetForm(this.props.formId);
            this.setState({formWasCompleted: false});
        }

        if (this.props.handleCloseDialog) {
            return this.props.handleCloseDialog();
        }

        var dialog = document.getElementById(this.props.dialogId)
        if (dialog) {
            if (!dialog.showModal)
                dialogPolyfill.registerDialog(dialog);
            dialog.close();
            dialog.classList.remove('is-visible');
        } else {
            console.log("Unable to find dialog with dialogId="+this.props.dialogId)
        }
    },

    render: function() {
        var divProps = _.omit(this.props, ['dialogId', 'actions'])
        var controls = (this.props.hideControls || this.state.formWasCompleted) ? "" : (
            <div className="control_">
                <button className="button_ button_-secondary" onClick={this.closeDialog}>Close</button>
                {this.props.actions}
            </div>);
        var children = (this.props.noContent) ? this.props.children : (
                <div className="dialog_-x-content">
                    {this.props.children}
                </div>);

        return (
            <div {...divProps}>
                <button className="dialog_-x-close" onClick={this.closeDialog}>
                    <span className="icon_ icon_-notext icon_-close">Close</span>
                </button>
                {children}
                {controls}
            </div>);
    }

});


module.exports = {
    DialogElement: DialogElement,
    DialogOpener: DialogOpener,
    Dialog: Dialog,
};
