var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

// Components
var Property = require('../components/BadgeDisplay.jsx').Property;

BadgeClassThumbnail = React.createClass({
  getDefaultProps: function() {
    return {
      handleClick: function(e){},
      showName: false
    };
  },
  render: function() {
    var name = "";
    if (this.props.showName) {
      name = (<p>{this.props.name}</p>);
    }
    return (
      <div
        className="badgeclass-display badge-display-thumbnail"
        onClick={this.props.handleClick}
      >
        <img src={this.props.image} alt={this.props.name} />
        {name}
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
      <div className="badge-display-full form-horizontal issuer-list xs-col-12" onClick={this.props.handleClick}>
        <div className='property-group image col-xs-2'>
          <Property name="Badge Image" label={false} property={properties.image} />
        </div>
        <div className="name-wrapper">
            <Property name="Name" property={properties.name} />
        </div>
        <div className="detail-wrapper">
            <div className="criteria-wrapper">
                <Property name="Criteria" label={true} property={properties.criteria} />
            </div>
            <div className="description-wrapper">
                <Property name="Description" label={true} property={properties.description} />
            </div>
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
      currentPage: 1,
      showNameOnThumbnail: false,
      emptyMessage: "There are no badges defined yet.",
      includeNullItem: false,
      handleNullClick: function(e) {},
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
        key: "bc-" + i,
        showName: this.props.showNameOnThumbnail
      }


      if (this.props.display == 'thumbnail'){
        var handleClick = function(e){};
        var providedHandler = this.props.handleClick
        if (providedHandler) {
          handleClick = function(e) { providedHandler(e, bc); };
        }
        return (
          <BadgeClassThumbnail {...properties} handleClick={handleClick} />
        );
      }
      else {
        var badgeclassPath = "/issuer/issuers/" + this.props.issuerSlug + "/badges/" + bc.slug;
        var handleClick = function(e){navigateLocalPath(badgeclassPath);};
        var providedHandler = this.props.handleClick;
        if (providedHandler) {
          handleClick = function(e) { providedHandler(e, bc); };
        }
        return (
          <BadgeClassDetail {...bc} key={'bc-' + i} handleClick={handleClick} />
        );
      }
    }.bind(this));
    if (badgeClasses.length < 1) {
      badgeClasses = this.props.emptyMessage;
    } else if (this.props.includeNullItem) {
      badgeClasses.push(<div key={"nullItem"}
                          className="badgeclass-display badgeclass-display-none col-xs-3"
                          onClick={this.props.handleNullClick}
                          >
                          <img src="/static/images/none.png" alt="No Badge" />
                          <p>No Badge</p>
                        </div>);
    }
    return (
      <div className="container-fluid">
        <div className="open-badge-list">
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