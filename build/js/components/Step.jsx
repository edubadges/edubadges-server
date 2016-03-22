var React = require('react');
var TextTruncate = require('../components/TextTruncate');

var Step = React.createClass({
    propTypes: {
        title: React.PropTypes.string.isRequired,
        subtitle: React.PropTypes.string,
        earned: React.PropTypes.bool,
        handleClick: React.PropTypes.func,
    },
    getDefaultProps: function() {
        return {
            earned: false,
            title: "Title",
            subtitle: undefined,
            handleClick: function() {},
        };
    },

    render: function() {
        var subtitle = this.props.subtitle ? (<p>{this.props.subtitle}</p>) : "";
        return (
            <button className={"card_ step_ "+(this.props.earned ? 'step_-earned' : '')} onClick={this.props.handleClick}>
                <TextTruncate element="span" line={this.props.subtitle ? 1 : 2} truncateText="…" text={this.props.title} showTitle={true} className=""/>
                {subtitle}
            </button>);
    }
});

module.exports = {
    Step: Step
};
