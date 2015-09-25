var React = require('react');
var moment = require('moment');
var _ = require('lodash');

var FacebookButton = require("../components/ShareButtons.jsx").FacebookButton;
var LinkedInButton = require("../components/ShareButtons.jsx").LinkedInButton;
var Heading = require('../components/Heading.jsx').Heading;

var Detail = React.createClass({
    proptypes: {
        issuer: React.PropTypes.object.isRequired,
        badge_class: React.PropTypes.object.isRequired,
        badge_instance: React.PropTypes.object,
        recipient: React.PropTypes.string,
    },
    getDefaultProps: function() {
        return {
            badge_instance: undefined,
            recipient: undefined
        };
    },

    render: function() {
        var issuerName = (_.get(this.props, 'issuer.json.url')) ?
            (<a href={_.get(this.props, 'issuer.json.url')} target="_blank" title="Website of badge issuer">
                {_.get(this.props, 'issuer.name')}
            </a>) : _.get(this.props, 'issuer.name', "Unknown");
        var issuerEmail = (_.get(this.props, 'issuer.json.email'))  ?
            "("+_.get(this.props, 'issuer.json.email')+")" : "";

        var properties = [
            (<li key="criteria">
                    <h2 className="detail_-x-meta">Criteria</h2>
                    <p>
                        <a href={_.get(this.props, 'badge_class.json.criteria', _.get(this.props, 'badge_class.criteria'))}
                          target="_blank" title="Criteria to earn this badge"
                        >
                        {_.get(this.props, 'badge_class.json.criteria', _.get(this.props, 'badge_class.criteria'))}
                    </a></p>
             </li>),

            (<li key="issuer">
                    <h2 className="detail_-x-meta">Issuer</h2>
                    <p>{issuerName} {issuerEmail}</p>
             </li>)];

            var badgeName = _.get(this.props, 'badge_class.name', "Unknown");
            var addToBadgr;
            if (this.props.badge_instance) {
                properties.unshift(
                    <li key="recipient">
                        <h2 className="detail_-x-meta">Recipient</h2>
                        <p>{this.props.recipient ? this.props.recipient : _.get(this.props, 'badge_instance.recipient_identifier', _.get(this.props, 'badge_instance.email'))}</p>
                    </li>
                );
                properties.unshift(
                    <li key="issued">
                        <h2 className="detail_-x-meta">Issue Date</h2>
 
                        <p>{moment(this.props.badge_instance.json.issuedOn).format('MMMM Do YYYY, h:mm a')}</p>
                    </li>
                );
                addToBadgr = (<button className="button_ button_-tertiary" href={"/earner/badges/new?url=" + _.get(this.props.badge_instance, 'json.id')} target="_blank">
                                Add to Badgr
                              </button>);

                var actions = this.props.actions ? this.props.actions : [
                    (<LinkedInButton key="linkedin" url={_.get(this.props.badge_instance, 'json.id')} title="I earned a badge!" message={badgeName} className='button_ button_-tertiary'>
                        Share on LinkedIn
                    </LinkedInButton>),
                    (<FacebookButton key="facebook" url={_.get(this.props.badge_instance, 'json.id')} className='button_ button_-tertiary'>
                        Share on Facebook
                    </FacebookButton>),
                ];
                properties.push(
                    <li key="actions">
                        <div className="l-horizontal">
                            <div>
                                {actions}
                            </div>
                        </div>
                    </li>
                );
            }

            return (
                <div className="dialog_-x_content">
                    <Heading size="small" title={badgeName} subtitle={_.get(this.props, 'badge_class.json.description')}/>
                    <div className="detail_">
                        <div>
                            <img src={_.get(this.props, 'badge_class.image')} width="224" height="224" alt={badgeName}/>
                        </div>
                        <ul>{properties}</ul>
                    </div>
                </div>);

    }

});


module.exports = {
    Detail: Detail
};
