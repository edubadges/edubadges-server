var React = require('react');


var Heading = React.createClass({
    getDefaultProps: function() {
        return {
            'title': "Title",
            'subtitle': undefined,
            'size': undefined,
            'rule': undefined,
        };
    },

    render: function() {
        var headerClassList = ["heading_"];
        var rule;

        var subtitle = this.props.subtitle ? (<p>{this.props.subtitle}</p>) : "";

        if (this.props.size) {
            headerClassList.push("heading_-"+ this.props.size);
        }

        var actions;
        if (React.Children.count(this.props.children) > 0) {
            actions = (
                <div className="heading_-x-actions">
                    {this.props.children}
                </div>
            )
        }

        if (this.props.rule) {
            rule = (<hr className="rule_" />)
        }

        return (
            <div className="x-owner">
                <header className={headerClassList.join(" ")}>
                    <div className="heading_-x-text">
                        <h1>{this.props.title}</h1>
                        {subtitle}
                    </div>
                    {actions}
                </header>
                {rule}
            </div>)
    }
});

module.exports = {
    Heading: Heading,
};
