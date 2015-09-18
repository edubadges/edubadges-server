var React = require('react');
var PatternItem = require('react-style-guide');

var FixedDataTable = require('fixed-data-table');
var Table = FixedDataTable.Table;
var Column = FixedDataTable.Column;


var ReactPatterns = React.createClass({
    fixedDataTable: function(){
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
            return (
                <span className="fixeddatatable-x-cell">{cellData}</span>
            );
        }

        return (
            <PatternItem
                title="Fixed Data Table"
                description="A table used for large sets of data that may fix headers and initial columns in view"
            >
                <Table
                    rowHeight={50}
                    rowGetter={rowGetter}
                    rowsCount={dataRows.length}
                    width={800}
                    maxHeight={500}
                    headerHeight={100}
                >
                    <Column label="Student" width={300} dataKey={0} fixed={true} cellRenderer={cellRenderer} />
                    <Column label="Module 1" width={400} dataKey={1} fixed={false} cellRenderer={cellRenderer} />
                    <Column label="Module 2" width={400} dataKey={2} fixed={false} cellRenderer={cellRenderer} />
                    <Column label="Module 3" width={400} dataKey={3} fixed={false} cellRenderer={cellRenderer} />
                </Table>
            </PatternItem>
        );
    },
    render: function(){
        return (
            <div className="reactpatterns">
                {this.fixedDataTable()}
            </div>
        );
    }
});


React.render(
    <ReactPatterns />,
    document.getElementById('ReactPatterns')
);



// Pattern Library base mechanics
function matchPattern(pattern) {
    var matchedElements = [];
    var allElements = document.getElementsByTagName('*');
    for (var i = 0; i < allElements.length; i++) {
        if (allElements[i].dataset.pattern == pattern) {
            matchedElements.push(allElements[i]);
        }
    }
    return matchedElements;
}

// Toggle states for menu (on container)

var container = document.querySelector('[data-pattern="container"]');

var navToggle = document.querySelector('[data-pattern="nav-toggle"]');

function toggleNav() {

    if (container.className == 'menu-visible') {

        container.className = '';

    } else {

        container.className = 'menu-visible';

    }

}

navToggle.onclick = function(){
    toggleNav();
};

var navItems = matchPattern('nav');

for (var i = 0; i < navItems.length; i++) {

    var navItem = navItems[i];

    navItem.onclick = function(){
        container.className = '';
    };

}

// Toggle states for code examples

function toggleContainer(element) {

    var toggle = element;

    var toggleParent = toggle.parentNode;

    if (toggle.className == 'is-active') {

        toggle.className = '';
        toggleParent.className = '';

    } else {

        toggle.className = 'is-active';
        toggleParent.className = 'is-active';

    }

}

// Create code examples

var patternCode = document.querySelectorAll('[data-pattern="code"]');

for (var i = 0; i < patternCode.length; i++) {

    // Grab the current code example in the loop
    var code = patternCode[i];

    // Grab its content
    var codeContent = code.innerHTML;

    // Find its parent
    var codeParent = code.parentNode;

    // Create the container to put it in
    var display = document.createElement('pre');
    var displayCode = document.createElement('code');
    var displayToggle = document.createElement('button');

    // Set up the toggle
    displayToggle.textContent = 'Toggle Code';
    displayToggle.setAttribute('data-pattern', 'code-toggle');

    // Set the attribute on the container
    display.setAttribute('data-pattern', 'code-display');

    // Set the code content as text inside of our new element
    displayCode.textContent = codeContent;

    // Put our code into the new container
    display.appendChild(displayToggle);
    display.appendChild(displayCode);


    // Put the new container above the code example
    codeParent.insertBefore(display, code);

}

var toggles = matchPattern('code-toggle');

for (var i = 0; i < toggles.length; i++) {

    var toggle = toggles[i];

    toggle.onclick = function(){
        toggleContainer(this);
    };

}

// Create titles based on pattern IDs

var patterns = document.querySelectorAll('[data-pattern="pattern"], [data-pattern="pattern-secondary"]');

for (var i = 0; i < patterns.length; i++) {
    var pattern = patterns[i];
    var patternID = pattern.id;
    var title = document.createElement('div');
    title.setAttribute('data-pattern', 'title');
    title.textContent = patternID;
    pattern.appendChild(title);
    pattern.insertBefore(title, pattern.firstChild);
}

// Creates a navigation for primary patterns

var primaryPatterns = document.querySelectorAll('[data-pattern="pattern"]');

for (var i = 0; i < primaryPatterns.length; i++) {
    var pattern = primaryPatterns[i];
    var patternID = pattern.id;
    var nav = document.querySelector('[data-pattern="nav-menu"]');
    var navItem = document.createElement('li');
    var navAnchor = document.createElement('a');
    navAnchor.setAttribute('href', '#' + patternID);
    navAnchor.textContent = patternID;
    navItem.appendChild(navAnchor);
    nav.insertBefore(navItem, nav.lastChild);
}