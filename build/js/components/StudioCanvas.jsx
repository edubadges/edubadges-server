var React = require('react');

var StudioCanvas = React.createClass({
  propTypes: {
    width: React.PropTypes.number.isRequired,
    height: React.PropTypes.number.isRequired,
    shape: React.PropTypes.string,
    backgroundImage: React.PropTypes.string,
    backgroundColor: React.PropTypes.string,
    backgroundPattern: React.PropTypes.string,
    graphic: React.PropTypes.string,
    graphicColor: React.PropTypes.string,
  },
  getDefaultProps: function() {
    return {
        width: 500,
        height: 500,
        shape: 'shield',
        backgroundImage: undefined,
        backgroundColor: undefined,
        graphic: undefined,
        graphicColor: '#ffffff',
    };
  },

  componentDidMount: function() {

    BadgeStudio.util.loadSVG = function(prefix, name, callback) {
      var path = initialData.STATIC_URL + 'badgestudio/' + prefix + '/' + name + '.svg'
      fabric.loadSVGFromURL(path, function (objects, options) {
        return callback(new fabric.Group(objects))
      })
    }

    this.studio = new BadgeStudio(this.refs.canvas.getDOMNode());
    this.updateBadgeStudio(this.props);
  },

  shouldComponentUpdate: function(nextProps, nextState) {
    return false;
  },

  componentWillReceiveProps: function(nextProps) {
    this.updateBadgeStudio(nextProps);
  },


  updateBadgeStudio: function(props) {
    if (props.shape) {
        this.studio.setShape(props.shape);
    }

    if (props.backgroundImage) {
        this.studio.setBackgroundImage(props.backgroundImage);
    } else {
        this.studio.removeBackgroundImage();
        this.studio.setBackgroundColor(props.backgroundColor)
    }

    if (props.graphic) {
        this.studio.setGlyphFromURL(props.graphic);
    }
    else {
        this.studio.removeGlyph();
    }

    if (props.backgroundPattern) {
        this.studio.setBackgroundPattern(props.backgroundPattern)
    } else {
        this.studio.removeBackgroundPattern();
    }

    if (props.graphicColor) {
        this.studio.setGlyphColor(props.graphicColor);
    }
  },


  render: function() {
    return (
        <canvas ref="canvas" width={this.props.width} height={this.props.height}>
        </canvas>
    );
  },


});


module.exports = {
    StudioCanvas: StudioCanvas
}