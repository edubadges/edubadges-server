var React = require('react');

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
                {this.props.title}
                {subtitle}
            </button>);
    }
});

module.exports = {
    Step: Step
};
