var React = require('react');
var FixedDataTable = require('fixed-data-table');
var Table = FixedDataTable.Table;
var Column = FixedDataTable.Column;
require('./polyfills');


/* MODULE fixeddatatable */
var dataRows = [
    ['Sally Student', 'Sally1', 'Sally2', 'Sally3'],
    ['Bill Student', 'Bill1', 'Bill2', 'Bill3'],
    ['Marge Student', 'Marge1', 'Marge2', 'Marge3'],
    ['Colin Student', 'Colin1', 'Colin2', 'Colin3'],
    ['Willard Student', 'Willard1', 'Willard2', 'Willard3'],
    ['Samantha Student', 'Samantha1', 'Samantha2', 'Samantha3'],
    ['Susan Student', 'Susan1', 'Susan2', 'Susan3'],
    ['Vegetarian Student', 'Vegetarian1', 'Vegetarian2', 'Vegetarian3'],
    ['Mohir Student', 'Mohir1', 'Mohir2', 'Mohir3'],
    ['Nate Student', 'Nate1', 'Nate2', 'Nate3'],
    ['Harry Student', 'Harry1', 'Harry2', 'Harry3']
];

function rowGetter(rowIndex){
    return dataRows[rowIndex];
}
function cellRenderer(cellData, cellDataKey, rowData, rowIndex, columnData, width){
    return (<span className="fixeddatatable-x-cell">{cellData}</span>);
}

React.render(
    (<Table
        rowHeight={50}
        rowGetter={rowGetter}
        rowsCount={dataRows.length}
        width={800}
        maxHeight={500}
        headerHeight={100}
    >
        <Column label="Student" width={300} dataKey={0} fixed={true} cellRenderer={cellRenderer} />
        <Column label="Module 1" width={400} dataKey={1} cellRenderer={cellRenderer} />
        <Column label="Module 2" width={400} dataKey={2} cellRenderer={cellRenderer} />
        <Column label="Module 3" width={400} dataKey={3} cellRenderer={cellRenderer} />
    </Table>),
    document.getElementById('REACT-fixeddatatable')
);
