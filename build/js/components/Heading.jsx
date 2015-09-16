var React = require('react')


var Heading = React.createClass({
    getDefaultProps: function() {
        return {
            'title': "Title",
            'subtitle': undefined,
            'size': undefined,
        }
    },

    render: function() {
        var subtitle = this.props.subtitle ? (<p>{this.props.subtitle}</p>) : "";
        var size = this.props.size ? this.props.size.toLowerCase() : "";

        if (size && (size in ["medium", "small"])) {
            size = "heading_-"+size;
        } else {
            size = "";
        }

        return (
            <header className="heading_ {size}">
                <h1>{this.props.title}</h1>
                {subtitle}
            </header>);
    }
});

module.exports = {
    Heading: Heading,
};


