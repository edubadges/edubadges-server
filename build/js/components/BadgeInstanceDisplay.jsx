var React = require('react');
var moment = require('moment');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api.js').APISubmitData;

// Components
var Button = require('../components/Button.jsx').Button;
var Heading = require('../components/Heading.jsx').Heading;
var Property = require('../components/BadgeDisplay.jsx').Property;
var LoadingIcon = require('../components/Widgets.jsx').LoadingIcon;

BadgeInstanceShort = React.createClass({
  render: function() {
    var displayIssueDate = moment(this.props.issuedOn).format('MMMM Do YYYY, h:mm:ss a');

    return (
      <div className="badgeinstance-display badgeinstance-display-short row">
        <div className="email col-xs-6 col-sm-4">{this.props.email}</div>
        <div className="issuedOn col-xs-6 col-sm-8">{displayIssueDate}</div>
      </div>
    );
  }
});


BadgeInstanceDetail = React.createClass({
  render: function() {
    var properties = {
      // image: {type: 'image', text: this.props.name + ' logo', href: this.props.image},
      // name: {type: 'text', text: this.props.name},
      // criteria: {type: 'link', href: this.props.json.criteria},
      // description: {type: 'text', text: this.props.json.description}
    }

    return (
      <div className="badge-display badgeclass-display badgeclass-display-detail col-xs-12">
      </div>
    );
  }
});


BadgeInstanceList = React.createClass({
  getDefaultProps: function() {
    return {
      display: 'list',
      perPage: 50,
      currentPage: 1,
      badgeInstances: [],
      dataRequestStatus: null
    };
  },
  getInitialState: function(){
      return {};
  },
  initRevokeInstance: function(badgeInstance, ev) {
      // TODO: Factor state into store
      this.setState({revoking: badgeInstance.slug});
  },
  cancelRevokeInstance: function(ev){
      this.setState({revoking: null});
  },
  revokeBadgeInstance: function(badgeInstance, ev) {
      badgeClassUrl = badgeInstance.badge_class;
      badgeClassSlug = badgeClassUrl.substr(badgeClassUrl.lastIndexOf('/')+1);

      issuerUrl = badgeInstance.issuer;
      issuerSlug = issuerUrl.substr(issuerUrl.lastIndexOf('/')+1);

      apiContext = {
          apiCollectionKey: "issuer_badgeinstances",
          apiSearchKey: 'slug',
          apiSearchValue: badgeInstance.slug,

          actionUrl: "/v1/issuer/issuers/"+ issuerSlug +"/badges/"+ badgeClassSlug +"/assertions/"+ badgeInstance.slug,
          method: "DELETE",
          successHttpStatus: [200],
          successMessage: "Badge instance revoked."
      };
      APISubmitData({revocation_reason: 'Manually revoked by issuer.'}, apiContext);
      this.setState({revoking: null});
  },

  render: function() {
    var badgeInstances = this.props.badgeInstances.map(function(badgeInstance, i) {

        var issuedOn = moment(badgeInstance.json.issuedOn).format('MMMM D, YYYY');
        var evidenceButton;
        if (badgeInstance.json.evidence) {
          var clickEvidence = function() {
            window.open(badgeInstance.json.evidence, '_blank');
          };
          evidenceButton = (<Button style="tertiary" label="Evidence" handleClick={clickEvidence}/>)
        }

        var leftCellGroup = (<div></div>), rightCellGroup = (<div></div>);
        if (this.state.revoking && this.state.revoking == badgeInstance.slug){
            rightCellGroup = (
                <div className="l-horizontal l-horizontalright">
                    <p style={{textAlign: "right"}}>Are you sure?</p>
                    <Button className="button_ button_-tertiary" label="Cancel"
                            onClick={this.cancelRevokeInstance} />
                    <Button className="button_" label="Confirm Revoke"
                            onClick={this.revokeBadgeInstance.bind(this, badgeInstance)} />
                </div>
            );
        }
        else {
            leftCellGroup = (
                <div>
                    <Button
                        className="button_ button_-tertiary" label="Revoke"
                        onClick={this.initRevokeInstance.bind(this, badgeInstance)}
                    />
                    {evidenceButton}
                </div>
            );
        }

        return (
            <tr key={badgeInstance.slug}>
                <th scope="row">{badgeInstance.recipient_identifier} </th>
                <td>{issuedOn}</td>
                <td>
                    <div>
                        {leftCellGroup}
                        {rightCellGroup}
                    </div>
                </td>
            </tr>
        );
    }.bind(this));

    var loadingIcon = this.props.dataRequestStatus == "waiting" ? (<LoadingIcon />) : '';

    return (
      <div className="x-owner">
        <table className="table_">
            <thead>
                <tr>
                    <th scope="col">Recipient</th>
                    <th scope="col">Issue Date</th>
                    <th scope="col">Actions</th>
                </tr>
            </thead>
            <tbody>
                {badgeInstances}
            </tbody>
        </table>
        {loadingIcon}
      </div>
    );
  }

});


module.exports = {
  BadgeInstanceList: BadgeInstanceList,
  BadgeInstanceDetail: BadgeInstanceDetail
};
