var React = require('react');
var _ = require('lodash');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api').APISubmitData;

//Stores
var APIStore = require('../stores/APIStore');

// Components
var Button = require('../components/Button.jsx').Button;
var Card = require('../components/Card.jsx');
var Property = require('../components/BadgeDisplay.jsx').Property;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');
var OpenBadgeList = require('../components/OpenBadgeList.jsx');
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
        <div className="form_-x-field">
            <label htmlFor="embed">Description</label>
            <textarea name="embed" id="embed" rows="4" tabindex="5" defaultValue={this.generateEmbed(this.props.share_url)} onClick={this.selectAllText} />
        </div>
    );
  }
});

var CollectionShareInfo = React.createClass({
    propTypes: {
        slug: React.PropTypes.string.isRequired,
        initialShareUrl: React.PropTypes.string,
    },

    getInitialState: function() {
        return {
            shared: Boolean(this.props.initialShareUrl),
            shareUrl: this.props.initialShareUrl,
        };
    },

  componentDidMount: function(){
    APIStore.addListener('DATA_UPDATED_shareCollection_' + this.props.collectionSlug, this.handleShareUpdate)
  },
  componentWillUnmount: function(){
    APIStore.removeListener('DATA_UPDATED_shareCollection_' + this.props.collectionSlug, this.handleShareUpdate);
  },
  handleShareUpdate: function(){
    var collection = APIStore.getFirstItemByPropertyValue('earner_collections', 'slug', this.props.collectionSlug);
    this.setState({ shared: ! this.state.shared, shareUrl: collection.share_url });
  },

  selectAllText: function(e){
    e.target.setSelectionRange(0, this.state.shareUrl.length);
  },
  render: function() {
    var embedField, shareLink;

    if (this.state.shared) {
        var embedField = (
            <div className="form_-x-field">
                <IFrameEmbedInfo share_url={this.state.shareUrl} />
            </div>);
        var shareLinkField = (
            <div className="form_-x-field">
                <label htmlFor="shareurl">Link</label>
                <div className="form_-x-action">
                    <input type="text" readOnly={true} name="shareurl" onClick={this.selectAllText} value={this.state.shareUrl} />
                    <button type="button" tabindex="3"><span className="icon_ icon_-copy">Copy</span></button>
                </div>
            </div>);
    }

    var sharePage = this.state.shared ? (<a href={this.state.shareUrl}>View Share Page</a>) : '';

    return (
      <form className="form_">
        <div className="form_-x-field">
          <input type="checkbox" name="toggle-share" checked={this.state.shared ? true : false} className={"share-collection-checkbox"} onChange={this.handleChange} />
          <label htmlFor="toggle-share">Generate sharing link {this.state.shared ? (<span className="hint">(Unchecking this box will disable sharing)</span>) : ''}</label>
        </div>
        { shareLinkField }
        { embedField }
      </form>
    );
  },
  handleChange: function(e){
    var apiContext;
    if ( ! this.state.shared) {
      // Turn sharing on
      apiContext = {
        formId: "shareCollection_" + this.props.collectionSlug,
        apiCollectionKey: "earner_collections",
        apiSearchKey: 'slug',
        apiSearchValue: this.props.collectionSlug,
        apiUpdateFieldWithResponse: 'share_url',

        actionUrl: "/v1/earner/collections/" + this.props.collectionSlug + "/share",
        method: "GET",
        successHttpStatus: [200],
        successMessage: "Collection updated"
      };

      APISubmitData(null, apiContext);
    }
    else {
      // Delete share hash
      apiContext = {
        formId: "shareCollection_" + this.props.collectionSlug,
        apiCollectionKey: "earner_collections",
        apiSearchKey: 'slug',
        apiSearchValue: this.props.collectionSlug,
        //apiUpdateValuesTo: {share_url: undefined, share_hash: undefined},  // Delete the values of these fields
        apiUpdateValuesFromResponse: ['share_url', 'share_hash'],  // The response would do the same as above as it doesn't have the fields in the response

        actionUrl: "/v1/earner/collections/" + this.props.collectionSlug + "/share",
        method: "DELETE",
        doNotDeleteCollection: true,  // Very important
        successHttpStatus: [204],
        successMessage: "Collection updated"
      };
        APISubmitData(null, apiContext);
    }
  },
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
      apiUpdateFieldWithResponse: 'badges',
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
    getDefaultProps: function() {
        return {
            badgesToShow: 6,
        };
    },
    handleClick: function(){
        navigateLocalPath(
            this.props.targetUrl || '/earner/collections/' + this.props.slug
        );
    },
    render: function() {
        var cardActionItems = [];

        if (this.props.share_url) {
            cardActionItems.push({
                actionUrl: this.props.share_url,
                iconClass: 'fa-external-link',
                actionClass: 'pull-right',
                title: "Share"
            });
        }

        var badges = APIStore.filter('earner_badges', 'id', 
            _.pluck(this.props.badgeList, 'id').slice(0,this.props.badgesToShow)
        );

        return (
            <div className="card_">
                <div className="collection_ viewdetails_">
                    <h1 className="truncate_" actions={cardActionItems}>{this.props.name}</h1>
                    <OpenBadgeList
                        display="image only"
                        badges={badges}
                        grid={false}
                        showEmptyBadge={this.props.showEmptyBadge}
                        clickEmptyBadge={this.props.clickEmptyBadge}
                        selectedBadgeIds={this.props.selectedBadgeIds}
                        handleClick={this.props.handleClick}
                        />
                    <div className="viewdetails_-x-details">
                        <button className="button_ button_-solid button_-uppercase" onClick={this.handleClick}>View Details</button>
                    </div>
                </div>
                <div className="title_">
                    <div className="title_-x-section">
                    <h1 className="truncate_">{this.props.badgeList.length} Badge{(this.props.badgeList.length === 0 || this.props.badgeList.length > 1) ? 's' : ''}</h1>
                </div>
                </div>
            </div>
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
        <div>
            <EarnerCollectionCard
                key={'collection-' + i}
                name={item.name}
                slug={item.slug}
                description={item.description}
                share_url={item.share_url}
                badgeList={item.badges || []}
                clickable={this.props.clickable}
                />
        </div>
      );
    }.bind(this));
    return (
      <div className="l-grid">
        {collections}
      </div>
    );
  }
});


module.exports = {
  EarnerCollectionList: EarnerCollectionList,
  EarnerCollectionCard: EarnerCollectionCard,
  EarnerCollectionDetail: EarnerCollectionDetail,
  CollectionShareInfo: CollectionShareInfo,
};
