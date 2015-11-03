var React = require('react');
var _ = require('lodash');

// Stores
var FormStore = require('../stores/FormStore');

// Actions
var FormActions = require('../actions/forms');

// Component
var TetherTarget = require('../components/Tether.jsx').TetherTarget;


var Button = React.createClass({
    propTypes: {
        label: React.PropTypes.string,
        labelFunction: React.PropTypes.func,
        isDisabled: React.PropTypes.bool,
        isDisabledFunction: React.PropTypes.func,
        className: React.PropTypes.string,
        popover: React.PropTypes.string,
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

    handleMouseEnter: function(ev) {
        var popover = this.refs.TetherTarget.tethered.domNode.querySelector('.popover_');
        popover.classList.add('is-active');
        this.refs.TetherTarget.tethered.tether.position();
        popover.classList.add('is-visible', 'is-tethered');
    },

    handleMouseLeave: function(e) {
        var popover = this.refs.TetherTarget.tethered.domNode.querySelector('.popover_');
        popover.classList.remove('is-active');
        popover.classList.remove('is-visible');
    },

    render: function() {
        // omit props reserved for internal use from being passed along.
        var props = _.omit(this.props, ['label', 'handleClick', 'isDisabled', 'style', 'popover']);

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
        var button = (<button className={cls} onClick={this.handleClick} {...props}>{this.label()}</button>);

        if (this.props.popover) {
            var popoverElement = (<p className="popover_">{this.props.popover}</p>);
            var tetherOptions = {
                attachment: 'bottom right',
                targetAttachment: 'top center',
                offset: '10px 0',
                targetOffset: '0 25px',
                constraints: [
                    {
                        to: 'window',
                        attachment: 'together',
                        pin: true
                    }
                ]
            }

            return (
                <TetherTarget ref="TetherTarget" tethered={popoverElement} tetherOptions={tetherOptions} onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                    {button}
                </TetherTarget>
            );
        }
        else {
            return button
        }

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
        var formType = this.props.formType || this.props.formId;

        var formData = FormStore.getFormData(this.props.formId);
        if (formData.formState && formData.formState.actionState !== "waiting") {
            FormActions.submitForm(this.props.formId, formType, formData.formState);
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
