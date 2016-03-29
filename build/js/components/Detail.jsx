var React = require('react');
var moment = require('moment');
var _ = require('lodash');

var FacebookButton = require("../components/ShareButtons.jsx").FacebookButton;
var LinkedInButton = require("../components/ShareButtons.jsx").LinkedInButton;
var Heading = require('../components/Heading.jsx').Heading;
var Step = require('../components/Step.jsx').Step;


function getImageFileNameFromUrl(url) {
    //this removes the anchor at the end, if there is one
    url = url.substring(0, (url.indexOf("#") == -1) ? url.length : url.indexOf("#"));
    //this removes the query after the file name, if there is one
    url = url.substring(0, (url.indexOf("?") == -1) ? url.length : url.indexOf("?"));
    //this removes everything before the last slash in the path
    url = url.substring(url.lastIndexOf("/") + 1, url.length);
    //return
    return url;
}


var Detail = React.createClass({
    proptypes: {
        issuer: React.PropTypes.object.isRequired,
        badge_class: React.PropTypes.object.isRequired,
        badge_instance: React.PropTypes.object,
        recipient: React.PropTypes.string,
        selfUpdaters: React.PropTypes.arrayOf(React.PropTypes.object),
        actionGenerator: React.PropTypes.func,
        showUnearnedStep: React.PropTypes.bool,
        showDownloadButton: React.PropTypes.bool
    },
    getDefaultProps: function() {
        return {
            badge_instance: undefined,
            recipient: undefined,
            actionGenerator: function(){},
            showUnearnedStep: false,
            showDownloadButton: false,
            imageSize: "144"
        };
    },
    getInitialState: function(){
        return {};
    },
    componentDidMount: function(){
        var updateFunction;

        if (this.props.selfUpdaters){
            _.forEach(this.props.selfUpdaters, function(updater){
                if (updater.handler)
                    updateFunction = updater.handler.bind(this);
                else
                    updateFunction = this.handleUpdate;

                updater.store.addListener(
                    updater.listenFor,
                    updateFunction
                );
            }, this);
        }
    },
    componentWillUnmount: function(){
        var updateFunction;

        if (this.props.selfUpdaters){
            _.forEach(this.props.selfUpdaters, function(updater){
                if (updater.handler)
                    updateFunction = updater.handler.bind(this);
                else
                    updateFunction = this.handleUpdate;
                
                updater.store.removeListener(
                    updater.listenFor,
                    updateFunction
                );
            }, this);
        }
    },
    handleUpdate: function(){
        this.forceUpdate();
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

            var badgeName = _.get(this.props, 'badge_class.name', "Unknown Badge");
            var stepName = this.props.objectiveName || badgeName;
            var addToBadgr;
            var badge_instance = _.find([this.props.badge_instance, this.state.badge_instance], function(bi){
                return (!!_.get(bi, 'json.issuedOn'));
            });
            var imageUrl = _.get(this.props, 'badge_class.image');
            if (badge_instance) {
                imageUrl = this.props.showDownloadButton ? _.get(badge_instance, 'json.id')+"/image" : _.get(this.props, 'badge_class.image');
                properties.unshift(
                    <li key="recipient">
                        <h2 className="detail_-x-meta">Recipient</h2>
                        <p>{this.props.recipient ? this.props.recipient : badge_instance.recipient_identifier || badge_instance.email}</p>
                    </li>
                );
                var dateString = moment(badge_instance.json.issuedOn).format('MMMM D, YYYY');
                properties.unshift(
                    <li key="issued">
                        <Step title={stepName} subtitle={"Earned "+dateString} earned={true}/>
                    </li>
                );
                addToBadgr = (<button className="button_ button_-tertiary" href={"/earner/badges/new?url=" + _.get(badge_instance, 'json.id')} target="_blank">
                                Add to Badgr
                              </button>);

                var actions = this.props.actions || this.props.actionGenerator() || [
                    (<LinkedInButton key="linkedin" url={_.get(badge_instance, 'json.id')} title="I earned a badge!" message={badgeName} className='button_ button_-tertiary'>
                        Share on LinkedIn
                    </LinkedInButton>),
                    (<FacebookButton key="facebook" url={_.get(badge_instance, 'json.id')} className='button_ button_-tertiary'>
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
            else if (this.props.showUnearnedStep) {
                properties.unshift(
                    <li key="unissued">
                        <Step title={stepName} subtitle="Not earned" earned={false}/>
                    </li>
                );
            }
            return (
                <div className="dialog_-x_content">
                    <Heading truncate={true} size="small" title={badgeName} subtitle={_.get(this.props, 'badge_class.json.description')}/>
                    <div className="detail_">
                        <div>
                            <img src={imageUrl} width={this.props.imageSize} height={this.props.imageSize} alt={badgeName}/>
                            {this.props.showDownloadButton ? <div style={{"text-align": "center"}}><a className="button_ button_-tertiary" target="_blank" href={imageUrl} download={getImageFileNameFromUrl(imageUrl)}>Download</a></div> : null}
                        </div>
                        <ul>{properties}</ul>
                    </div>
                </div>);

    }

});


module.exports = {
    Detail: Detail
};
