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
      { title: "user", url: "#", icon: "icon_ icon_-small icon_-right icon_-dropdownlight", children: [
        { title: "User Profile", url: "/accounts/", icon: "fa-user", children: [] },
        { title: "LTI Info", url: "/accounts/lti", icon: "fa-gear", children: [] },

        // { title: "Settings", url: "/#user/settings", icon: "fa-gear", children: [] },
        { title: "Log Out", url: "/logout", icon: "fa-sign-out", children: [] }
      ] }
    ]
  },
  badgebookMenu: {
    items: [
      { title: "Objectives", url: "/badgebook/objectives", icon: "fa-certificate", children: [] },
      { title: "Progress", url: "/badgebook/progress", icon: "fa-tasks", children: [] }
    ]
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
      ],
      badgebookProgress: [],
      badgebookObjectives: [
        {
          title: "Create New Badge",
          buttonType: "primary",
          icon: "fa-pencil-square-o",
          activePanelCommand: { type: "BadgeClassCreateUpdateForm", content: {}}
        }
      ],
  }
};

MenuStore.menus = {
  topMenu: MenuStore.defaultItems.topMenu,
  badgebookMenu: MenuStore.defaultItems.badgebookMenu,
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

  var newItems = [], item;
  // try to load the variable declared as initialData in the view template
  if (initialData.installed_apps.indexOf('composer') > -1)
    newItems.push(
      { title: "My Badges", url: "/earner/badges", icon: "", children: [] },
      { title: "My Collections", url: "/earner/collections", icon: "", children: [] }
    );
  if (initialData.installed_apps.indexOf('issuer') > -1)
    newItems.push(
      { title: "Issue", url: "/issuer", icon: "", children: []}
    );
  if (initialData.installed_apps.indexOf('consumer') > -1)
    newItems.push(
      { title: "Understand", url: "/understand", icon: "", children: [] }
    );
  if ('user' in initialData) {
    for (index in MenuStore.menus.topMenu.items) {
      item = MenuStore.menus.topMenu.items[index];
      if (item.title = 'user') {
        item['title'] = initialData.user.username;
        newItems.push(item);
        break;
      }
    }
  }
  MenuStore.menus.topMenu.items = newItems;

  if (initialData.lti_learner) {
    MenuStore.menus.badgebookMenu.items = [];
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
      MenuStore.storeInitialData();
      MenuStore.emit('INITIAL_DATA_LOADED');
      break;

    case 'CLICK_CLOSE_MENU':
      MenuStore.emit('UNCAUGHT_DOCUMENT_CLICK');
      break;

    case 'CLOSE_MODAL':
      MenuStore.emit('CLOSE_MODAL');
      break;

    default:
      // do naaathing.
  }
});

module.exports = {
  getAllItems: MenuStore.getAllItems,
  addListener: MenuStore.addListener,
  removeListener: MenuStore.removeListener,
  listeners: MenuStore.listeners,
  once: MenuStore.once,
  on: MenuStore.addListener,
  dispatchToken: MenuStore.dispatchToken,
  emit: MenuStore.emit
};
