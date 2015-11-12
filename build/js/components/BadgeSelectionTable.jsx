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
    return (
      <span className={rowData.selected ? "icon_ icon_-notext icon_-selectfilled" : "icon_ icon_-notext icon_-selectempty"}>
          {rowData.selected ? "Selected" : "Not selected"}
      </span>
    );
};
var renderBadgeName = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
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
};
var renderIssuerName = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
    return _.get(rowData, 'json.badge.issuer.name[@value]');
};
var renderIssueDateCell = function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
  return moment(_.get(rowData, 'json.issuedOn[@value]')).format('MMMM Do YYYY');
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
            initialSelectedBadges: [],
            widthHint: 800,
            heightHint: 600,
            cellRenderer: this.cellRenderer
        };
    },
    getInitialState: function(){
        var state = {
            selected: []
        };
        for (var i=0; i<this.props.badges.length; i++){
            state['selected'][i] = this.props.initialSelectedBadges.indexOf(this.props.badges[i].id) > -1
        }
        return state;
    },

    rowGetter: function(rowIndex) {
        var data = this.props.badges[rowIndex];
        data['selected'] = this.state.selected[rowIndex];
        return data;
    },
    cellRenderer: function(cellData, cellDataKey, rowData, rowIndex, columnData, width){
        return (<div className="fixeddatatable-x-cell">{cellData}</div>);
    },
    onRowClick: function(ev, rowIndex, rowData){
        var selected = this.state.selected;
        selected[rowIndex] = !selected[rowIndex];
        this.setState({selected: selected});
        this.forceUpdate();
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
                onRowClick={this.onRowClick}
                >
                {columns}
            </Table>
        );
    }
});

module.exports.BadgeSelectionTable = BadgeSelectionTable;


