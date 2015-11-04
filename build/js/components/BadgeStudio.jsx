var React = require('react');
var Button = require('../components/Button.jsx').Button;
var StudioCanvas = require('../components/StudioCanvas.jsx').StudioCanvas;


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
            'backgroundColor': '#555555'
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

    handleColorChange: function(e) {
        var color = e.target.value;
        console.log("color change", color)
        this.setState({
            'backgroundColor': color
        })
    },

    render: function() {
        return (<div>
            <p>
            badge studio...
            </p>
            <StudioCanvas width={400} height={400} backgroundColor={this.state.backgroundColor}/>
            <p>
            Color:<input type="text" onChange={this.handleColorChange} />
            </p>
            <p>
            <Button label="done" handleClick={this.handleBadgeComplete}/>
            </p>
        </div>);

    }

});

module.exports = {
    BadgeStudio: BadgeStudio
}