var React = require('react');

var Badge = require('../components/Badge.jsx').Badge;
var Title = require('../components/Title.jsx').Title;


var Issuer = React.createClass({
    propTypes: {
        name: React.PropTypes.string.isRequired,
        badgeClasses: React.PropTypes.array.isRequired,
        image: React.PropTypes.string,
        description: React.PropTypes.string,

        includeBadges: React.PropTypes.bool,

        handleClick: React.PropTypes.func,
        handleAddClick: React.PropTypes.func,
        handleLinkClick: React.PropTypes.func,
        handleBadgeClick: React.PropTypes.func,

    },
    getDefaultProps: function() {
        return {
            image: undefined,
            description: "",

            includeBadges: true,

            handleBadgeClick: function() {},
            handleClick: function() {},
            handleLinkClick: undefined,
            handleAddClick: undefined
        };
    },
    getInitialState: function() {
        return {
            badgesExpanded: false
        };
    },

    toggleBadges: function() {
        this.setState({
            badgesExpanded: !this.state.badgesExpanded
        });
    },

    render: function() {
        var linklink;
        var addlink;

        var badgelink;
        var badgecontainer;
        if (this.props.includeBadges && this.props.badgeClasses.length > 0) {
            badgelink = (
                <button className={"icon_ icon_-notext "+(this.state.badgesExpanded ? 'icon_-collapse' : 'icon_-expand')}
                        onClick={this.toggleBadges}>Show Badges</button>);

            var badges = this.props.badgeClasses.slice(0,4).map(function(badgeclass) {
                return (
                    <div key={"issuer-badge-"+badgeclass.slug} onClick={this.handleBadgeClick}>
                        <div className="card_">
                            <Badge image={badgeclass.image}
                                   description={badgeclass.description}
                                   noAction={true} />
                            <Title title={badgeclass.name} centered={true}/>
                        </div>
                    </div>);

            }, this);

            badgecontainer = (
                <div className="issuer_-x-badges">
                    <div className="l-grid">
                        {badges}
                    </div>
                </div>

            );
        }

        if (this.props.handleAddClick) {
            addlink = (
                <button className="icon_ icon_-notext icon_-add"
                        handleClick={this.props.handleAddClick}>Add Something</button>);
        }

        if (this.props.handleLinkClick) {
            linklink = (
                <button className="icon_ icon_-notext icon_-link"
                        handleClick={this.props.handleLinkClick}>Link Somewhere</button>);
        }

        var image = this.props.image ? (<img src={this.props.image} width="48" height="48" alt={this.props.description}/>) : "";

        return (
            <div className={"issuer_ "+(this.state.badgesExpanded ? 'is-expanded' : '')}>
                <header className="card_">
                    <div className="issuer_-x-image" onClick={this.props.handleClick}>
                        {image}
                    </div>
                    <div className="issuer_-x-title" onClick={this.props.handleClick}>
                        <h1>{this.props.name}</h1>

                        <p>{this.props.description}</p>
                    </div>
                    <div className="issuer_-x-controls">
                        {badgelink}
                        {linklink}
                        {addlink}
                    </div>
                </header>
                {badgecontainer}
            </div>);
    }
});

module.exports = {
    Issuer: Issuer
};
