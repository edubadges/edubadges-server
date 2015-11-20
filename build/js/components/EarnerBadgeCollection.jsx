var React = require('react');
var _ = require('lodash');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api').APISubmitData;

//Stores
var APIStore = require('../stores/APIStore');

// Components
var BadgeSelectionTable = require('../components/BadgeSelectionTable.jsx').BadgeSelectionTable;
var Button = require('../components/Button.jsx').Button;
var Card = require('../components/Card.jsx');
var Dialog = require ('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
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

var CollectionShareInfo = React.createClass({
    propTypes: {
        collectionSlug: React.PropTypes.string.isRequired,
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

  selectAllText: function(ev) {
    ev.target.select();
  },
  copyShareLink: function(ev) {
    var shareLink = document.getElementById('sharelink');
    shareLink.select();

    var successful = document.execCommand('copy');
    if ( ! successful) {
        alert('Could not copy text in this browser, please copy your link using the mouse.');
    }
  },

  render: function() {
    var shareLink, sharePage = '', embedCode = '';

    if (this.state.shared) {
        embedCode = '<iframe height="500" width="300" frameborder="0" src="' + this.state.shareUrl + '/embed' + '"></iframe>';
        sharePage = (<a href={this.state.shareUrl}>View Share Page</a>);
    }

    return (
      <form className="form_">
        <div className="form_-x-field" style={{'display': 'none'}}>
          <input id="toggle-share" type="checkbox" name="toggle-share" checked={this.state.shared ? true : false} className={"share-collection-checkbox"} onChange={this.handleChange} />
          <label htmlFor="toggle-share">Generate sharing link {this.state.shared ? (<span className="hint">(Unchecking this box will disable sharing)</span>) : ''}</label>
        </div>
        <div className="form_-x-field">
            <label htmlFor="sharelink">Link</label>
            <div className="form_-x-action">
                <input id="sharelink" type="text" readOnly={true} name="sharelink" onClick={this.selectAllText} value={this.state.shareUrl} />
                <button type="button" tabIndex="3"><span className="icon_ icon_-copy" onClick={this.copyShareLink}>Copy</span></button>
            </div>
        </div>
        <div className="form_-x-field">
            <label htmlFor="embed">Description</label>
            <textarea name="embed" id="embed" rows="4" tabIndex="5" value={embedCode} onClick={this.selectAllText} />
        </div>
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
        apiUpdateValuesTo: {share_url: undefined, share_hash: undefined},  // Delete the values of these fields
        //apiUpdateValuesFromResponse: ['share_url', 'share_hash'],  // The response would do the same as above as it doesn't have the fields in the response

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
    propTypes: {
        slug: React.PropTypes.string.isRequired,
        badgeList: React.PropTypes.array,
        targetUrl: React.PropTypes.string,
    },

    getInitialState: function() {
        return {
            selectedBadgeIds: _.pluck(this.props.badgeList, 'id'),
        };
    },

    componentDidMount: function(){
        APIStore.addListener('DATA_UPDATED_earnerCollection_' + this.props.slug, this.earnerCollectionStoreUpdated)
    },

    componentWillUnmount: function(){
        APIStore.removeListener('DATA_UPDATED_earnerCollection_' + this.props.slug, this.earnerCollectionStoreUpdated);
    },

    save: function(){
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

        var data = this.state.selectedBadgeIds.map(function(badgeId){
            return {id: badgeId};
        }.bind(this));

        this.setState({formState: 'waiting'});
        APISubmitData(data, apiContext);
    },

    earnerCollectionStoreUpdated: function() {
        this.setState({
            formState: undefined,
            message: {type: 'success', content: 'Collection updated.'},
        });
        this.refs.manage.closeDialog();
    },

    onRowClick: function(ev, rowIndex, rowData) {
        var newSelectedBadgeArray = this.state.selectedBadgeIds.slice();

        var toBeSelected = ! rowData.selected;
        if (toBeSelected) newSelectedBadgeArray.push(rowData.id);
        else newSelectedBadgeArray.splice(newSelectedBadgeArray.indexOf(rowData.id), 1);

        this.setState({selectedBadgeIds: newSelectedBadgeArray});
    },

    render: function() {
        var allBadges = APIStore.getCollection('earner_badges');
        var collectionBadges = APIStore.filter('earner_badges', 'id', _.pluck(this.props.badgeList, 'id'));

        var actions = (<Button type="button" label="Update collection" onClick={this.save} />);
        var dialog = (
            <Dialog ref="manage" actions={actions} dialogId="manage-collection-badges">
                <Heading
                    size="medium"
                    title="Add / Remove Badges" />
                <BadgeSelectionTable
                    badges={allBadges}
                    initialSelectedBadges={_.pluck(this.props.badgeList, 'id')}
                    onRowClick={this.onRowClick} />
            </Dialog>
        );

        return (
            <div>
                {this.state.message ? (<div className={"alert alert-" + this.state.message.type}>{this.state.message.content}</div>) : ""}
                <Heading
                    size="medium"
                    title="Badges in Collection"
                    subtitle="Manage and save which badges appear in this collection."
                    rule={false}>
                    <DialogOpener dialog={dialog} dialogId="manage-collection-badges" key="manage-collection-badges">
                        <Button label="Manage" propagateClick={true} />
                    </DialogOpener>
                </Heading>

                {this.state.formState == "waiting" ? <LoadingComponent /> : ""}

                <EarnerBadgeList
                    display="thumbnail"
                    badges={collectionBadges}
                    moreLink={this.props.targetUrl || '/earner/collections/' + this.props.slug}
                    handleClick={this.selectBadgeId} />
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
