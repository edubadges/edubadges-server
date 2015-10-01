var React = require('react');
var _ = require('lodash');

// Stores
var FormStore = require('../stores/FormStore');

// Actions
var FormActions = require('../actions/forms');


var Button = React.createClass({
    propTypes: {
        label: React.PropTypes.string,
        labelFunction: React.PropTypes.func,
        isDisabled: React.PropTypes.bool,
        isDisabledFunction: React.PropTypes.func
    },
    getDefaultProps: function() {
        return {
            handleClick: function(e) {},
            labelFunction: function() {},
            isDisabled: false,
            propagateClick: false
        };
    },

    handleClick: function(e) {
        if (!this.isDisabled()) {
            this.props.handleClick(e);
        }
        if (!this.props.propagateClick) {
            e.preventDefault();
            e.stopPropagation();
        }
    },

    label: function(){
        return this.props.label || this.props.labelFunction() || '';
    },

    isDisabled: function() {
        if (this.props.isDisabled)
            return true;
        else if (this.props.isDisabledFunction !== undefined)
            return this.props.isDisabledFunction();
        else
            return false;
    },

    render: function() {
        // omit props reserved for internal use from being passed along.
        var props = _.omit(this.props, ['label', 'handleClick', 'isDisabled', 'style']);

        var buttonClass = "button_";
        var style = this.props.style ? this.props.style.toLowerCase() : "";
        if (["secondary","tertiary","solid","uppercase"].indexOf(style) != -1) {
            buttonClass += " button_-"+style
        }
        var cls = this.props.className ? this.props.className : buttonClass;

        if (this.isDisabled()) {
            props.disabled = "disabled";
            cls += " is-disabled";
        }
        return (<button className={cls} onClick={this.handleClick} {...props}>{this.label()}</button>);

    }
});


var SubmitButton = React.createClass({
    propTypes: {
        formId: React.PropTypes.string.isRequired,
        formType: React.PropTypes.string,
    },
    getDefaultProps: function() {
        return {
            style: 'primary',
            label: 'Submit',
        }
    },

    handleFormSubmit: function() {
        formType = this.props.formType || this.props.formId;

        var formData = FormStore.getFormData(this.props.formId);
        if (formData.formState.actionState !== "waiting") {
            FormActions.submitForm(this.props.formId, formType);
        }
    },

    render: function() {
        return (<Button style={this.props.style} type="submit" key="submit" handleClick={this.handleFormSubmit} label={this.props.label} />)
    }
});


module.exports = {
    Button: Button,
    SubmitButton: SubmitButton,
};
