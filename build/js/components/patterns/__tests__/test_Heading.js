/** @jsx React.DOM */

jest.dontMock('../Heading.jsx');

describe('Heading', function() {
    it('renders a heading without subtitle', function() {
        var React = require('react/addons');
        var Heading = require('../Heading.jsx').Heading;
        var TestUtils = React.addons.TestUtils;

        var heading = TestUtils.renderIntoDocument(<Heading title="My Title"/>);

        var h1 = TestUtils.findRenderedDOMComponentWithTag(heading, 'h1');
        expect(React.findDOMNode(h1).textContent).toEqual("My Title");

        var p = TestUtils.findRenderedDOMComponentWithTag(heading, 'p');
        expect(p).toEqual(null);

    });
});