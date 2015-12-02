var Dispatcher = require('../dispatcher/appDispatcher');


var CollectionStoreActions = {
    init: function(selected) {
        Dispatcher.dispatch({action: {
            type: 'INITIALIZE_COLLECTION',
            selected: selected,
        }});
    },
    toggle: function(rowIndex, rowData) {
        Dispatcher.dispatch({action: {
            type: 'TOGGLE_COLLECTION_SELECTION',
            rowIndex: rowIndex,
            rowData: rowData,
        }});
    },
};


module.exports = {
    CollectionStoreActions: CollectionStoreActions,
};
