
var _ = require('lodash');
var React = require('react');


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

function DialogElement(reactComponent, dialogId) {
    this.reactComponent = reactComponent;
    this.dialogId = dialogId;

    this.domNode = document.createElement('dialog');
    this.domNode.className = "dialog_";
    this.domNode.id = dialogId;
    document.body.appendChild(this.domNode);

    dialogPolyfill.registerDialog(this.domNode);
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
        dialogId: React.PropTypes.string.isRequired
    },
    componentDidMount: function() {
        this.dialog = new DialogElement(this.props.dialog, this.props.dialogId)
    },
    componentWillUnmount: function() {
        this.dialog.destroy();
    },
    componentDidUpdate: function() {
        this.dialog.update();
    },

    openDialog: function() {
        this.dialog.showDialog();
    },


    render: function() {
        var divProps = _.omit(this.props, 'dialog', 'dialogId');
        return (
            <div onClick={this.openDialog} {...divProps}>
                {this.props.children}
            </div>);

    }

});

var Dialog = React.createClass({
    propTypes: {
        dialogId: React.PropTypes.string.isRequired
    },

    closeDialog: function() {
        var dialog = document.getElementById(this.props.dialogId)
        if (dialog) {
            dialogPolyfill.registerDialog(dialog);
            dialog.close();
            dialog.classList.remove('is-visible');
        } else {
            console.log("Unable to find dialog with dialogId="+this.props.dialogId)
        }
    },

    render: function() {
        return (
            <div>
                <button className="dialog_-x-close" onClick={this.closeDialog}>
                    <span className="icon_ icon_-notext icon_-close">Close</span>
                </button>
                <div className="dialog_-x-content">
                    {this.props.children}
                </div>
                <div className="control_">
                    <button className="button_ button_-secondary" onClick={this.closeDialog}>Close</button>
                </div>
            </div>);
    }

});


module.exports = {
    DialogElement: DialogElement,
    DialogOpener: DialogOpener,
    Dialog: Dialog,
};
