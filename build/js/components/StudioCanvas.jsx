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

        var padding = 10;
        var width = this.props.width - padding*2
        var height = this.props.height - padding*2

        // scale svg to fit into our viewport
        var scale;
        if (svg.width > svg.height) {
          scale = width / svg.width;
        }
        else {
          scale = height / svg.height;
        }
        svg.scaleX = scale;
        svg.scaleY = scale;
        // center svg in viewport
        svg.left = (this.props.width - (svg.width*svg.scaleX))/2;
        svg.top = (this.props.height - (svg.height*svg.scaleY))/2;
        return callback(svg)
      }.bind(this))
    }.bind(this);

    this.studio = new BadgeStudio(this.refs.canvas.getDOMNode());
    this.updateBadgeStudio(this.props, true);
  },

  shouldComponentUpdate: function(nextProps, nextState) {
    return false;
  },

  componentWillReceiveProps: function(nextProps) {
    if (this.props != nextProps)
      this.updateBadgeStudio(nextProps);
  },


  updateBadgeStudio: function(props, force) {

    // shape is required, default to circle
    var shape = props.shape ? props.shape.split('.')[0] : 'circle'
    if (shape != this.props.shape || force) {
      this.studio.setShape(shape);
    }

    // background color is required, default to white
    if (props.backgroundColor != this.props.backgroundColor || force) {
      this.studio.setBackgroundColor(props.backgroundColor || '#ffffff')
    }

    // graphic color is required, default to black
    if (props.graphicColor != this.props.graphicColor || force) {
      this.studio.setGlyphColor(props.graphicColor || '#000000');
    }

    // remove background image if none is set
    if (props.backgroundImage != this.props.backgroundImage || force) {
      if (props.backgroundImage) {
        this.studio.setBackgroundImage(initialData.STATIC_URL + "badgestudio/backgrounds/" + props.backgroundImage);
      } else {
        this.studio.removeBackgroundImage();
      }
    }

    // remove graphic if none is set
    if (props.graphic != this.props.graphic || force) {
      if (props.graphic) {
        this.studio.setGlyphFromURL(initialData.STATIC_URL + "badgestudio/graphics/" + props.graphic, function() {
            this.studio.setGlyphColor(props.graphicColor || '#000000');

            // scale glyph to 1/3 the viewport 
            var width = this.props.width/3
            var height = this.props.height/3
            var scale;
            if (this.studio.glyph.width > this.studio.glyph.height) {
              scale = width / this.studio.glyph.width;
            }
            else {
              scale = height / this.studio.glyph.height;
            }

            this.studio.glyph.set({scaleX: scale, scaleY: scale});
            this.studio.glyph.center();
            this.studio.canvas.renderAll();
        }.bind(this));
      } else {
        this.studio.removeGlyph();
      }
    }

    // remove background pattern if none is set
    if (props.backgroundPattern != this.props.backgroundPattern || force) {
      if (props.backgroundPattern) {
        this.studio.setBackgroundPattern(initialData.STATIC_URL + "badgestudio/backgrounds/" + props.backgroundPattern);
      } else {
        this.studio.removeBackgroundPattern();
      }
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
