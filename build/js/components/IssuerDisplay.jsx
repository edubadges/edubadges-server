var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

// Stores
var APIStore = require('../stores/APIStore');

// Components
var Property = require('../components/BadgeDisplay.jsx').Property;
var BadgeClassList = require('./BadgeClassDisplay.jsx').BadgeClassList;


var IssuerDisplayShort = React.createClass({
  render: function() {
    originUrl = this.props.url.split('/')[2];
  
    var properties = {
      name: {type: 'text', text: this.props.name},
      image: {type: 'image', text: this.props.name + ' logo', href: this.props.image},
      name: {type: 'text', text: this.props.name},
      url: {type: 'link', href: this.props.url, text: originUrl}
    }

    return (
      <div className="issuer-display issuer-display-short col-xs-12" onClick={this.props.handleClick}>
        <div className='row'>
          <div className='property-group image col-xs-3'>
            <Property name="Issuer Logo" label={false} property={properties.image} />
          </div>
          <div className='property-group basic-data col-xs-9'>
            <Property name="Name" property={properties.name} />
            <Property name="URL" label={false} property={properties.url} />
            <BadgeClassList display="thumbnail" max={4} badgeClasses={this.props.badgeClasses} />
          </div>
        </div>
      </div>
    );
  }
});

var IssuerDisplay = React.createClass({
  getDefaultProps: function() {
    return {
      displayBadgeClasses: true
    };
  },
  render: function() {
    var originUrl = this.props.json.url.split('/')[2];
    var properties = {
      image: {type: 'image', text: this.props.name + ' logo', href: this.props.image},
      name: {type: 'text', text: this.props.name},
      url: {type: 'link', href: this.props.json.url, text: originUrl},
      description: {type: 'text', text: this.props.json.description}
    }
    return (
      <div className="issuer-display issuer-display-detail col-xs-12">
        <div className='property-group image col-xs-3'>
          <Property name="Issuer Logo" label={false} property={properties.image} />
        </div>
        <div className='property-group image col-xs-9'>
          <Property name="Name" property={properties.name} />
          <Property name="URL" label={false} property={properties.url} />
          <Property name="Description" label={false} property={properties.description} />
        </div>
      </div>
    );
  }
});

/* 
  Earner Badge List: A wrapper around OpenBadgeList that updates active badge
  within an activePanel through a passed in setter.
*/
var IssuerList = React.createClass({
  render: function() {
    var issuers, listClass;
    if (!this.props.issuers){
      issuers = "";
      listClass = 'issuer-list empty';
    }
    else {
      issuers = this.props.issuers.map(function(issuer, i){
        var issuerPath = "/issuer/issuers/" + issuer.slug;
        var badgeClasses = this.props.badgeclasses.filter(
          function(el,i,array){ return (el.issuer == issuer.json.id); }
        );
        var handleClick = function(e){navigateLocalPath(issuerPath);};
        return (
          <IssuerDisplayShort
            name={issuer.name}
            image={issuer.image}
            url={issuer.json.url}
            key={"issuer-" + i}
            handleClick={handleClick}
            badgeClasses={badgeClasses}
          />
        );
      }.bind(this));
    }
    return (
      <div className={listClass}>
        {issuers}
      </div>
    );
  }
});


module.exports = {
  IssuerList: IssuerList,
  IssuerDisplay: IssuerDisplay,
  IssuerDisplayShort: IssuerDisplayShort
};
