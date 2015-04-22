var React = require('react');
var moment = require('moment');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

// Components
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
  render: function() {
    var badgeInstances = this.props.badgeInstances.slice(
      this.props.perPage * (this.props.currentPage-1),
      this.props.perPage + this.props.perPage * (this.props.currentPage-1)
    ).map(function(instance, i){
      var properties = {
        email: instance.email,
        slug: instance.slug,
        issuedOn: instance.json.issuedOn,
        key: "instance-" + i
      }

      if (this.props.display == 'list'){
        return (
          <BadgeInstanceShort {...properties} />
        );
      }

    }.bind(this));
    return (
      <div className="badgeinstance-list container-fluid">
        {this.props.dataRequestStatus == "waiting" ? (<LoadingIcon />) : ''}
        {badgeInstances}
      </div>
    );
  }

});


module.exports = {
  BadgeInstanceList: BadgeInstanceList,
  BadgeInstanceDetail: BadgeInstanceDetail
};