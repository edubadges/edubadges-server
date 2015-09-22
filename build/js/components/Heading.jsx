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

        var actions;
        if (React.Children.count(this.props.children) > 0) {
            actions = (
                <div className="heading_-x-actions">
                    {this.props.children}
                </div>
            )
        }

        return (
            <header className={"heading_ "+size}>
                <div className="heading_-x-text">
                    <h1>{this.props.title}</h1>
                    {subtitle}
                </div>
                {actions}
            </header>);
    }
});

module.exports = {
    Heading: Heading,
};


