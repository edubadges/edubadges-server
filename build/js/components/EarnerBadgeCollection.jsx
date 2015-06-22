var React = require('react');
var _ = require('underscore');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

//Stores
var APIStore = require('../stores/APIStore');

// Components
var Card = require('../components/Card.jsx');
var Property = require('../components/BadgeDisplay.jsx').Property;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');


var moreLinkBadgeJSON = function(moreCount){
  return {
    "type": "more-link",
    "id": -1,
    "errors": [],
    "clickable": false,
    "recipient_id": '',
    "json": {
      "id": ":_0",
      "type": "Assertion",
      "badge": {
        "id": ":_1",
        "type": "BadgeClass",
        "name": {
          "type": "xsd:string",
          "@value": moreCount + " more"
        },
        "description": {
          "type": "xsd:string",
          "@value": ""
        },
        "issuer": {
          "name": ""
        }
      },
      "image": {
        "type": "image",
        "id": "https://placeholdit.imgix.net/~text?txtsize=19&txt=%20your%20&w=200&h=200"
      }
    }
  };
};


var EarnerCollectionDetail = React.createClass({
  render: function() {
    var cardActionItems = [{
      actionUrl: this.props.share_url,
      iconClass: 'fa-external-link',
      actionClass: 'pull-right',
      title: "Share"
    }]
    var badges = APIStore.filter('earner_badges', 'id', _.pluck(this.props.badgeList, 'id'));

    return (
      <div className="earner-collection-detail">
        <p className="earner-collection-description row">
          <span className="text-label col-xs-12 col-sm-4">Description</span>
          <span className="text-content col-xs-12 col-sm-8">{this.props.description}</span>
        </p>
        <EarnerBadgeList
          display="thumbnail"
          badges={badges}
          moreLink={this.props.targetUrl || '/earner/collections/' + this.props.slug}
        />
      </div>
    );
  }
});


var EarnerCollectionCard = React.createClass({
  handleClick: function(){
    if (this.props.clickable)
      navigateLocalPath(
        this.props.targetUrl || '/earner/collections/' + this.props.slug
      );
  },
  render: function() {
    var cardActionItems = [{
      actionUrl: this.props.share_url,
      iconClass: 'fa-external-link',
      actionClass: 'pull-right',
      title: "Share"
    }];
    var badges = APIStore.filter('earner_badges', 'id', _.pluck(this.props.badgeList, 'id').slice(0,7));

    if (this.props.badgeList.length > 7){
      badges.push(moreLinkBadgeJSON(this.props.badgeList.length - 7));
    }
    return (
      <Card
        title={this.props.name}
        onClick={this.handleClick}
        actions={cardActionItems}
      >
        <EarnerBadgeList
          display="image only"
          badges={badges}
          moreLink={this.props.targetUrl || '/earner/collections/' + this.props.slug}
        />
      </Card>
    );
  }
});

/* 
  EarnerCollectionList: 
*/
var EarnerCollectionList = React.createClass({
  getDefaultProps: function() {
    return {
      clickable: true
    };
  },
  render: function() {
    var collections = this.props.collections.map(function(item, i){
      return (
        <EarnerCollectionCard
          key={'collection-' + i}
          name={item.name}
          slug={item.slug}
          description={item.description}
          share_url={item.share_url}
          badgeList={item.badges || []}
          clickable={this.props.clickable}
        />
      );
    }.bind(this));
    return (
      <div className="earner-collection-list">
        {collections}
      </div>
    );
  }
});


module.exports = {
  EarnerCollectionList: EarnerCollectionList,
  EarnerCollectionCard: EarnerCollectionCard,
  EarnerCollectionDetail: EarnerCollectionDetail
};
