var React = require('react');
var Button = require('../components/Button.jsx').Button;


var BadgeStudio = React.createClass({
    proptypes: {
        handleBadgeComplete: React.PropTypes.func,
    },
    getDefaultProps: function() {
        return {
            handleBadgeComplete: undefined
        }
    },
    getInitialState: function() {
        return {

        }
    },

    componentDidMount: function() {

    },
    componentWillUnmount: function() {

    },

    handleBadgeComplete: function() {
        if (this.props.handleBadgeComplete)
            this.props.handleBadgeComplete();
    },

    render: function() {
        return (<div>
            badge studio...
            <Button label="done" handleClick={this.handleBadgeComplete}/>
        </div>);

    }

});

module.exports = {
    BadgeStudio: BadgeStudio
}