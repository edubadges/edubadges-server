var React = require('react');

var StudioCanvas = React.createClass({
  propTypes: {
    width: React.PropTypes.number.isRequired,
    height: React.PropTypes.number.isRequired,
    shape: React.PropTypes.string,
    backgroundImage: React.PropTypes.string,
    backgroundColor: React.PropTypes.string,
    graphic: React.PropTypes.string,
    graphicColor: React.PropTypes.string,
  },
  getDefaultProps: function() {
    return {
        width: 400,
        height: 400,
        shape: 'shield',
        backgroundImage: undefined,
        backgroundColor: '#555555',
        graphic: undefined,
        graphicColor: '#ffffff',
    };
  },

  componentDidMount: function() {
    console.log("mounted", this.refs);
    console.log("canvas", this.refs.canvas);

    this.studio = new BadgeStudio(this.refs.canvas.getDOMNode());
    this.studio.setBackgroundColor('rgba(24,124,255,0.3)');
  },

  shouldComponentUpdate: function(nextProps, nextState) {
    console.log("shouldComponentUpdate", nextProps, nextState)
    return false;
  },

  componentWillReceiveProps: function(nextProps) {
    console.log("componentWillReceiveProps", nextProps, this.props)

    this.studio.setBackgroundColor(nextProps.backgroundColor)
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