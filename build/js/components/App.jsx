var React = require('react');
var RouterMixin = require('react-mini-router').RouterMixin;
var navigate = require('react-mini-router').navigate;

// Stores
var RouteStore = require('../stores/RouteStore.js');
var ItemsStore = require('../stores/MenuStore.js');

// Components
var TopLinks = require('../components/TopLinks.jsx');
var SideBarNav = require('../components/SideBarNav.jsx');
var OpenBadgeList = require('../components/OpenBadgeList.jsx');

// Actions
var LifeCycleActions = require('../actions/lifecycle');

var App = React.createClass({
  mixins: [RouterMixin],

  // Route configuration: 
  routes: {
    '/': 'home',
    '/earn': 'earnerHome',
    '/issue/notifications/new': 'issuerNotificationForm',
    '/issue/notifications/:id': 'issuerNotificationView',
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
      topMenu: ItemsStore.getAllItems('topMenu'),
      sideBarNav: ItemsStore.getAllItems('sidebarMenu'),
      appTitle: 'Badge Trust'
    };
  },
  getInitialState: function() {
    return {
      activeTopMenu: null,
      path: window.location.pathname
    };
  },
  componentWillMount: function() {
    LifeCycleActions.appWillMount();
  },
  componentDidMount: function() {
    ItemsStore.addListener('UNCAUGHT_DOCUMENT_CLICK', this._hideMenu);
    RouteStore.addListener('ROUTE_CHANGED', this.handleRouteChange);
  },

  // Menu visual display functions:
  setActiveTopMenu: function(key){
    this.setState({activeTopMenu: key});
  },
  _hideMenu: function(){
    if (this.state.activeTopMenu != null)
      this.setState({activeTopMenu: null});
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
        <header>
          <nav className="navbar navbar-default navbar-static-top" role="navigation">

            <div className="navbar-header">
              <button type="button" className="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
                <span className="sr-only">Toggle navigation</span>
                <i className="fa fa-fw fa-bars"></i>
              </button>
              <a className="navbar-brand" href="/">{ this.props.appTitle }</a>
              <div className="navbar-right">
                <TopLinks items={this.props.topMenu.items} setActive={this.setActiveTopMenu} active={this.state.activeTopMenu} />
              </div>
            </div>  

            <div className="navbar-default sidebar" role="navigation">
              <SideBarNav items={this.props.sideBarNav.items} />
            </div>
          </nav>
        </header>

        <section className="main-section content-container">
          <div id="page-wrapper" className="page-wrapper">
            <div className="container-fluid">
              <div className="row">
                { mainComponent }
              </div>
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
    var mainComponent = ( <OpenBadgeList /> );
    return this.render_base(mainComponent);
  },

  issuerNotificationForm: function() {
    var mainComponent = "NOTIFICATION FORM"
    return this.render_base(mainComponent);
  },
  issuerNotificationView: function() {
    var mainComponent = "NOTIFICATION VIEW"
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
