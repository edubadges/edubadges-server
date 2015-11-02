/**
 * Concentric Sky Pattern Library:
 * Creates a navigation structure and source code example viewing in-browser for
 * defined modules (following SMACSS recommendations).
 */

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