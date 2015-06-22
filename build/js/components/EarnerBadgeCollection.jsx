var React = require('react');
var _ = require('underscore');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api').APISubmitData;

//Stores
var APIStore = require('../stores/APIStore');

// Components
var ActionBar = require('../components/ActionBar.jsx').ActionBar;
var Card = require('../components/Card.jsx');
var Property = require('../components/BadgeDisplay.jsx').Property;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');
var LoadingComponent = require('../components/LoadingComponent.jsx');

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
  getInitialState: function() {
    return {
      formState: "inactive",
      selectedBadgeIds: [],
      message: ''
    };
  },
  componentDidMount: function(){
    APIStore.addListener('DATA_UPDATED_earnerCollection_' + this.props.slug, this.handleUpdate)
  },
  componentWillUnmount: function(){
    APIStore.removeListener('DATA_UPDATED_earnerCollection_' + this.props.slug, this.handleUpdate);
  },
  startEditing: function(){
    this.setState({
      formState: "editing",
      selectedBadgeIds: _.pluck(this.props.badgeList, 'id'),
      message: ''
    });
  },
  save: function(){
    console.log("SAVING....");
    this.setState({formState: "waiting"});

    var apiContext = {
      formId: "earnerCollection_" + this.props.slug,
      apiCollectionKey: "earner_collections",
      apiItemKey: this.props.slug,
      actionUrl: "/v1/earner/collections/" + this.props.slug + "/badges",
      method: "PUT",
      successHttpStatus: [200],
      successMessage: "Collection updated"
    };
    var data = this.state.selectedBadgeIds.map(function(el, index){
      return {"id": el};
    }.bind(this));
    console.log(data);
    APISubmitData(data, apiContext);

  },
  selectBadgeId: function(id){
    if (this.state.selectedBadgeIds.indexOf(id) > -1)
      this.setState({selectedBadgeIds: _.without(this.state.selectedBadgeIds, id)});
    else
      this.setState({selectedBadgeIds: this.state.selectedBadgeIds.concat([id])})
  },
  handleUpdate: function(){
    if (this.isMounted()){
      this.setState({
        message: {type: 'success', content: 'Collection updated.'},
        formState: 'inactive',
        selectedBadgeIds: []
      });
    }
  },
  render: function() {
    var badges, editBadgeButtonConfig, panelFunction;


    if (this.state.formState == 'inactive'){
      badges = APIStore.filter('earner_badges', 'id', _.pluck(this.props.badgeList, 'id'));

      editBadgeButtonConfig = { 
        title: "Select Badges",
        buttonType: "primary",
        icon: "fa-certificate", 
        activePanelCommand: {} 
      };
      panelFunction = this.startEditing;
    }

    else if (this.state.formState == 'editing' || this.state.formState == 'waiting') {
      badges = APIStore.getCollection('earner_badges');

      editBadgeButtonConfig = { 
        title: "Save",
        buttonType: "primary",
        icon: "fa-floppy-o", 
        activePanelCommand: {} 
      };
      panelFunction = this.save;
    }

    else {
      // needs testing: when waiting on API response, set the included badges to the selected set.
      badges = APIStore.filter('earner_badges', 'id', this.state.selectedBadgeIds);
    }


    return (
      <div className="earner-collection-detail">
        <p className="earner-collection-description row">
          <span className="text-label col-xs-12 col-sm-4">Description</span>
          <span className="text-content col-xs-12 col-sm-8">{this.props.description}</span>
        </p>
        <ActionBar 
          title="Badges in collection"
          viewId={'earnerCollectionDetail' + this.props.slug}
          items={[editBadgeButtonConfig]}
          updateActivePanel={panelFunction}
        />
        {this.state.formState == "waiting" ? <LoadingComponent /> : ""}
        {this.state.message ? (<div className={"alert alert-" + this.state.message.type}>{this.state.message.content}</div>) : ""}
        <EarnerBadgeList
          display="thumbnail"
          badges={badges}
          moreLink={this.props.targetUrl || '/earner/collections/' + this.props.slug}
          handleClick={this.state.formState == 'editing' ? this.selectBadgeId : null}
          selectedBadgeIds={this.state.selectedBadgeIds}
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
