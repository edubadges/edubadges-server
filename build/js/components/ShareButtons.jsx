var React = require('react');

var LinkedInButton = React.createClass({
    propTypes: {
        url: React.PropTypes.string.isRequired,
        image: React.PropTypes.string,
        title: React.PropTypes.string,
        message: React.PropTypes.string,
        element: React.PropTypes.string,
        onClick: React.PropTypes.func
    },

    getDefaultProps: function () {
        return {
            element: "button",
            onClick: function() {}
        };
    },

    click: function (e) {
        this.props.onClick(e);
        window.open(this.constructUrl(), "_blank", "width=550,height=448");
    },

    render: function () {
        return React.createElement(this.props.element, { 'onClick': this.click, 'className': this.props.className }, this.props.children);
    },

    constructUrl: function () {
        var url = "https://www.linkedin.com/shareArticle?mini=true&url=" + encodeURIComponent(this.props.url);
        if (this.props.title) {
            url += '&title='+ this.props.title;
        }
        if (this.props.message) {
            url += '&summary='+ this.props.message;
        }
        return url;
    }
});


var FacebookButton = React.createClass({
    propTypes: {
        url: React.PropTypes.string.isRequired,
        element: React.PropTypes.string,
        onClick: React.PropTypes.func
    },

    getDefaultProps: function () {
        return {
            element: "button",
            onClick: function() {}
        };
    },

    click: function (e) {
        this.props.onClick(e);
        window.open(this.constructUrl(), "_blank", "width=550,height=274");
    },

    render: function () {
        return React.createElement(this.props.element, { 'onClick': this.click, 'className': this.props.className }, this.props.children);
    },

    constructUrl: function () {
        return "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(this.props.url);
    }
});


module.exports = {
    "LinkedInButton": LinkedInButton,
    "FacebookButton": FacebookButton
};
