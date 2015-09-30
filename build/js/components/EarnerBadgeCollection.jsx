var React = require('react');
var _ = require('lodash');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api').APISubmitData;

//Stores
var APIStore = require('../stores/APIStore');

// Components
var ActionBar = require('../components/ActionBar.jsx').ActionBar;
var Button = require('../components/Button.jsx').Button;
var Card = require('../components/Card.jsx');
var Property = require('../components/BadgeDisplay.jsx').Property;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');
var LoadingComponent = require('../components/LoadingComponent.jsx');
var Heading = require('../components/Heading.jsx').Heading;

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

var IFrameEmbedInfo = React.createClass({
  generateEmbed: function(url){
    return '<iframe height="500" width="300" frameborder="0" src="' + url + '/embed' + '"></iframe>';
  },
  selectAllText: function(e){
    e.target.setSelectionRange(0, this.generateEmbed(this.props.share_url).length);
  },
  render: function() {
    return (
      <div className="collection-embed-info">
        <textarea defaultValue={this.generateEmbed(this.props.share_url)} onClick={this.selectAllText} /> 
      </div>
    );
  }
});

var CollectionShareInfo = React.createClass({
  getDefaultProps: function() {
    return {
      share_url: ''
    };
  },
  selectAllText: function(e){
    e.target.setSelectionRange(0, this.props.share_url.length);
  },
  render: function() {
    var embedInfo = this.props.share_url ? (<IFrameEmbedInfo share_url={this.props.share_url} />) : '';

    return (
      <div className={this.props.share_url ? "card_ collection-share-info sharing-enabled" : "card_ collection-share-info sharing-disabled disabled"} style={{padding: '1em'}}>
        <div className="sharing-input">
          <input type="checkbox" name="sharecheck" checked={this.props.share_url ? true : false} className={"share-collection-checkbox"} onChange={this.props.handleChange} />
          <label htmlFor="sharecheck">
            Generate sharing link
            {this.props.share_url ? (<span className="hint">(Unchecking this box will disable sharing)</span>) : ''}
          </label>
        </div>
        <div className="sharing-url-box">
          <label htmlFor="shareurl">Link:</label>
          <input type="text" readOnly={true} name="shareurl" onClick={this.selectAllText} value={this.props.share_url} />
          {embedInfo}
        </div>
        {this.props.share_url ? (<p className="hint">When enabled, anyone with the link will be able to view this collection.</p>) : ''}
        {this.props.share_url ? (<p><a href={this.props.share_url}><button className='btn btn-primary'>View Share Page</button></a></p>) : ''}
      </div>
    );
  }
});


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
    this.setState({formState: "waiting"});

    var apiContext = {
      formId: "earnerCollection_" + this.props.slug,
      apiCollectionKey: "earner_collections",
      apiSearchKey: 'slug',
      apiSearchValue: this.props.slug,
      apiUpdateKey: 'badges',
      actionUrl: "/v1/earner/collections/" + this.props.slug + "/badges",
      method: "PUT",
      successHttpStatus: [200],
      successMessage: "Collection updated"
    };
    var data = this.state.selectedBadgeIds.map(function(el, index){
      return {"id": el};
    }.bind(this));
    APISubmitData(data, apiContext);

  },
  selectBadgeId: function(id){
    if (this.state.selectedBadgeIds.indexOf(id) > -1)
      this.setState({selectedBadgeIds: _.without(this.state.selectedBadgeIds, id)});
    else
      this.setState({selectedBadgeIds: this.state.selectedBadgeIds.concat([id])})
  },
  handleShareChange: function(e){
    var apiContext;
    if (!this.props.share_url) {
      // Turn sharing on
      apiContext = {
        formId: "earnerCollection_" + this.props.slug,
        apiCollectionKey: "earner_collections",
        apiSearchKey: 'slug',
        apiSearchValue: this.props.slug,
        apiUpdateKey: 'share_url',
        actionUrl: "/v1/earner/collections/" + this.props.slug + "/share",
        method: "GET",
        successHttpStatus: [200],
        successMessage: "Collection updated"
      };
    }
    else {
      // Delete share hash
      apiContext = {
        formId: "earnerCollection_" + this.props.slug,
        apiCollectionKey: "earner_collections",
        apiSearchKey: 'slug',
        apiSearchValue: this.props.slug,
        apiUpdateKey: 'share_url',
        actionUrl: "/v1/earner/collections/" + this.props.slug + "/share",
        method: "DELETE",
        successHttpStatus: [204],
        successMessage: "Collection updated"
      };
    }

    APISubmitData(null, apiContext);
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
      <div>
        <CollectionShareInfo
          share_url={this.props.share_url}
          handleChange={this.handleShareChange}
        />

        {this.state.message ? (<div className={"alert alert-" + this.state.message.type}>{this.state.message.content}</div>) : ""}
        {this.state.formState == "waiting" ? <LoadingComponent /> : ""}

        <Heading
          size="medium"
          title={"Badges in Collection"}
          subtitle={this.state.formState == 'editing' ? "Manage and save which badges appear in this collection." : "Badges with a gray highlighed background will remain in the collection when you click save."}
          rule={false}>
            <Button label={this.state.formState == 'editing' ? "Save": "Select Badges"} propagateClick={true}
              handleClick={panelFunction}
            />
        </Heading>
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
    var cardActionItems = [];
    if (this.props.share_url)
      cardActionItems.push({
        actionUrl: this.props.share_url,
        iconClass: 'fa-external-link',
        actionClass: 'pull-right',
        title: "Share"
      });

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
