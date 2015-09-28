var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

// Stores
var APIStore = require('../stores/APIStore');

// Components
var Property = require('../components/BadgeDisplay.jsx').Property;
var BadgeClassList = require('./BadgeClassDisplay.jsx').BadgeClassList;
var Issuer = require('../components/Issuer.jsx').Issuer;


var IssuerDisplayShort = React.createClass({
  render: function() {
    originUrl = this.props.url.split('/')[2];
  
    var properties = {
      name: {type: 'xsd:string', '@value': this.props.name},
      image: {type: 'image', name: this.props.name + ' logo', id: this.props.image},
      url: {type: 'id', id: this.props.url, name: originUrl}
    }

    return (
      <div className="issuer-display issuer-display-short panel panel-default" onClick={this.props.handleClick}>
        <div className='panel-heading'>
          <div className='property-group image'>
            <Property name="Issuer Logo" label={false} property={properties.image} />
          </div>
          <div className='property-group basic-data'>
            <Property name="Name" property={properties.name} />
            <Property name="URL" label={false} property={properties.url} />
          </div>
        </div>
        <div className="panel-body">
            <div className="">
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
      image: {type: 'image', name: this.props.name + ' logo', id: this.props.image},
      name: {type: 'xsd:string', '@value': this.props.name},
      url: {type: 'id', id: this.props.json.url, name: originUrl},
      description: {type: 'xsd:string', '@value': this.props.json.description}
    }
    return (
      <div className="detail_">
        <div>
          <img src={properties.image.id} width="112" height="112" />
        </div>
        <ul>
          <li>
            <h2 className="detail_-x-meta">Name</h2>
            <p>{properties.name['@value']}</p>
          </li>
          <li>
            <h2 className="detail_-x-meta">URL</h2>
            <p><a href="{properties.url.id}">{properties.url.name || properties.url.id}</a></p>
          </li>
          <li>
            <h2 className="detail_-x-meta">Description</h2>
            <p>{properties.description['@value']}</p>
          </li>
        </ul>
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
        var providedHandler = this.props.handleClick;
        if (providedHandler) {
          handleClick = function(e){ providedHandler(e, issuer); };
        }
        return (
            <div key={"issuer-"+i}>
                <Issuer name={issuer.name}
                        image={issuer.image}
                        description={issuer.description}
                        badgeClasses={badgeClasses}
                        handleClick={handleClick}/>
            </div>);

        //return (
        //    <IssuerDisplayShort
        //      name={issuer.name}
        //      image={issuer.image}
        //      url={issuer.json.url}
        //      key={"issuer-" + i}
        //      handleClick={handleClick}
        //      badgeClasses={badgeClasses}
        //    />
        //);
      }.bind(this));
    }
    return (
      <div className="l-vertical l-wrapper l-wrapper-inset">
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
