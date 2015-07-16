var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');
var APIStore = require('../stores/APIStore');

var ActiveActions = require('../actions/activeActions');
var MenuStore = assign({}, EventEmitter.prototype);

 

// TODO Replace with data entered into the Dispatcher on page load
MenuStore.defaultItems = {
  topMenu: {
    items: [
      // { title: "messages", url: "#", icon: "fa-envelope", children: [] },
      // { title: "tasks", url: "#", icon: "fa-tasks", children: []},
      // { title: "alerts", url: "#", icon: "fa-bell", children: [] },
      { title: "user", url: "#", icon: "fa-user", children: [
        { title: "User Profile", url: "/accounts/", icon: "fa-user", children: [] },
        { title: "LTI Info", url: "/accounts/lti", icon: "fa-gear", children: [] },

        // { title: "Settings", url: "/#user/settings", icon: "fa-gear", children: [] },
        { title: "Log Out", url: "/logout", icon: "fa-sign-out", children: [] }
      ] }
    ]
  },
  roleMenu: {
    items: []
  },
  secondaryMenus: {
      earnerHome: [
        { title: "My Badges", url: "/earner/badges", icon: "fa-certificate", children: [] },
        { title: "My Collections", url: "/earner/collections", icon: "fa-folder-open", children: [] }
      ],
      issuerMain: [
        { title: "Issue Badges", url: "/issue/badges", icon: "fa-mail-forward", children: [] },
        { title: "Issuer Settings", url: "/issue/settings", icon: "fa-cog", children: [] }
      ],
      consumerMain: [
        { title: "Compare Badges", url: "/understand/badges", icon: "fa-mail-forward", children: [] },
        { title: "Endorse Acceptable Badges", url: "/understand/endorse", icon: "fa-cog", children: [] }
      ]
  },
  actionBars: {
      earnerBadges: [
        { 
          title: "Import Badge",
          buttonType: "primary",
          icon: "fa-certificate", 
          activePanelCommand: { type: "EarnerBadgeImportForm", content: { badgeId: null } } 
        }
      ],
      earnerCollections: [
        { 
          title: "Add Collection",
          buttonType: "primary",
          icon: "fa-folder-open", 
          activePanelCommand: { type: "EarnerCollectionCreateForm", content: {} } 
        }
      ],
      earnerCollectionDetail: [
        { 
          title: "Edit Details",
          buttonType: "primary",
          icon: "fa-pencil-square-o", 
          activePanelCommand: { type: "EarnerCollectionEditForm", content: {} } 
        }
      ],
      issuerMain: [
      ],
      issuerDetail: [
        {
          title: "Add Badge",
          buttonType: "primary",
          icon: "fa-pencil-square-o",
          activePanelCommand: { type: "BadgeClassCreateUpdateForm", content: {}}
        }
      ],
      badgeClassDetail: [
        {
          title: "Issue Badge",
          buttonType: "primary",
          icon: "fa-mail-forward",
          activePanelCommand: { type: "BadgeInstanceCreateUpdateForm", content: {}}
        }
      ],
      consumerMain: [
        { 
          title: "Analyze Badge",
          buttonType: "primary",
          icon: "fa-upload", 
          activePanelCommand: { type: "ConsumerBadgeForm", content: { badgeId: null } } 
        }
      ]
  }
};

MenuStore.menus = {
  topMenu: MenuStore.defaultItems.topMenu,
  roleMenu: MenuStore.defaultItems.roleMenu,
  secondaryMenus: MenuStore.defaultItems.secondaryMenus,
  actionBars: MenuStore.defaultItems.actionBars
}

MenuStore.getAllItems = function(menu, viewName) {
  // if (typeof viewName === 'undefined')

  return MenuStore.menus[menu];
};

MenuStore.addListener = function(type, callback) {
  MenuStore.on(type, callback);
};

// MenuStore.removeListener = function(type, callback) {
//   MenuStore.removeListener(type, callback);
// };

MenuStore.storeInitialData = function() {
  if (typeof initialData == 'undefined')
    return;

  // try to load the variable declared as initialData in the view template
  if (initialData.installed_apps.indexOf('issuer') > -1)
    MenuStore.menus.roleMenu.items.push(
      { title: "Issue", url: "/issuer", icon: "fa-mail-forward", children: []}
    );
  if (initialData.installed_apps.indexOf('composer') > -1)
    MenuStore.menus.roleMenu.items.push(
      { title: "Earn", url: "/earner", icon: "fa-certificate", children: [] }
    );
  if (initialData.installed_apps.indexOf('consumer') > -1)
    MenuStore.menus.roleMenu.items.push(  
      { title: "Understand", url: "/understand", icon: "fa-info-circle", children: [] }
    );
  if ('user' in initialData){
    for (index in MenuStore.menus.topMenu.items){
      item = MenuStore.menus.topMenu.items[index];
      if (item.title = 'user')
        item['title'] = initialData.user.username
      break;
    }

  }

  if ('user' in initialData && initialData.user.approvedIssuer){
    MenuStore.menus.actionBars.issuerMain = [
      {
        title: "Add Issuer",
        buttonType: "primary",
        icon: "fa-pencil-square-o",
        activePanelCommand: { type: "IssuerCreateUpdateForm", content: {}}
      }
    ];
  }
}


// Register with the dispatcher
MenuStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'APP_WILL_MOUNT':
      MenuStore.storeInitialData()
      MenuStore.emit('INITIAL_DATA_LOADED');
      break;

    case 'CLICK_CLOSE_MENU':
      MenuStore.emit('UNCAUGHT_DOCUMENT_CLICK');
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  getAllItems: MenuStore.getAllItems,
  addListener: MenuStore.addListener,
  removeListener: MenuStore.removeListener
}
