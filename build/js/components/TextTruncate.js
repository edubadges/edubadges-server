/*

Taken from: https://github.com/ShinyChang/React-Text-Truncate
and modified to work with react 0.13
 -- Wiggins [March 2016]
 

Original License:

The MIT License (MIT)

Copyright (c) 2015 Shiny Chang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

var React = require('react');
var MenuStore = require('../stores/MenuStore');

var TextTruncate = React.createClass({
    propTypes: {
        text: React.PropTypes.string,
        className: React.PropTypes.string,
        truncateText: React.PropTypes.string,
        line: React.PropTypes.number,
        showTitle: React.PropTypes.bool
    },

    getDefaultProps:function(){
        return {
            text: '',
            truncateText: '…',
            line: 1,
            showTitle: true,
            className: "",
        }
    },

    componentWillMount: function() {
        this.onResize = this.onResize.bind(this);
        var canvas = document.createElement('canvas');
        var docFragment = document.createDocumentFragment();
        docFragment.appendChild(canvas);
        this.canvas = canvas.getContext('2d');
    },
    componentDidMount: function() {
        this.scopeElement = React.findDOMNode(this.refs.scope);
        var style = window.getComputedStyle(this.scopeElement);
        var font = [];
        font.push(style['font-weight']);
        font.push(style['font-style']);
        font.push(style['font-size']);
        font.push(style['font-family']);
        this.canvas.font = font.join(' ');
        this.forceUpdate();

        window.addEventListener('resize', this.onResize);
        MenuStore.addListener('OPEN_DIALOG', this.onResize);
    },
    componentWillUnmount: function() {
        window.removeEventListener('resize', this.onResize);
        MenuStore.removeListener('OPEN_DIALOG', this.onResize);
    },
    onResize:function() {
        this.forceUpdate();
    },
    measureWidth:function(text) {
        return this.canvas.measureText(text).width;
    },
    getRenderText:function() {
        var textWidth = this.measureWidth(this.props.text);
        var scopeElement = this.scopeElement;
        var scopeWidth = scopeElement.offsetWidth;

        if (scopeWidth >= textWidth) {
            return this.props.text;
        } else {
            var n = 0;
            var max = this.props.text.length;
            var text = '';
            var splitPos = 0;
            var startPos = 0;
            var line = this.props.line;
            while(line--) {
                var ext = line ? '' : this.props.truncateText;
                while(n <= max) {
                    n++;
                    text = this.props.text.substr(startPos, n);
                    if (this.measureWidth(text + ext) > scopeWidth) {
                        splitPos = text.lastIndexOf(' ');
                        if (splitPos === -1) {
                            splitPos = n - 1;
                        }
                        startPos += splitPos;
                        break;
                    }
                }
                if (n >= max) {
                    startPos = max;
                    break;
                }
                n = 0;
            }
            return startPos === max
                      ? this.props.text
                      : this.props.text.substr(0, startPos - 1) + this.props.truncateText;
        }
    },
    render:function() {
        var text = this.props.text.substring(0,30) + this.props.truncateText;
        if (this.refs.scope) {
            text = this.getRenderText();
        }
        var attrs = {
            ref: 'scope'
        };
        if (this.props.showTitle) {
            attrs.title = this.props.text;
        }
        if (this.props.className) {
            attrs.className = this.props.className;
        }

        return React.createElement('div', attrs, text);
    }
});

module.exports = TextTruncate;