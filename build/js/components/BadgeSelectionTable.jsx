var React = require('react');
var _ = require('lodash');
var moment = require('moment');
var Table = require('fixed-data-table').Table;
var Column = require('fixed-data-table').Column;

// Stores
var APIStore = require('../stores/APIStore');
var CollectionStore = require('../stores/CollectionStore').CollectionStore;
var FormStore = require('../stores/FormStore');

// Actions
var APIActions = require('../actions/api');
var CollectionStoreActions = require('../actions/CollectionStoreActions').CollectionStoreActions;

// Components
var Pagination = require('../components/Pagination.jsx').Pagination;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Detail = require('../components/Detail.jsx').Detail;
var Button = require('../components/Button.jsx').Button;


// Cell rendering helpers for the FixedDataTable React component
var fixedDataTable = {
    headerRenderer: function(column, label, cellDataKey, columnData, rowData, width) {
        var allSelected = this.state.selected.every(function(selected) { return selected; });
        if (column.icon) {
            return (<p onClick={this.toggleAll} className={"icon_ icon_-notext icon_-check " + (allSelected ? "icon_-check-is-active" : "")}>Selected</p> );
        }
        return (<p className="truncate_" title={label}>{label}</p>);
    },

    tableColumns: [
        {
            label: "Select",
            icon: "icon_-check",
            width: 56,
            render: function(cellData, cellDataKey, rowData, rowIndex, columnData, width) {
                return (
                    <span className={"icon_ icon_-notext icon_-check " + (rowData.selected ? "icon_-check-is-active" : "")}>
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
                        <div>
                            <button>
                                <img src={_.get(rowData, 'json.image.id')} width="40" height="40" alt={_.get(rowData, 'json.badge.name[@value]')} />
                            </button>
                            <button className="truncate_">
                                {_.get(rowData, 'json.badge.name[@value]')}
                            </button>
                        </div>
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
        stored: React.PropTypes.bool,
        onRowClick: React.PropTypes.func,
        batchRowClick: React.PropTypes.func,
    },

    getDefaultProps: function() {
        return {
            badges: [],
            initialSelectedBadges: [],
            widthHint: 800,
            heightHint: 600,
            stored: false,
            onRowClick: function(){},
        };
    },

    getInitialState: function() {
        var selected = this.props.badges.map(function(badge, i) {
            return (this.props.initialSelectedBadges.indexOf(badge.id) !== -1);
        }.bind(this));

        if (this.props.stored) {
            CollectionStoreActions.init(selected.slice());
        }

        return {
            selected: selected.slice(),
        }
    },

    componentDidMount: function() {
        CollectionStore.addListener('COLLECTION_BADGE_TOGGLED', this.toggleCollectionState); 
    },

    onRowClick: function(ev, rowIndex, rowData) {
        this.props.onRowClick(ev, rowIndex, rowData);

        if (this.props.stored) {
            CollectionStoreActions.toggle(rowIndex, rowData);
        }
        else {
            this.toggleCollectionState(rowIndex, rowData);
        }
    },

    toggleCollectionState: function(rowIndex, rowData) {
        var newSelectionArray = this.state.selected.slice();
        newSelectionArray[rowIndex] = ! newSelectionArray[rowIndex]; 
        this.setState({selected: newSelectionArray});
    },

    toggleAll: function() {
        var allSelected = this.state.selected.every(function(selected) { return selected; });
        var newSelectionArray = this.state.selected.slice();
        newSelectionArray = newSelectionArray.map(function() { return ! allSelected; });
        this.props.batchRowClick(this.props.badges, ! allSelected);
        this.setState({selected: newSelectionArray});
    },

    rowGetter: function(rowIndex) {
        return _.extend({ selected: this.state.selected[rowIndex] },
                        this.props.badges[rowIndex]);
    },

    rowClassNameGetter: function(rowIndex) {
        if (this.state.selected[rowIndex]) {
            return "is-selected";
        }
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
                rowClassNameGetter={this.rowClassNameGetter}
                rowsCount={this.props.badges.length}
                width={this.props.widthHint}
                maxHeight={this.props.heightHint}
                headerHeight={56}
                onRowClick={this.onRowClick}>
                    {renderedColumns}
            </Table>
        );
    }
});


module.exports = {
    BadgeSelectionTable:BadgeSelectionTable,
}
