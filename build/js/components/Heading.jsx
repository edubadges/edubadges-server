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

        var title;
        if (this.props.meta) {
            title = (
                <h1>
                    <div style={{display: 'inline'}}>{this.props.title}</div> (<span>{this.props.meta}</span>)
                </h1>);
        }
        else {
            title = (<h1>{this.props.title}</h1>);
        }

        return (
            <div className="x-owner">
                <header className={headerClassList.join(" ")}>
                    <div className="heading_-x-text">
                        {title}
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
