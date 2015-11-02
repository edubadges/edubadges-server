var React = require('react');
var _ = require('lodash');
var FixedDataTable = require('fixed-data-table');
var Table = FixedDataTable.Table;
var Column = FixedDataTable.Column;


var APIActions = require('../actions/api');
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');

var Pagination = require('../components/Pagination.jsx').Pagination;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Detail = require('../components/Detail.jsx').Detail;
var Button = require('../components/Button.jsx').Button;


var CollectionBadgeTable = React.createClass({
    proptypes: {
        badges: React.PropTypes.array.isRequired,
        widthHint: React.PropTypes.number,
        heightHint: React.PropTypes.number,
    },
    getDefaultProps: function(){
        return {

        };
    },



    rowGetter: function(){return [];},
    render: function() {
        return (
            <Table
                rowHeight={56}
                rowGetter={this.rowGetter}
                rowsCount={this.props.badges.length}
                width={this.props.widthHint}
                maxHeight={this.props.heightHint}
                headerHeight={56}
                >
                {columns}
            </Table>
        );
    }
});

module.exports.CollectionBadgeTable = CollectionBadgeTable;


