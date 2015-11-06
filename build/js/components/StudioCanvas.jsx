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
        shape: undefined, // 'circle'
        backgroundImage: undefined,
        backgroundColor: undefined,
        graphic: undefined,
        graphicColor: undefined
    };
  },

  componentDidMount: function() {

    BadgeStudio.util.loadSVG = function(prefix, name, callback) {
      var path = initialData.STATIC_URL + 'badgestudio/' + prefix + '/' + name + '.svg'
      fabric.loadSVGFromURL(path, function (objects, options) {
        var svg = new fabric.Group(objects)

        var scale;
        if (this.props.width > this.props.height) {
          scale = this.props.width / svg.width;
        }
        else {
          scale = this.props.height / svg.height;
        }
        svg.scaleX = scale;
        svg.scaleY = scale;
        return callback(svg)
      }.bind(this))
    }.bind(this);

    this.studio = new BadgeStudio(this.refs.canvas.getDOMNode());
    this.updateBadgeStudio(this.props);
  },

  shouldComponentUpdate: function(nextProps, nextState) {
    return false;
  },

  componentWillReceiveProps: function(nextProps) {
    if (this.props != nextProps)
      this.updateBadgeStudio(nextProps);
  },


  updateBadgeStudio: function(props) {

    // shape is required, default to circle
    if (props.shape) {
      this.studio.setShape(props.shape.split('.')[0], function() {
        
      });
    } else {
      this.studio.setShape('circle');
    }

    // background color is required, default to white
    this.studio.setBackgroundColor(props.backgroundColor || '#ffffff')

    // graphic color is required, default to black
    this.studio.setGlyphColor(props.graphicColor || '#000000');

    // remove background image if none is set
    if (props.backgroundImage) {
      this.studio.setBackgroundImage(initialData.STATIC_URL + "badgestudio/backgrounds/" + props.backgroundImage);
    } else {
      this.studio.removeBackgroundImage();
    }

    // remove graphic if none is set
    if (props.graphic) {
      this.studio.setGlyphFromURL(initialData.STATIC_URL + "badgestudio/graphics/" + props.graphic, function() {
          if (props.graphicColor)
              this.studio.setGlyphColor(props.graphicColor || '#000000');
          this.studio.glyph.set({scaleX: 0.7, scaleY: 0.7});
          this.studio.glyph.center();
          this.studio.canvas.renderAll();
      }.bind(this));
    } else {
      this.studio.removeGlyph();
    }

    // remove background pattern if none is set
    if (props.backgroundPattern) {
      this.studio.setBackgroundPattern(initialData.STATIC_URL + "badgestudio/backgrounds/" + props.backgroundPattern);
    } else {
      this.studio.removeBackgroundPattern();
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
