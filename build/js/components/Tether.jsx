/** @jsx React.DOM */

/* this was taken from: https://gist.github.com/mik01aj/5b98bad5b5ba04a1b93f */


var _ = require('lodash');
var React = require('react');
var Tether = require('tether');



/*
 *
 * TetheredElement js helper
 *
 */

// NOTE: This is not a React component. It's a plain JS object that manages a React component.
function TetheredElement(reactComponent, tetherOptions) {
    this.reactComponent = reactComponent;

    this.domNode = document.createElement('div');
    this.domNode.style.position = 'absolute'; // needed for Tether
    this.domNode.style.background = 'white';
    document.body.appendChild(this.domNode);

    this.tether = new Tether(_.merge({
        element: this.domNode,
    }, tetherOptions));

    this.update();
}
TetheredElement.prototype.update = function () {
    React.render(
        this.reactComponent,
        this.domNode,
        function(){ return this.tether.position()}
    );
};
TetheredElement.prototype.destroy = function () {
    React.unmountComponentAtNode(this.domNode);
    this.domNode.parentNode.removeChild(this.domNode);
    this.tether.destroy();
};


/*
 *
 * TetherTarget - react component
 *
 * Usage:
 *

var tetherOptions = {
    // element and target are set automatically
    attachment: 'top center',
    constraints: [
        {to: 'window', pin: true, attachment: 'together'},
    ],
};
<TetherTarget tethered={ <i>I'm tethered!</i> } tetherOptions={ tetherOptions }>
    <h1>Hello world! I'm a big box, which is the Tether target!</h1>
</TetherTarget>

 *
 */

var TetherTarget = React.createClass({
    propTypes: {
        tethered: React.PropTypes.node.isRequired,
        tetherOptions: React.PropTypes.object.isRequired,
        handleTethered: React.PropTypes.func
    },
    getInitialState: function () {
        return {tooltipVisible: false};
    },
    componentDidMount: function () {
        var tetherOptions = _.merge({
            target: this.getDOMNode(),
        }, this.props.tetherOptions);
        this.tethered = new TetheredElement(this.props.tethered, tetherOptions);
        if (this.props.handleTethered) {
            this.props.handleTethered()
        }
    },
    componentWillUnmount: function () {
        this.tethered.destroy();
    },
    componentDidUpdate: function () {
        this.tethered.update();
    },
    render: function () {
        var divProps = _.omit(this.props, ['tethered', 'tetherOptions', 'handleTethered']);
        return <div {... divProps }>
            { this.props.children }
        </div>;
    },
});


module.exports = {
    TetheredElement: TetheredElement,
    TetherTarget: TetherTarget
};