
var React = require('react');
var FacebookButton = require("react-social").FacebookButton;
var Heading = require('../components/Heading.jsx').Heading;

var Detail = React.createClass({
    proptypes: {
        issuer: React.PropTypes.object.isRequired,
        badge_class: React.PropTypes.object.isRequired,
        badge_instance: React.PropTypes.object,
    },
    getDefaultProps: function() {
        return {
            badge_instance: undefined
        }
    },

    render: function() {
        var properties = [
            (<li key="criteria">
                    <h2 className="detail_-x-meta">Criteria</h2>
                    <p><a href={this.props.badge_class.criteria} target="_blank" title="Criteria to earn this badge">{this.props.badge_class.criteria}</a></p>
             </li>),

            (<li key="issuer">
                    <h2 className="detail_-x-meta">Issuer</h2>
                    <p>{this.props.issuer.name}</p>
             </li>)];

            if (this.props.issuer.url) {
                properties.push(
                    <li key="website">
                        <h2 className="detail_-x-meta">Issuer Website</h2>
                        <p><a href={this.props.issuer.url} target="_blank" title="Website of badge issuer">{this.props.issuer.url}</a></p>
                    </li>);
            }

            if (this.props.issuer.email) {
                properties.push(
                    <li key="contact">
                        <h2 className="detail_-x-meta">Issuer Contact</h2>
                        <p><a href={"mailto:"+this.props.issuer.email} target="_blank" title="Contact email for issuer">{this.props.issuer.email}</a></p>
                    </li>);
            }

            if (this.props.badge_instance) {
                properties.unshift(
                    <li key="recipient">
                        <h2 className="detail_-x-meta">Recipient</h2>
                        <p>{this.props.badge_instance.email}</p>
                    </li>
                );
                properties.unshift(
                    <li key="issued">
                        <h2 className="detail_-x-meta">Issue Date</h2>
                        <p>{this.props.badge_instance.json.issuedOn}</p>
                    </li>
                );
                properties.push(
                    <li key="actions">
                        <button className="button_ button_-tertiary" href={"/earner/badges/new?url=" + _.get(this.props.badge_instance, 'json.id')} target="_blank">
                            Add to Badgr
                        </button>
                        <FacebookButton url={_.get(this.props.badge_instance, 'json.id')} message="I earned a badge!" className='button_ button_-tertiary'>
                            Share on Facebook
                        </FacebookButton>
                    </li>
                );
            }

            return (
                <div className="dialog_-x_content">
                    <Heading size="small" title={this.props.badge_class.name} subtitle={this.props.badge_class.description}/>
                    <div className="detail_">
                        <div>
                            <img src={this.props.badge_class.image} width="224" height="224" alt={this.props.badge_class.name}/>
                        </div>
                        <ul>{properties}</ul>
                    </div>
                </div>);

    }

});


module.exports = {
    Detail: Detail
};
