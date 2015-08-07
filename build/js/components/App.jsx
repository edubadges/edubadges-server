var React = require('react');
var RouterMixin = require('react-mini-router').RouterMixin;
var navigate = require('react-mini-router').navigate;
var assign = require('object-assign');
var urllite = require('urllite/lib/core');
var _ = require('lodash');

// Stores
var RouteStore = require('../stores/RouteStore');
var MenuStore = require('../stores/MenuStore');
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');
var FormConfigStore = require('../stores/FormConfigStore');
var UserStore = require('../stores/UserStore');
var ActiveActionStore = require('../stores/ActiveActionStore');

// Components
var TopLinks = require('../components/TopLinks.jsx');
var SideBarNav = require('../components/SideBarNav.jsx');
var MainComponent = require ('../components/MainComponent.jsx');
var SecondaryMenu = require('../components/SecondaryMenu.jsx');
var BreadCrumbs = require('../components/BreadCrumbs.jsx');
var ActionBar = require('../components/ActionBar.jsx').ActionBar;
var HeadingBar = require('../components/ActionBar.jsx').HeadingBar;
var ActivePanel = require('../components/ActivePanel.jsx');
var OpenBadgeList = require('../components/OpenBadgeList.jsx');
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var EarnerBadgeForm = require('../components/Form.jsx').EarnerBadgeForm;
var IssuerNotificationForm = require('../components/Form.jsx').IssuerNotificationForm
var IssuerList = require('../components/IssuerDisplay.jsx').IssuerList;
var IssuerDisplay = require('../components/IssuerDisplay.jsx').IssuerDisplay;
var BadgeClassDetail = require('../components/BadgeClassDisplay.jsx').BadgeClassDetail;
var BadgeInstanceList = require('../components/BadgeInstanceDisplay.jsx').BadgeInstanceList
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');
var EarnerCollectionList = require('../components/EarnerBadgeCollection.jsx').EarnerCollectionList;
var EarnerCollectionDetail = require('../components/EarnerBadgeCollection.jsx').EarnerCollectionDetail;
var ConsumerBadgeList = require('../components/ConsumerBadgeList.jsx');

// Actions
var LifeCycleActions = require('../actions/lifecycle');
var FormActions = require('../actions/forms');
var ActiveActions = require('../actions/activeActions');
var APIActions = require('../actions/api');
var ClickActions = require('../actions/clicks');

var App = React.createClass({
  mixins: [RouterMixin],

  // Route configuration: 
  routes: {
    '/': 'earnerMain',
    '/earner': 'earnerMain',
    '/earner/badges': 'earnerBadges',
    '/earner/badges/new': 'earnerImportBadge',
    '/earner/badges/:badgeId': 'earnerBadgeDetail',
    '/earner/collections': 'earnerCollections',
    '/earner/collections/:collectionSlug': 'earnerCollectionDetail',
    '/issuer': 'issuerMain',
    '/issuer/issuers': 'issuerMain',
    '/issuer/issuers/:issuerSlug': 'issuerDetail',
    '/issuer/issuers/:issuerSlug/badges/:badgeClassSlug': 'badgeClassDetail',
    '/explorer': 'consumerMain'
  },
  dependencies: {
    'earnerMain': ['earner_badges', 'earner_collections'],
    'issuerMain': ['issuer_issuers', 'issuer_badgeclasses']
  },

  // Route handling:
  handleRouteChange: function() {
    newRoute = RouteStore.getCurrentRoute();
    if (newRoute.startsWith('/earner'))
      this.handleDependencies(this.dependencies['earnerMain']);
    else if (newRoute.startsWith('/issuer'))
      this.handleDependencies(this.dependencies['issuerMain']);
    else if (newRoute.startsWith('/explorer'))
      this.handleDependencies([])
    navigate(newRoute);
  },


  getDefaultProps: function() {
    return {
      path: urllite(window.location.href).pathname + urllite(window.location.href).search,
      appTitle: 'Badgr',
      actionBars: MenuStore.getAllItems('actionBars'),
      secondaryMenus: MenuStore.getAllItems('secondaryMenus')
    };
  },
  getInitialState: function() {
    return {
      earnerBadges: [],
      requestedCollections: [],
      activePanels: ActiveActionStore.getAllActiveActions(),
      roleMenu: MenuStore.getAllItems('roleMenu')
    };
  },
  componentWillMount: function() {
    LifeCycleActions.appWillMount();
  },
  componentDidMount: function() {
    MenuStore.addListener('INITIAL_DATA_LOADED', function(){ this.updateMenu('roleMenu');});
    MenuStore.addListener('UNCAUGHT_DOCUMENT_CLICK', this._hideMenu);
    RouteStore.addListener('ROUTE_CHANGED', this.handleRouteChange);
    APIStore.addListener('DATA_UPDATED', function(){
      if (this.isMounted())
        this.setState({});
    }.bind(this));
    ActiveActionStore.addListener('ACTIVE_ACTION_UPDATED', this.handleActivePanelUpdate);
  },

  // Menu visual display functions:

  setActiveTopMenu: function(key){
    if (this.isMounted())
      this.setState({activeTopMenu: key});
  },
  _hideMenu: function(){
    if (this.state.activeTopMenu != null)
      this.setState({activeTopMenu: null});
  },
  updateMenu: function(key){
    if (this.isMounted()){
      var newState = {}
      newState[key] = MenuStore.getAllItems(key);
      this.setState(newState);
    }
  },

  updateActivePanel: function(viewId, update){
    console.log("Updating active panel " + viewId);
    console.log(update);
    ActiveActions.updateActiveAction(
      viewId,
      //updates vary by type; example: { type: "OpenBadgeDisplay", content: { badgeId: id, detailLevel: 'detail' }}
      update
    );
  },
  clearActivePanel: function(viewId){
    ActiveActions.clearActiveAction(viewId);
  },
  handleActivePanelUpdate: function(){
    if (this.isMounted()){
      update = { activePanels: ActiveActionStore.getAllActiveActions() };
      this.setState(update);
    }
  },

  handleDependencies: function(collectionKeys){
    toFetch = collectionKeys.filter(function(key, index){
      if (!APIStore.collectionsExist([key]) && this.state.requestedCollections.indexOf(key) == -1)
        return true;
      return false;
    }, this);

    if (toFetch.length > 0){
      this.setState({requestedCollections: this.state.requestedCollections.concat(toFetch)}, function(){
        APIActions.APIFetchCollections(toFetch);
      });
      return true;
    }
    return false;
  },


  /***   ---   RENDERING   ---   ***/
  // Triggers route-based rendering
  render: function() {
    return this.renderCurrentRoute();
  },

  // Render the base structure for the app (top menu, sidebar, and main content area)
  render_base: function(mainComponent) {
    return (
      <div id="wrapper" className="wrapper">
        <header className="main-header">
          <div className="wrap">
            <nav className="navbar navbar-default navbar-static-top" role="navigation">

              <div className="navbar-header">
                <a className="navbar-brand" href="/issuer">
                  <span>{ this.props.appTitle }</span>
                </a>
                <div className="navbar-right">
                  <TopLinks items={MenuStore.getAllItems('roleMenu').items} setActive={function(key){}} active={null} showLabels={true} />
                  <TopLinks items={MenuStore.getAllItems('topMenu').items} setActive={this.setActiveTopMenu} active={this.state.activeTopMenu} showLabels={true} />
                </div>
              </div>  
            </nav>
          </div>
        </header>

        <section className="main-section content-container">
          <div className="wrap page-wrapper">
            <div className="container-fluid">
                { mainComponent }
            </div>
          </div>
        </section>

      </div>
    );
  },


  earnerMain: function() {
    ClickActions.navigateLocalPath('/earner/badges');
    return this.render_base("Loading My Badges...");
  },

  earnerBadges: function(params){
    var viewId = "earnerBadges",
        currentPage=parseInt(_.get(params, 'page')) || 1,
        nextPage = currentPage + 1;
    dependenciesMet = APIStore.collectionsExist(this.dependencies['earnerMain']);

    var mainComponent = (
      <MainComponent viewId={viewId} dependenciesLoaded={dependenciesMet} >
        <HeadingBar
          title="My Badges"
        />
        <ActivePanel
          viewId={viewId}
          {...{"type":"EarnerBadgeImportForm","content":{"badgeId":null}}}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        <EarnerBadgeList
          viewId={viewId}
          badges={APIStore.getCollection('earner_badges')}
          perPage={20}
          currentPage={currentPage}
          moreLink={"/earner/badges?page=" + nextPage}
        />
      </MainComponent>
    );

    return this.render_base(mainComponent);
  },

  earnerImportBadge: function(params){
    var viewId = 'earnerImportBadge';
    var dependenciesMet = APIStore.collectionsExist(this.dependencies['earnerMain']);
    var breadCrumbs = [
      { name: "Earner Home", url: '/earner'},
      { name: "My Badges", url: '/earner/badges' },
      { name: "Import New Badge", url: '/earner/badges/new' }
    ];
    var navigateToBadgeList = function(){
      ClickActions.navigateLocalPath('/earner/badges');
    };

    var importUrl = params['url'];
    var mainComponent = (
      <MainComponent viewId={viewId} dependenciesLoaded={dependenciesMet} >
        <BreadCrumbs items={breadCrumbs} />
        <ActivePanel 
          viewId={viewId}
          type="EarnerBadgeImportForm"
          url={importUrl || ''}
          submitImmediately={importUrl ? true : false}
          clearActivePanel={navigateToBadgeList}
        />

      </MainComponent>
    );
    return this.render_base(mainComponent);
  },

  earnerBadgeDetail: function(badgeId) {
    var viewId = 'earnerBadgeDetail';
    var badge = APIStore.getFirstItemByPropertyValue(
      'earner_badges', 'id', badgeId
    );

    if (!badge)
      return this.render_base("Badge not found!");

    var breadCrumbs = [
      { name: "Earner Home", url: '/earner'},
      { name: "My Badges", url: '/earner/badges' },
      { name: badge.json.badge.name['@value'], url: '/earner/badges/' + badgeId }
    ];
    var mainComponent = (
      <MainComponent viewId={viewId}>
        <BreadCrumbs items={breadCrumbs} />
        <ActionBar 
          title={badge.json.badge.name['@value']}
          viewId={viewId}
          items={this.props.actionBars[viewId] || []}
          updateActivePanel={this.updateActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <OpenBadge
          id={badge.id}
          display="full"
          json={badge.json}
          recipientId={badge.recipient_id}
          errors={badge.errors}
        />
      </MainComponent>
    );

    // render the view
    return this.render_base(mainComponent);
  },

  earnerCollections: function() {
    var viewId = 'earnerCollections';
    var breadCrumbs = [
      { name: "Earner Home", url: '/earner'},
      { name: "My Collections", url: '/earner/collections' }
    ];

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <BreadCrumbs items={breadCrumbs} />
        <ActionBar 
          title="My Collections"
          viewId={viewId}
          items={this.props.actionBars[viewId] || []}
          updateActivePanel={this.updateActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        <EarnerCollectionList
          collections={APIStore.getCollection('earner_collections')}
          perPage={50}
        />
      </MainComponent>
    );

    // render the view
    return this.render_base(mainComponent);
  },

  earnerCollectionDetail: function(collectionSlug) {
    var viewId = 'earnerCollectionDetail';

    var collection = APIStore.getFirstItemByPropertyValue(
      'earner_collections', 'slug', collectionSlug
    );
    if (!collection)
      return this.render_base("Collection not found.");
    badgesIndexList = _.pluck(collection.badges, 'id');
    badgesInCollection = APIStore.filter(
      'earner_badges', 'id', badgesIndexList
    ); 

    var breadCrumbs = [
      { name: "Earner Home", url: '/earner'},
      { name: "My Collections", url: '/earner/collections' },
      { name: collection.name, url: '/earner/collections/' + collectionSlug }
    ];

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <BreadCrumbs items={breadCrumbs} />
        <ActionBar 
          title={collection.name}
          viewId={viewId}
          items={this.props.actionBars[viewId] || []}
          updateActivePanel={this.updateActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          collection={collection}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          formKey={collectionSlug}
        />
        <EarnerCollectionDetail
          name={collection.name}
          slug={collection.slug}
          clickable={false}
          description={collection.description}
          share_url={collection.share_url}
          badgeList={badgesInCollection}
          display="thumbnail"
        />
      </MainComponent>
    );

    // render the view
    return this.render_base(mainComponent);
  },

  issuerMain: function() {
    var viewId = "issuerMain";
    dependenciesMet = APIStore.collectionsExist(this.dependencies['issuerMain']);

    var mainComponent = (
      <MainComponent viewId={viewId} dependenciesLoaded={dependenciesMet}>
        <ActionBar
          title="My Issuers"
          viewId={viewId}
          items={this.props.actionBars[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        <IssuerList
          viewId={viewId}
          issuers={APIStore.getCollection('issuer_issuers')}
          badgeclasses={APIStore.getCollection('issuer_badgeclasses')}
        />
      </MainComponent>
    );
    return this.render_base(mainComponent);
  },

  issuerDetail: function(issuerSlug, params){
    if (!params['perPage'])
      params['perPage'] = 10
    if (!params['currentPage'])
      params['currentPage'] = 1

    var viewId = "issuerDetail-" + issuerSlug;
    var issuer = APIStore.getFirstItemByPropertyValue('issuer_issuers', 'slug', issuerSlug);
    var badgeClasses = APIStore.filter('issuer_badgeclasses', 'issuer', issuer.json.id);
    var breadCrumbs = [
      { name: "My Issuers", url: '/issuer'},
      { name: issuer.name, url: '/issuer/issuers/' + issuerSlug }
    ];
    var mainComponent = (
      <MainComponent viewId={viewId}>
        <BreadCrumbs items={breadCrumbs} />
        <IssuerDisplay {...issuer} />
        <ActionBar 
          title="Active Badges"
          viewId={viewId}
          items={this.props.actionBars['issuerDetail']}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          issuerSlug={issuerSlug}
          formKey={issuerSlug}
        />
        <BadgeClassList
          issuerSlug={issuerSlug}
          badgeClasses={badgeClasses}
          display="detail"
          perPage={params.perPage}
          currentPage={params.currentPage}
        />
      </MainComponent>
    )

    return this.render_base(mainComponent);
  },

  badgeClassDetail: function(issuerSlug, badgeClassSlug){
    var loadingInstances = ""; var badgeInstanceDisplayLength;
    var viewId = "badgeClassDetail-" + badgeClassSlug;
    var issuer = APIStore.getFirstItemByPropertyValue('issuer_issuers', 'slug', issuerSlug);
    var badgeClass = APIStore.getFirstItemByPropertyValue('issuer_badgeclasses', 'slug', badgeClassSlug);
    var badgeInstances = APIStore.filter('issuer_badgeinstances', 'badgeclass', badgeClass.json.id);
    var instanceRequestStatus = null;

    var breadCrumbs = [
      { name: "My Issuers", url: '/issuer'},
      { name: issuer.name, url: '/issuer/issuers/' + issuerSlug},
      { name: badgeClass.name, url: "/issuer/issuers/" + issuerSlug + "/badges/" + badgeClass.slug}
    ];

    // Trigger a get on instances if none are found and haven't been requested yet:
    var instanceGetPath = '/v1' + breadCrumbs[2].url + '/assertions';
    if (badgeInstances.length == 0 && !APIStore.hasAlreadyRequested(instanceGetPath)){
      loadingInstances = "loading...";
      APIActions.APIGetData({
        actionUrl: instanceGetPath,
        apiCollectionKey: 'issuer_badgeinstances',
        successfulHttpStatus: [200]
      });
      instanceRequestStatus = "waiting";
    }
    badgeInstanceDisplayLength = loadingInstances != "" ? loadingInstances : badgeInstances.length

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <BreadCrumbs items={breadCrumbs} />
        <HeadingBar 
          title={issuer.name + ": " + badgeClass.name}
        />
        <BadgeClassDetail {...badgeClass} />
        <ActionBar
          title={"Recipients (" + badgeInstanceDisplayLength + ")"}
          viewId={viewId}
          items={this.props.actionBars['badgeClassDetail']}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
          issuerSlug={issuerSlug}
          badgeClassSlug={badgeClassSlug}
          formKey={issuerSlug + '/' + badgeClassSlug}
        />
        <BadgeInstanceList
          issuerSlug={issuerSlug}
          badgeClass={badgeClass}
          badgeInstances={badgeInstances}
          dataRequestStatus={instanceRequestStatus}
        />
      </MainComponent>
    )

    return this.render_base(mainComponent);
  },

  issuerCertificateForm: function() {
    var mainComponent = "CERTIFICATE FORM"
    return this.render_base(mainComponent);
  },
  issuerCertificateView: function() {
    var mainComponent = "CERTIFICATE VIEW"
    return this.render_base(mainComponent);
  },

  consumerMain: function() {
    var activeBadgeId = null;
    var viewId = "consumerMain";
    var consumerBadges = APIStore.getCollection('consumerBadges');

    if (this.state.activePanels && viewId in this.state.activePanels && 'content' in this.state.activePanels[viewId]){
      activeBadgeId = this.state.activePanels[viewId].content.badgeId;
    }

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <SecondaryMenu viewId={viewId} items={this.props.secondaryMenus[viewId]} />
        <ActionBar 
          title="Understand Badges"
          viewId={viewId}
          items={this.props.actionBars[viewId]}
          updateActivePanel={this.updateActivePanel}
          activePanel={this.state.activePanels[viewId]}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        <ConsumerBadgeList
          viewId={viewId}
          consumerBadges={consumerBadges}
          updateActivePanel={this.updateActivePanel}
          activeBadgeId={activeBadgeId}
        />
      </MainComponent>
    );
    
    return this.render_base(mainComponent);
  },

  notFound: function() {
    ClickActions.navigateOut(window.location.href);
    return this.render_base("Redirecting...");
  }
  
});


module.exports = App;
