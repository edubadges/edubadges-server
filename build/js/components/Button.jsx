var React = require('react');
var _ = require('lodash');

var Button = React.createClass({
    propTypes: {
        label: React.PropTypes.string.isRequired,
        isDisabled: React.PropTypes.bool,
    },
    getDefaultProps: function() {
        return {
            handleClick: function(e) { },
            isDisabled: false
        };
    },

    handleClick: function(e) {
        if (!this.props.isDisabled) {
            this.props.handleClick(e);
        }
        e.preventDefault();
        e.stopPropagation();
    },

    render: function() {
        var props = _.assign({}, this.props);
        // remove our internal properties, and pass the rest along as attributes
        delete props.label;
        delete props.handleClick;
        delete props.isDisabled;
        delete props.style;

        var buttonClass = "button_";
        var style = this.props.style ? this.props.style.toLowerCase() : "";
        if (["secondary","tertiary","solid","uppercase"].indexOf(style) != -1) {
            buttonClass += " button_-"+style
        }
        var cls = this.props.className ? this.props.className : buttonClass;

        if (this.props.isDisabled) {
            props.disabled = "disabled";
        }
        return (<button className={cls} onClick={this.handleClick} {...props}>{this.props.label}</button>);

    }
});

module.exports = {
    Button: Button
};
