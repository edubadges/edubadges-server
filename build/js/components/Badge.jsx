var React = require('react');

var Badge = React.createClass({
    proptypes: {
        image: React.PropTypes.string.isRequired,
        description: React.PropTypes.string,
        label: React.PropTypes.string,
        width: React.PropTypes.number,
        height: React.PropTypes.number,
        noAction: React.PropTypes.bool,
    },

    getDefaultProps: function() {
        return {
            image: "",
            description: undefined,
            width: 128,
            height: 128,
            noAction: false,
            label: "View Details",
            handleClick: function() {},
        };
    },

    render: function() {
        var badgeClassList = ["badge_"], badgeAction;

        if ( ! this.props.noAction) {
            badgeClassList.push("viewdetails_");
            badgeAction = (
                <div className="viewdetails_-x-details">
                    <button className="button_ button_-solid button_-uppercase">{this.props.label}</button>
                </div>);
        }

        return (
            <div className={badgeClassList.join(" ")} onClick={this.props.handleClick}>
                <img src={this.props.image} width={this.props.width} height={this.props.height} alt={this.props.description}/>
                {badgeAction}
            </div>);
    }

});

module.exports = {
    Badge: Badge
};
