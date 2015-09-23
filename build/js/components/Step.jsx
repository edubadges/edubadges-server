var React = require('react');

var Step = React.createClass({
    propTypes: {
        title: React.PropTypes.string.isRequired,
        earned: React.PropTypes.bool,
    },
    getDefaultProps: function() {
        return {
            earned: false,
            title: "Title",
        };
    },

    render: function() {
        return (<button className={"card_ step_ "+(this.props.earned ? 'step_-earned' : '')}>{this.props.title}</button>);
    }
});

module.exports = {
    Step: Step
};
