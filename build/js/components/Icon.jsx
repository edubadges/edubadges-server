var React = require('react');

var Icon = React.createClass({
    proptypes: {
        iconName: React.PropTypes.string.isRequired,

        position: React.PropTypes.string,
        showText: React.PropTypes.bool,
        size: React.PropTypes.string,
    },

    getDefaultProps: function() {
        return {
            position: "left",
            size: "large",
            showText: true,
        };
    },

    render: function() {
        var position = (this.props.position == "right") ? "icon_-right" : "";
        var size = (this.props.size == "small") ? "icon_-small" : "";
        var showText = ( ! this.props.showText) ? "icon_-notext" : "";

        return (
            <span className={"icon_ "+ this.props.iconName +" "+ position +" "+ size +" "+ showText}>{this.props.children}</span>);
    }

});

module.exports = {
    Icon: Icon
};
