var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');

var ActiveActions = require('../actions/activeActions');
var MenuStore = assign({}, EventEmitter.prototype);
 

// TODO Replace with data entered into the Dispatcher on page load
MenuStore.defaultItems = {
  topMenu: {
    items: [
      // { title: "messages", url: "#", icon: "fa-envelope", children: [] },
      // { title: "tasks", url: "#", icon: "fa-tasks", children: []},
      { title: "alerts", url: "#", icon: "fa-bell", children: [] },
      { title: "user", url: "#", icon: "fa-user", children: [
        { title: "User Profile", url: "/#user", icon: "fa-user", children: [] },
        { title: "Settings", url: "/#user/settings", icon: "fa-gear", children: [] },
        { title: "Log Out", url: "/logout", icon: "fa-sign-out", children: [] }
      ] }
    ]
  },
  roleMenu: {
    items: []
  },
  secondaryMenus: {
      earnerHome: [
        { title: "My Badges", url: "/earn", icon: "fa-certificate", children: [] },
        { title: "My Collections", url: "/earn/collections", icon: "fa-folder-open", children: [] },
        { title: "Discover Badges", url: "/earn/discover", icon: "fa-globe", children: [] }
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
      earnerHome: [
        { 
          title: "Add Badge",
          buttonType: "primary",
          icon: "fa-certificate", 
          activePanelCommand: { type: "EarnerBadgeForm", content: { badgeId: null } } 
        }
      ],
      issuerMain: [
        {
          title: "Define New Badge",
          buttonType: "primary",
          icon: "fa-pencil-square-o",
          activePanelCommand: { type: "IssuerBadgeForm", content: {}}
        },
        {
          title: "Notify Earners",
          buttonType: "default",
          icon: "fa-envelope",
          activePanelCommand: { type: "IssuerNotificationForm", content: {}}
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
  if ('issuer' in initialData)
    MenuStore.menus.roleMenu.items.push(
      { title: "Issue", url: "/issuer", icon: "fa-mail-forward", children: []}
    );

  if ('earner' in initialData)
    MenuStore.menus.roleMenu.items.push(
      { title: "Earn", url: "/earn", icon: "fa-certificate", children: [] }
    );
  if ('consumer' in initialData)
    MenuStore.menus.roleMenu.items.push(  
      { title: "Understand", url: "/understand", icon: "fa-info-circle", children: [] }
    );
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
