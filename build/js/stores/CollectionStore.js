var Flux = require('flux');
var EventEmitter = require('events').EventEmitter;
//var Dispatcher = (new Flux.Dispatcher());
var Dispatcher = require('../dispatcher/appDispatcher');
var assign = require('object-assign');


var _selected = [];
var CollectionStore = assign({}, EventEmitter.prototype, {
    getSelections: function() {
        return _selected;
    },

    dispatcherToken: Dispatcher.register(function(payload) {
        var action = payload.action;

        switch (action.type) {
            case 'INITIALIZE_COLLECTION':
                _selected = action.selected;
                CollectionStore.emit('COLLECTION_INITIALIZED');
                break;

            case 'TOGGLE_COLLECTION_SELECTION':
                _selected[action.rowIndex] = ! _selected[action.rowIndex];
                CollectionStore.emit('COLLECTION_BADGE_TOGGLED', action.rowIndex, action.rowData);
                break;
        }
    }),
});


module.exports = {
    CollectionStore: CollectionStore,
};
