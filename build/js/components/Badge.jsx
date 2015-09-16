var React = require('react');

var Badge = React.createClass({
    proptypes: {
        image: React.PropTypes.string.isRequired,
        description: React.PropTypes.string,
        label: React.PropTypes.string,
        width: React.PropTypes.number,
        height: React.PropTypes.number,
    },

    getDefaultProps: function() {
        return {
            image: "",
            description: undefined,
            width: 128,
            height: 128,
            label: "View Details",
            handleClick: function() {},
        };
    },

    render: function() {
        return (
            <div className="badge_">
                <img src={this.props.image} width={this.props.width} height={this.props.height} alt={this.props.description}/>
                <div className="badge_-x-action">
                    <button className="button_ button_-solid button_-uppercase" onClick={this.props.handleClick}>{this.props.label}</button>
                </div>
            </div>);
    }

});

module.exports = {
    Badge: Badge
};
