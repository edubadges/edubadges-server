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
var MainComponent = require ('../components/MainComponent.jsx');
var ActionBar = require('../components/ActionBar.jsx').ActionBar;
var Heading = require('../components/Heading.jsx').Heading;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Button = require('../components/Button.jsx').Button;
var SubmitButton = require('../components/Button.jsx').SubmitButton;
var HeadingBar = require('../components/ActionBar.jsx').HeadingBar;
var ActivePanel = require('../components/ActivePanel.jsx');
var OpenBadgeList = require('../components/OpenBadgeList.jsx');
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var EarnerBadgeForm = require('../components/Form.jsx').EarnerBadgeForm;
var IssuerNotificationForm = require('../components/Form.jsx').IssuerNotificationForm;
var IssuerList = require('../components/IssuerDisplay.jsx').IssuerList;
var IssuerDisplay = require('../components/IssuerDisplay.jsx').IssuerDisplay;
var BadgeClassDetail = require('../components/BadgeClassDisplay.jsx').BadgeClassDetail;
var BadgeClassTable = require('../components/BadgeClassDisplay.jsx').BadgeClassTable;
var BadgeClassList = require('../components/BadgeClassDisplay.jsx').BadgeClassList;
var BadgeInstanceList = require('../components/BadgeInstanceDisplay.jsx').BadgeInstanceList;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');
var CollectionShareInfo = require('../components/EarnerBadgeCollection.jsx').CollectionShareInfo;
var EarnerCollectionList = require('../components/EarnerBadgeCollection.jsx').EarnerCollectionList;
var ManageCollection = require('../components/EarnerBadgeCollection.jsx').ManageCollection;
var ConsumerBadgeList = require('../components/ConsumerBadgeList.jsx');
var BadgeStudio = require('../components/BadgeStudio.jsx').BadgeStudio;

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

    var currentItem = _.find(this.state.topMenu.items, function(o) { return o.url == newRoute; }, this);
    if (this.isMounted() && currentItem && currentItem.title != this.state.activeTopMenu) {
        this.setState({'activeTopMenu': currentItem.title});
    }

    navigate(newRoute);
  },


  getDefaultProps: function() {
    return {
      path: urllite(window.location.href).pathname + urllite(window.location.href).search,
      appTitle: 'Badgr',
      actionBars: MenuStore.getAllItems('actionBars'),
    };
  },
  getInitialState: function() {
    return {
      earnerBadges: [],
      requestedCollections: [],
      activePanels: ActiveActionStore.getAllActiveActions(),
      topMenu: MenuStore.getAllItems('topMenu'),
      activeTopMenu: null,
      openTopMenu: null
    };
  },
  componentWillMount: function() {
    MenuStore.addListener('INITIAL_DATA_LOADED', function(){ this.updateMenu('topMenu');}.bind(this));
    LifeCycleActions.appWillMount();
  },
  componentDidMount: function() {
    MenuStore.addListener('UNCAUGHT_DOCUMENT_CLICK', this.hideOpenTopMenu);
    RouteStore.addListener('ROUTE_CHANGED', this.handleRouteChange);
    APIStore.addListener('DATA_UPDATED', function(collectionKey){
        if (collectionKey === 'issuer_badgeinstances') {
            // An update to issuer_badgeinstances should always update issuer_badgeclasses as recipient_count will be stale
            APIActions.APIFetchCollections(['issuer_badgeclasses']);
        }
      if (this.isMounted())
        this.setState({});
    }.bind(this));
    ActiveActionStore.addListener('ACTIVE_ACTION_UPDATED', this.handleActivePanelUpdate);
  },

  // Menu visual display functions:
  setOpenTopMenu: function(key){
    if (this.state.openTopMenu != key)
      this.setState({openTopMenu: key});
    else
      this.setState({openTopMenu: null});
  },
  hideOpenTopMenu: function(){
    /* Handler called to close open sub-menus:
    It runs whenever a click is made outside a '.closable' element.
    */
    if (this.isMounted() && this.state.openTopMenu != null)
      this.setState({openTopMenu: null});
  },
  updateMenu: function(key){
    if (this.isMounted()) {

        var newState = {}
        newState[key] = MenuStore.getAllItems(key);

        if (key == 'topMenu') {
          var currentItem = _.find(newState[key].items, function(o) { return o.url == this.props.path; }, this);
          if (currentItem) {
            newState.activeTopMenu = currentItem.title;
          }
        }
      this.setState(newState);
    }
  },

  updateActivePanel: function(viewId, update){
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
        <div className="x-owner">
            <header className="header_ l-wrapper">
            <a className="header_-x-logo" href="/">
                <img src="/static/images/header-logo.svg" width="193" height="89" />
            </a>
            <nav>
                <TopLinks
                    items={MenuStore.getAllItems('topMenu').items}
                    setOpen={this.setOpenTopMenu}
                    active={this.state.activeTopMenu}
                    open={this.state.openTopMenu}
                    showLabels={true} />
            </nav>
            </header>

            { mainComponent }
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

    function handleFormSubmit(formId, formType) {
        var formData = FormStore.getFormData(formId);
        if (formData.formState.actionState !== "waiting") {
            FormActions.submitForm(formId, formType);
        }
    }

    var dialogFormId = "EarnerBadgeImportForm"
    var formProps = FormConfigStore.getConfig(dialogFormId);
    FormStore.getOrInitFormData(dialogFormId, formProps);

    var actions=[
        <SubmitButton formId={dialogFormId} label="Import Badge" />
    ];
    var dialog = (
        <Dialog formId={dialogFormId} dialogId="import-badge" actions={actions} className="closable">
            <Heading size="small"
                        title="Import Badge"
                        subtitle="Verify an Open Badge and add it to your library by uploading a badge image or entering its URL."/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId} dependenciesLoaded={dependenciesMet}>
          <Heading
            size="large"
            title="My Badges"
            subtitle="Import your Open Badges with Badgr! Upload images to verify your badges, and then add them to collections to share with your friends and colleagues."
            rule={true}>
                <DialogOpener dialog={dialog} dialogId="import-badge" key="import-badge">
                    <Button className="action_" label="Import Badge" propagateClick={true}/>
                </DialogOpener>
          </Heading>
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
    var navigateToBadgeList = function(){
      ClickActions.navigateLocalPath('/earner/badges');
    };

    var importUrl = params['url'];
    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId} dependenciesLoaded={dependenciesMet}>
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

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId}>
        <Heading
          backButton="/earner/badges"
          size="large"
          title={badge.json.badge.name['@value']}
          subtitle={badge.json.badge.description['@value']}
          rule={true} />
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

    var dialogFormId = "EarnerCollectionCreateForm";
    var formProps = FormConfigStore.getConfig(dialogFormId);
    FormStore.getOrInitFormData(dialogFormId, formProps);

    var actions=[
        <SubmitButton formId={dialogFormId} label="Add Collection" />
    ];
    var dialog = (
        <Dialog formId={dialogFormId} dialogId="add-collection" actions={actions} className="closable">
            <Heading size="small"
                        title="New Collection"
                        subtitle=""/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId}>
          <Heading
            size="large"
            title="My Collections"
          subtitle="Define collections to organize your badges, then display your collections to friends, employers, or other collaborators."
            rule={true}>
                <DialogOpener dialog={dialog} dialogId="add-collection" key="add-collection">
                    <Button className="action_" label="Add Collection" propagateClick={true}/>
                </DialogOpener>
          </Heading>
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
    badgesInCollection = APIStore.filter('earner_badges', 'id', badgesIndexList); 

    var dialogFormId = "EarnerCollectionEditForm";
    var formProps = FormConfigStore.getConfig(dialogFormId, {}, {
        collection: {
            slug: collectionSlug,
            name: collection.name,
            description: collection.description,
        }
    });
    FormStore.getOrInitFormData(dialogFormId, formProps)

    var editActions=[
        <SubmitButton formId={dialogFormId} label="Edit Collection" />
    ];
    var editDialog = (
        <Dialog formId={dialogFormId} dialogId="edit-collection" actions={editActions} className="closable">
            <Heading size="small"
                        title="Edit Collection"
                        subtitle=""/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);

    var shareDialogAction = (<Button label="Toggle Share" onClick={function() { document.getElementById('toggle-share').click() }} />);
    var shareDialog = (
        <Dialog formId={dialogFormId} actions={shareDialogAction} dialogId="share-collection" className="closable">
            <Heading size="small"
                        title="Share Collection"
                        subtitle="Once enabled, anyone with the link will be able to view this collection."/>

            <CollectionShareInfo initialShareUrl={collection.share_url} collectionSlug={collectionSlug} />
        </Dialog>);

    var badgeIdsInCollection = APIStore.filter('earner_badges', 'id', _.pluck(badgesInCollection, 'id'));

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId}>
          <Heading
            backButton="/earner/collections"
            size="large"
            title={collection.name}
            subtitle={collection.description}
            rule={true}>
                <DialogOpener dialog={editDialog} dialogId="edit-collection" key="edit-collection">
                    <Button className="action_" label="Edit" propagateClick={true}/>
                </DialogOpener>
                <DialogOpener dialog={shareDialog} dialogId="share-collection" key="share-collection">
                    <Button className="action_" label="Share" propagateClick={true}/>
                </DialogOpener>
                <ManageCollection label="Add / Remove badges" slug={collectionSlug} badgeList={badgesInCollection} />
          </Heading>
          <EarnerBadgeList
              display="thumbnail"
              badges={badgeIdsInCollection}
              moreLink={'/earner/collections/' + collectionSlug}
              handleClick={this.selectBadgeId} />
      </MainComponent>
    );

    // render the view
    return this.render_base(mainComponent);
  },

  issuerMain: function() {
    var viewId = "issuerMain";
    dependenciesMet = APIStore.collectionsExist(this.dependencies['issuerMain']);

    var dialogFormId = "IssuerCreateUpdateForm"
    var formProps = FormConfigStore.getConfig(dialogFormId);
    FormStore.getOrInitFormData(dialogFormId, formProps);

    var actions=[
        <SubmitButton key="submit" formId={dialogFormId} label="Add Issuer" />
    ];
    var dialog = (
        <Dialog formId={dialogFormId} dialogId="add-issuer" actions={actions} className="closable">
            <Heading size="small"
                        title="New Issuer"
                        subtitle=""/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);


    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId} dependenciesLoaded={dependenciesMet}>
          <Heading
            size="large"
            title="My Issuers"
            subtitle=""
            rule={true}>
                <DialogOpener dialog={dialog} dialogId="add-issuer" key="add-issuer">
                    <Button className="action_" label="Add Issuer" propagateClick={true}/>
                </DialogOpener>
          </Heading>
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
      params['perPage'] = -1
    if (!params['currentPage'])
      params['currentPage'] = 1

    var viewId = "issuerDetail-" + issuerSlug;
    var issuer = APIStore.getFirstItemByPropertyValue('issuer_issuers', 'slug', issuerSlug);
    var issuersBadgeClasses = APIStore.filter('issuer_badgeclasses', 'issuer', issuer.json.id);

    var dialogFormId = "BadgeClassCreateUpdateForm" + issuerSlug;
    var formProps = FormConfigStore.getConfig("BadgeClassCreateUpdateForm", {}, {issuerSlug: issuerSlug});
    formProps.formId = dialogFormId;
    formProps.apiContext.formId = dialogFormId;
    FormStore.getOrInitFormData(dialogFormId, formProps);

    var formData = FormStore.getFormData(dialogFormId);
    if (formData.apiContext) {
        var parseSlug = new RegExp("/v1/issuer/issuers/([^/]+)/badges");
        var actionSlug = parseSlug.exec(formData.apiContext.actionUrl).pop();
        if (actionSlug && actionSlug !== issuerSlug) {
            FormStore.initFormData(dialogFormId, formProps);
        }
    }

    var showBadgeStudio = function(e) {
      e.stopPropagation();

      var formState = FormStore.getFormState(dialogFormId);
      this.setState({showingBadgeStudio: true, badgeStudioDetail: formState}, function() {
        var dialog = document.getElementById("issuer-add-badge")
        if (dialog) {
          dialog.close();
          dialog.classList.remove('is-visible');
        }
        var overlay = document.querySelector("body > div._dialog_overlay")
        if (overlay) {
          document.body.removeChild(overlay);
        }

      });
    }.bind(this);
    var handleBadgeComplete = function(dataURL, blob) {
      if (dataURL && blob) {

        FormActions.patchForm(dialogFormId, {
          'image': blob,
          'imageData': dataURL
        });

      }
      
      this.setState({showingBadgeStudio: false}, function() {
        var dialog = document.getElementById("issuer-add-badge")
        if (dialog) {
          dialog.showModal();
          dialog.classList.add('is-visible');
        }

      });

    }.bind(this);


    var actions=[
        <SubmitButton formId={dialogFormId} label="Create" />
    ];
    var dialog = (
        <Dialog formId={dialogFormId} dialogId="issuer-add-badge" actions={actions} className="closable">
            <Heading size="small"
                        title="Create New Badge"
                        subtitle=""/>
            <BasicAPIForm handleBadgeStudioClick={showBadgeStudio} hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);

    if (this.state.showingBadgeStudio) {

      var mainComponent = (
        <MainComponent className="l-vertical" mainClassName="l-mainoverride" viewId={viewId}>
          <BadgeStudio handleBadgeComplete={handleBadgeComplete} badgeDetail={this.state.badgeStudioDetail}/>
        </MainComponent>);

    } else {

      var mainComponent = (
        <MainComponent className="l-vertical" viewId={viewId}>
          <Heading
            backButton="/issuer"
            title={issuer.name}
            subtitle={issuer.description}
            rule={true}>
                <DialogOpener dialog={dialog} dialogId="issuer-add-badge" key="issuer-add-badge">
                    <Button className="action_" label="Add Badge" propagateClick={true}/>
                </DialogOpener>
          </Heading>
          <IssuerDisplay {...issuer} />
          <Heading
            size="small"
            title="Active Badges" />
          <BadgeClassTable
            issuerSlug={issuerSlug}
            badgeClasses={issuersBadgeClasses}
          />
        </MainComponent>);

    }


    return this.render_base(mainComponent);
  },

  badgeClassDetail: function(issuerSlug, badgeClassSlug){
    var loadingInstances = ""; var badgeInstanceDisplayLength;
    var viewId = "badgeClassDetail-" + badgeClassSlug;
    var badgeClass = APIStore.getFirstItemByPropertyValue('issuer_badgeclasses', 'slug', badgeClassSlug);
    var issuer = APIStore.getFirstItemByPropertyValue('issuer_issuers', 'slug', issuerSlug);
    var badgeInstances = APIStore.filter('issuer_badgeinstances', 'badge_class', badgeClass.json.id);
    var instanceRequestStatus = null;

    // Trigger a get on instances if none are found and haven't been requested yet:
    var instanceGetPath = "/v1/issuer/issuers/"+ issuerSlug +"/badges/"+ badgeClass.slug +"/assertions";
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

    badgeClass.issuer = issuer;

    var dialogFormId = "BadgeInstanceCreateUpdateForm" + issuerSlug + badgeClassSlug;
    var formProps = FormConfigStore.getConfig("BadgeInstanceCreateUpdateForm", {}, {issuerSlug: issuerSlug, badgeClassSlug: badgeClass.slug});
    formProps.formId = dialogFormId;
    formProps.apiContext.formId = dialogFormId;
    FormStore.getOrInitFormData(dialogFormId, formProps);

    var actions=[
        <SubmitButton key="submit" formId={dialogFormId} label="Submit" />
    ];
    var dialog = (
        <Dialog formId={dialogFormId} dialogId="create-badge-instance" actions={actions} className="closable">
            <Heading size="small"
                        title="New Badge Instance"
                        subtitle=""/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...formProps} />
        </Dialog>);

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId}>

        <ul className="breadcrumb_">
            <li><a href="/issuer">Issue Badges</a></li>
            <li><a href={"/issuer/issuers/"+issuer.slug}>{issuer.name}</a></li>
        </ul>


        <Heading
          backButton={"/issuer/issuers/"+ issuer.slug}
          title={badgeClass.name}
          subtitle={badgeClass.description}
          rule={true}>
              <DialogOpener dialog={dialog} dialogId="create-badge-instance" key="create-badge-instance">
                <Button className="action_" label="Issue Badge" propagateClick={true}/>
              </DialogOpener>
        </Heading>
        <BadgeClassDetail {...badgeClass} />
        <Heading size="small" title="Badge Recipients" meta={badgeInstances.length} />
        <BadgeInstanceList
          issuerSlug={issuerSlug}
          badgeClass={badgeClass}
          badgeInstances={badgeInstances}
          dataRequestStatus={instanceRequestStatus}
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

  consumerMain: function() {
    var activeBadgeId = null;
    var viewId = "consumerMain";
    var consumerBadges = APIStore.getCollection('consumerBadges');

    if (this.state.activePanels && viewId in this.state.activePanels && 'content' in this.state.activePanels[viewId]){
      activeBadgeId = this.state.activePanels[viewId].content.badgeId;
    }

    var mainComponent = (
      <MainComponent className="l-vertical" viewId={viewId}>
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
