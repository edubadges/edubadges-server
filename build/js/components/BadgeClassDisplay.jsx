var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

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
  getDefaultProps: function() {
    return {
      handleClick: function(e){}
    };
  },
  render: function() {
    var properties = {
      image: {type: 'image', name: this.props.name + ' logo', id: this.props.image},
      name: {type: 'xsd:string', '@value': this.props.name},
      criteria: {type: 'id', id: this.props.json.criteria},
      description: {type: 'xsd:string', '@value': this.props.json.description}
    }

    return (
      <div 
        className="badge-display badgeclass-display badgeclass-display-detail col-xs-12"
        onClick={this.props.handleClick}
      >
        <div className='property-group image col-xs-3'>
          <Property name="Badge Image" label={false} property={properties.image} />
        </div>
        <div className='property-group details col-xs-9'>
          <Property name="Name" property={properties.name} />
          <Property name="Criteria" label={true} property={properties.criteria} />
          <Property name="Description" label={true} property={properties.description} />
        </div>
      </div>
    );
  }
});

BadgeClassList = React.createClass({
  getDefaultProps: function() {
    return {
      display: 'thumbnail',
      perPage: 4,
      currentPage: 1
    };
  },
  render: function() {
    var badgeClasses = this.props.badgeClasses.slice(
      this.props.perPage * (this.props.currentPage-1),
      this.props.perPage + this.props.perPage * (this.props.currentPage-1)
    ).map(function(bc, i){
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
        var badgeclassPath = "/issuer/issuers/" + this.props.issuerSlug + "/badges/" + bc.slug;
        var handleClick = function(e){navigateLocalPath(badgeclassPath);};
        var providedHandler = this.props.handleClick
        if (providedHandler) {
          handleClick = function(e) { providedHandler(e, bc); };
        }
        return (
          <BadgeClassDetail {...bc} key={'bc-' + i} handleClick={handleClick} />
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
  BadgeClassList: BadgeClassList,
  BadgeClassDetail: BadgeClassDetail
};