var React = require('react');

//Actions
var navigateLocalPath = require('../actions/clicks.js').navigateLocalPath;


var Heading = React.createClass({
    getDefaultProps: function() {
        return {
            'title': "Title",
            'subtitle': undefined,
            'size': undefined,
            'rule': undefined,
        };
    },

    handleBackButton: function(ev) {
        navigateLocalPath(this.props.backButton);
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

        var backButton;
        if (this.props.backButton) {
            backButton = (<button className="heading_-x-back icon_ icon_-back icon_-notext" onClick={this.handleBackButton}>Back</button>);
        }

        if (this.props.rule) {
            rule = (<hr className="rule_" />)
        }

        var meta;
        if (this.props.meta) {
            meta = (<strong>({this.props.meta})</strong>);
        }

        return (
            <div className="x-owner">
                <header className={headerClassList.join(" ")}>
                    <div className="heading_-x-text">
                        <h1 className={this.props.truncate ? "truncate_" : ""}>{this.props.title} {meta}</h1>
                        {subtitle}
                    </div>
                    {actions}
                    {backButton}
                </header>
                {rule}
            </div>)
    }
});

module.exports = {
    Heading: Heading,
};
