var React = require('react');
var RouterMixin = require('react-mini-router').RouterMixin;
var navigate = require('react-mini-router').navigate;
var assign = require('object-assign');

// Stores
var RouteStore = require('../stores/RouteStore');
var MenuStore = require('../stores/MenuStore');
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');
var UserStore = require('../stores/UserStore');
var ActiveActionStore = require('../stores/ActiveActionStore');

// Components
var TopLinks = require('../components/TopLinks.jsx');
var SideBarNav = require('../components/SideBarNav.jsx');
var MainComponent = require ('../components/MainComponent.jsx');
var SecondaryMenu = require('../components/SecondaryMenu.jsx');
var ActionBar = require('../components/ActionBar.jsx');
var ActivePanel = require('../components/ActivePanel.jsx');
var OpenBadgeList = require('../components/OpenBadgeList.jsx');
var EarnerBadgeForm = require('../components/Form.jsx').EarnerBadgeForm;
var IssuerNotificationForm = require('../components/Form.jsx').IssuerNotificationForm
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');

// Actions
var LifeCycleActions = require('../actions/lifecycle');
var FormActions = require('../actions/forms');
var ActiveActions = require('../actions/activeActions');

var App = React.createClass({
  mixins: [RouterMixin],

  // Route configuration: 
  routes: {
    '/': 'home',
    '/earn': 'earnerHome',
    // '/earn/badges': 'earnerBadgeForm',
    // '/earn/badges/:id': 'earnerBadgeForm',
    '/issue/badges': 'issuerMain',
    '/issuer/certificates/new': 'issuerCertificateForm',
    '/issuer/certificates/:id': 'issuerCertificateView', 
    '/understand': 'consumerHome'
  },

  // Route handling:
  handleRouteChange: function() {
    newRoute = RouteStore.getCurrentRoute();
    navigate(newRoute);
  },


  getDefaultProps: function() {
    return {
      appTitle: 'Badge Trust',
      roleMenu: MenuStore.getAllItems('roleMenu'),
      actionMenu: MenuStore.getAllItems('topMenu'),
      actionBars: MenuStore.getAllItems('actionBars'),
      secondaryMenus: MenuStore.getAllItems('secondaryMenus')
    };
  },
  getInitialState: function() {
    return {
      earnerBadges: [],
      activePanels: ActiveActionStore.getAllActiveActions(),
      path: window.location.pathname
    };
  },
  componentWillMount: function() {
    LifeCycleActions.appWillMount();
  },
  componentDidMount: function() {
    this.setState(
      { earnerBadges: APIStore.getCollection('earnerBadges') }
    );

    MenuStore.addListener('UNCAUGHT_DOCUMENT_CLICK', this._hideMenu);
    RouteStore.addListener('ROUTE_CHANGED', this.handleRouteChange);
    APIStore.addListener('DATA_UPDATED_earnerBadges', function(){
      // TODO: implement test: if (APIStore.routeUsesCollection(RouteStore.getCurrentRoute(), 'earnerBadges'))
      this.setState( {earnerBadges: APIStore.getCollection('earnerBadges')} );
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
  contextPropsForActivePanel: function(viewId){
    if (!(viewId in this.state.activePanels))
      return {};

    var context;
    var panel = this.state.activePanels[viewId];
    if (panel.type == "EarnerBadgeForm") {
      context = {
        recipientIds: UserStore.getProperty('earnerIds'),
        badgeId: panel.content.badgeId
      };
    }
    else if (panel.type == "OpenBadgeDisplay") {
      context = {
        badgeId: panel.content.badgeId,
        detailLevel: panel.content.detailLevel,
        badge: APIStore.getFirstItemByPropertyValue('earnerBadges', 'id', panel.content.badgeId)
      };
    }
    else if (panel.type == "IssuerNotificationForm") {
      context = {
      }
    }
    return context;
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
                <a className="navbar-brand" href="/"><img src="/static/images/header-logo-120.png" className="brand-logo" />
                  <span>{ this.props.appTitle }</span>
                </a>
                <div className="navbar-right">
                  <TopLinks items={this.props.roleMenu.items} setActive={function(key){}} active={null} showLabels={true} />
                  <TopLinks items={this.props.actionMenu.items} setActive={this.setActiveTopMenu} active={this.state.activeTopMenu} showLabels={false} />
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


  home: function() {
    var mainComponent = "HOME"
    return this.render_base(mainComponent);
  },

  earnerHome: function() {
    var activeBadgeId = null;
    var viewId = 'earnerHome';
    if (this.state.activePanels && viewId in this.state.activePanels && 'content' in this.state.activePanels[viewId]){
      activeBadgeId = this.state.activePanels[viewId].content.badgeId;
    }

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <SecondaryMenu viewId={viewId} items={this.props.secondaryMenus[viewId]} />
        <ActionBar 
          title="My Badges"
          viewId={viewId}
          items={this.props.actionBars[viewId]}
          updateActivePanel={this.updateActivePanel}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          {...this.contextPropsForActivePanel(viewId)}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        <EarnerBadgeList
          viewId={viewId}
          earnerBadges={this.state.earnerBadges}
          updateActivePanel={this.updateActivePanel}
          activeBadgeId={activeBadgeId}
        />
      </MainComponent>
    );

    // render the view
    return this.render_base(mainComponent);
  },

  issuerMain: function(id) {
    var viewId = "issuerMain";
  

    var mainComponent = (
      <MainComponent viewId={viewId}>
        <SecondaryMenu viewId={viewId} items={this.props.secondaryMenus[viewId]} />
        <ActionBar
          title="Issue Badges"
          viewId={viewId}
          items={this.props.actionBars[viewId]}
          updateActivePanel={this.updateActivePanel}
        />
        <ActivePanel
          viewId={viewId}
          {...this.state.activePanels[viewId]}
          {...this.contextPropsForActivePanel(viewId)}
          updateActivePanel={this.updateActivePanel}
          clearActivePanel={this.clearActivePanel}
        />
        
      </MainComponent>
    );
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

  consumerHome: function() {
    var mainComponent = "CONSUMER HOME"
    return this.render_base(mainComponent);
  },

  notFound: function() {
    var mainComponent = "NOT FOUND: " + this.state.path
    return this.render_base(mainComponent);
  }
  
});


module.exports = App;
