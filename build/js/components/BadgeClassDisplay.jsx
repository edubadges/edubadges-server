var React = require('react');

// Components
var Property = require('../components/BadgeDisplay.jsx').Property;

BadgeClassThumbnail = React.createClass({
  render: function() {
    return (
      <div className="badgeclass-display badgeclass-display-thumbnail col-xs-3">
        <img src={this.props.image} alt={this.props.name} />
      </div>
    );
  }
});

BadgeClassDetail = React.createClass({
  render: function() {
    var properties = {
      image: {type: 'image', text: this.props.name + ' logo', href: this.props.image},
      name: {type: 'text', text: this.props.name},
      criteria: {type: 'link', href: this.props.json.criteria},
      description: {type: 'text', text: this.props.json.description}
    }

    return (
      <div className="badge-display badgeclass-display badgeclass-display-detail col-xs-12">
        <div className='property-group image col-xs-3'>
          <Property name="Badge Image" label={false} property={properties.image} />
        </div>
        <div className='property-group details col-xs-9'>
          <Property name="Name" property={properties.name} />
          <Property name="Criteria" label={false} property={properties.criteria} />
          <Property name="Description" label={false} property={properties.description} />
        </div>
      </div>
    );
  }
});

BadgeClassList = React.createClass({
  getDefaultProps: function() {
    return {
      display: 'thumbnail'
    };
  },
  render: function() {
    var badgeClasses = this.props.badgeClasses.slice(0,4).map(function(bc, i){
      var properties = {
        image: bc.image,
        name: bc.name,
        slug: bc.slug,
        key: "bc-" + i
      }

      if (this.props.display == 'thumbnail'){
        return (
          <BadgeClassThumbnail {...properties} />
        );
      }
      else {
        return (
          <BadgeClassDetail {...bc} key={'bc-' + i} />
        );
      }
    }.bind(this));
    return (
      <div className="container-fluid">
        <div className="badgeclass-list badgeclass-list-thumbnail row">
          {badgeClasses}
        </div>
      </div>
    );
  }

});


module.exports = {
  BadgeClassList: BadgeClassList
};