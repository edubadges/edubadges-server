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
            'backgroundColor': '#f0f',
            'shape': 'circle',
            'graphic': initialData.STATIC_URL+'badgestudio/graphics/Flower.png'
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
        this.setState({
            'backgroundColor': color
        })
    },

    render: function() {
        return (<div>
            <p>
            badge studio...
            </p>
            <StudioCanvas 
                width={500} 
                height={500} 
                backgroundColor={this.state.backgroundColor}
                shape={this.state.shape}
                graphic={this.state.graphic}
                />
            <p>
            Color:<input type="text" onChange={this.handleColorChange} value={this.state.backgroundColor} />
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