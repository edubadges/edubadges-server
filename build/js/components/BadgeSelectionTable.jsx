var React = require('react');
var _ = require('lodash');
var moment = require('moment');
var Table = require('fixed-data-table').Table;
var Column = require('fixed-data-table').Column;

var APIActions = require('../actions/api');
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');

var Pagination = require('../components/Pagination.jsx').Pagination;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Detail = require('../components/Detail.jsx').Detail;
var Button = require('../components/Button.jsx').Button;


// Cell rendering helpers for the FixedDataTable React component
var fixedDataTable = {
    headerRenderer: function(column, label, cellDataKey, columnData, rowData, width) {
        if (column.icon) {
            return (<span className={"icon_ icon_-notext " + column.icon}></span> );
        }
        return (<span className="truncate_" title={label}>{label}</span>);
    },

    tableColumns: [
        {
            label: "Select",
            icon: "icon_-add",
            width: 56,
            render: function(cellData, cellDataKey, rowData, rowIndex, columnData, width) {
                return (
                    <span className={"icon_ icon_-notext icon_-select" + (rowData.selected ? "filled" : "empty")}>
                        {rowData.selected ? "Selected" : "Not selected"}
                    </span>
                );
            }
        },
        {
            label: "Badge Name",
            align: "left",
            width: 240,
            render: function(cellData, cellDataKey, rowData, rowIndex, columnData, width) {
                return (
                    <div className="l-horizontal">
                        <button>
                            <img src={_.get(rowData, 'json.image.id')} width="48" height="48" alt={_.get(rowData, 'json.badge.name[@value]')} />
                        </button>
                        <button className="truncate_ action_ action_-tertiary">
                            {_.get(rowData, 'json.badge.name[@value]')}
                        </button>
                    </div>
                );
            }
        },
        {
            label: "Issuer",
            align: "left",
            render: function(cellData, cellDataKey, rowData, rowIndex, columnData, width) {
                return _.get(rowData, 'json.badge.issuer.name[@value]');
            }
        },
        {
            label: "Issue Date",
            align: "left",
            render: function(cellData, cellDataKey, rowData, rowIndex, columnData, width) {
                return moment(_.get(rowData, 'json.issuedOn[@value]')).format('MMMM Do YYYY');
            }
        },
    ],
}

var BadgeSelectionTable = React.createClass({
    propTypes: {
        badges: React.PropTypes.array.isRequired,
        initialSelectedBadges: React.PropTypes.array,
        widthHint: React.PropTypes.number,
        heightHint: React.PropTypes.number,
    },

    getDefaultProps: function(){
        return {
            badges: [],
            initialSelectedBadges: [],
            widthHint: 800,
            heightHint: 600,
        };
    },

    getInitialState: function(){
        return {
            selected: this.props.badges.map(function(badge, i) {
                return (this.props.initialSelectedBadges.indexOf(badge.id) !== -1);
            }.bind(this))
        }
    },

    rowGetter: function(rowIndex) {
        return _.extend({ selected: this.state.selected[rowIndex] },
                        this.props.badges[rowIndex]);
    },

    onRowClick: function(ev, rowIndex, rowData) {
        var newSelectionArray = _.extend({}, this.state.selected);
        newSelectionArray[rowIndex] = ! newSelectionArray[rowIndex]; 
        this.setState({selected: newSelectionArray});
    },

    render: function() {
        var renderedColumns = fixedDataTable.tableColumns.map(function(column, i) {
            return (
                <Column key={"award-column-"+i}
                    label={column.label}
                    headerRenderer={fixedDataTable.headerRenderer.bind(this, column)}
                    cellRenderer={column.render}
                    align={column.align || "center"}
                    width={column.width || 120}
                    dataKey={"col-" + i}
                    fixed={false}
                    flexGrow={1} />);
        }.bind(this));

        return (
            <Table
                rowHeight={56}
                rowGetter={this.rowGetter}
                rowsCount={this.props.badges.length}
                width={this.props.widthHint}
                maxHeight={this.props.heightHint}
                headerHeight={36}
                onRowClick={this.onRowClick}>
                    {renderedColumns}
            </Table>
        );
    }
});


module.exports = {
    BadgeSelectionTable:BadgeSelectionTable,
}
