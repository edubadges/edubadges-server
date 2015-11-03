var React = require('react');
var _ = require('lodash');
var moment = require('moment');
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


// Cell rendering helpers
var renderSelectCell = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
    return (<span className="icon_ icon_-notext icon_-add">icon</span>);
};
var renderBadgeName = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
    return (
        <div className="l-horizontal">
            <button><img srcst="http://placehold.it/96x96 2x, http://placehold.it/48x48" src="http://placehold.it/48x48" width="48" height="48" alt="Badge Image" /></button>
            <button className="truncate_ action_ action_-tertiary">Badge Name</button>
        </div>
    );
};
var renderIssuerName = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
    return "Issuer Name"
};
var renderIssueDateCell = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
  return moment("2015-11-02T16:20Z").format('MMMM Do YYYY, h:mm:ss a');
};


var BadgeSelectionTable = React.createClass({
    proptypes: {
        badges: React.PropTypes.array.isRequired,
        widthHint: React.PropTypes.number,
        heightHint: React.PropTypes.number,
    },
    getDefaultProps: function(){
        return {
            badges: [],
            widthHint: 800,
            heightHint: 600,
            cellRenderer: this.cellRenderer
        };
    },

    rowGetter: function(rowIndex) {
        return this.props.badges[rowIndex];
    },
    cellRenderer: function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
        return (<div className="fixeddatatable-x-cell">{cellData}</div>);
    },

    render: function() {

        var headings = [
            {label: "Select", icon: "icon_-add", cellRenderer: renderSelectCell, width: 56},
            {label: "Badge Name", cellRenderer: renderBadgeName, width: 240, align: "left"},
            {label: "Issuer", cellRenderer: renderIssuerName, align: "left"},
            {label: "Issue Date", cellRenderer: renderIssueDateCell, align: "left"}
        ];
        var columns = headings.map(function(colInfo, i){
            var headerRenderer = function(label, cellDataKey, columnData, rowData, width) {
                if (colInfo.icon)
                    return (<span className={"icon_ icon_-notext " + colInfo.icon}></span> );
                return (<span className="truncate_" title={label}>{label}</span>);
            };
            return (
                <Column key={"award-column-"+i}
                    label={colInfo.label}
                    headerRenderer={headerRenderer}
                    cellRenderer={colInfo.cellRenderer}
                    align={colInfo.align || "center"}
                    width={colInfo.width || 120}
                    dataKey={"col-" + i}
                    fixed={false}
                    flexGrow={1}
                     />);
        }.bind(this));

        return (
            <Table
                rowHeight={56}
                rowGetter={this.rowGetter}
                rowsCount={this.props.badges.length}
                width={this.props.widthHint}
                maxHeight={this.props.heightHint}
                headerHeight={36}
                >
                {columns}
            </Table>
        );
    }
});

module.exports.BadgeSelectionTable = BadgeSelectionTable;


