var Dispatcher = require('../dispatcher/appDispatcher');
var EventEmitter = require('events').EventEmitter;
var assign = require('object-assign');



var MenuStore = assign({}, EventEmitter.prototype);
 

// TODO Replace with data entered into the Dispatcher on page load
MenuStore.defaultItems = {
  topMenu: {
    items: [
      { title: "messages", url: "#", icon: "fa-envelope", children: [] },
      { title: "tasks", url: "#", icon: "fa-tasks", children: []},
      { title: "alerts", url: "#", icon: "fa-bell", children: [] },
      { title: "user", url: "#", icon: "fa-user", children: [
        { title: "User Profile", url: "/#user", icon: "fa-user", children: [] },
        { title: "Settings", url: "/#user/settings", icon: "fa-gear", children: [] },
        { title: "Log Out", url: "/logout", icon: "fa-sign-out", children: [] }
      ] }
    ]
  },
  sidebarMenu: {
    items: [
      { title: "Earn", url: "/earn", icon: "fa-certificate", children: [] },
      { title: "Issue", url: "#", icon: "fa-mail-forward", children: [
        { title: "Award Badges", url: "/issue", icon: "fa-bookmark", children: [] },
        { title: "Notify Earners", url: "/issue/notify", icon: "fa-envelope", children: [] },
        { title: "Print Certificates", url: "/certificates", icon: "fa-file", children: []}
      ]},
      { title: "Understand", url: "/understand", icon: "fa-info-circle", children: [] }
    ]
  }
};

MenuStore.getAllItems = function(menu) {
  return MenuStore.defaultItems[menu];
};

MenuStore.addListener = function(type, callback) {
  MenuStore.on(type, callback);
};

MenuStore.removeListener = function(type, callback) {
  MenuStore.removeListener(type, callback);
};

// Register with the dispatcher
MenuStore.dispatchToken = appDispatcher.register(function(payload){
  var action = payload.action;

  switch(action.type){
    case 'CLICK_CLOSE_MENU':
      MenuStore.emit('uncaught_document_click');
      break;

    default:
      // do naaathing.
  }
});

console.log("OMG I'M GOING TO LOG THE EVENT EMITTER");
console.log(MenuStore);

module.exports = {
  getAllItems: MenuStore.getAllItems,
  addListener: MenuStore.addListener,
  removeListener: MenuStore.removeListener
}
