var React = require('react');

var fakeSerializedBadge = {
  assertion: {
    issuedOn: {
      type: "text",
      text: "2015-1-1"
    },
    evidence: {
      type: "link",
      href: "http://example.org/such-evidence"
    }
  },
  badgeclass: {
    image: {
      type: "image",
      text: "Alt Text for Badge Image",
      href: "http://placehold.it/300x300"
    },
    name: {
      type: "text",
      text: "Badge of Awesome"
    },
    description: {
      type: "text",
      text: "This badge is issued to those who are awesome. That's the only criterion."
    },
    criteria: {
      type: "link",
      href: "http://example.org/so-criteria"
    },
    tags: {
      type: "text",
      text: "awesomeness, exceptionalness, superiority, queenliness"
    }
  }, 
  issuer: {
    type: "link",
    text: "Example Issuer",
    href: "http://example.org"
  }
}



var Property = React.createClass({
  /* props = {
    name: "Text",
    property: {
      type: "link",
      text "alt-text or link text",
      href: "image or link URL"
      }
    }
  }
  */
  getDefaultProps: function() {
    var props = {
      label: true,
      linksClickable: true
    };
  },
  renderPropertyName: function(propName){
    return ( 
      <span className={"propertyName " + propName}>{propName}</span>
    );
  },
  renderPropertyValue: function(property){
    var KNOWN_TYPES = {
      "text": this.renderStringValue,
      "link": this.renderLinkValue,
      "image": this.renderImageValue
    }
    // add non-clickable link handling on this.props.clickableLink=false


    return KNOWN_TYPES[property.type](property);
  },
  renderStringValue: function(property){
    return (
      <span className={"propertyValue " + this.props.name}>{property.text}</span>
    );
  },
  renderLinkValue: function(value){
    return (
        <a href={value.href}>{value.text || value.href }</a>
      );
  },
  renderImageValue: function(value){
    return (
      <img className="propertyImage" src={value.href} alt={value.text} />
    );
  },
  render: function(){
    return (
      <div className="badgeProperty">
        { this.props.label ? this.renderPropertyName(this.props.property.name) : null }
        { this.renderPropertyValue(this.props.property) }
      </div>
    );
  }
});


var Extension = React.createClass({
  render: function(){
    propertyOutput = this.props.properties.map(function(currentProp, i, array){
      return ( 
        <Property property={currentProp} />
      );
    });
    return (
      <div className="badgeExtension">
        {propertyOutput}
      </div>
    );
  }
});


var BadgeDisplayThumbnail = React.createClass({
  render: function() {
    return (
      <div className='badge-display badge-display-thumbnail'>
        <Property name='Badge Image' label={false} property={this.props.badgeclass.image} />
        <Property name='Name' label={false} property={this.props.badgeclass.name} />
        <Property name='Issuer' label={false} property={this.props.issuer} linksClickable={false}/>
      </div>
    );
  }
});


var BadgeDisplayDetail = React.createClass({
  render: function() {
    return (
      <div className='badge-display badge-display-detail'>
        <div className='property-group badgeclass'>
          <Property name='Badge Image' label={false} property={this.props.badgeclass.image} />
          <Property name='Name' property={this.props.badgeclass.name} />
          <Property name='Description' property={this.props.badgeclass.description} />
          <Property name='Criteria' property={this.props.badgeclass.criteria} />
        </div>

        <div className='property-group issuer'>
          <Property name='Issuer' property={this.props.issuer} />
        </div>

        <div className='property-group assertion'>
          <Property name='issue date' property={this.props.assertion.issuedOn} />
          <Property name='evidence link' property={this.props.assertion.evidence} />
        </div>
      </div>
    )
  }
});


var BadgeDisplayFull = React.createClass({
  render: function() {
    return (
      <div className='badge-display badge-display-full'>
        <div className='property-group badgeclass'>
          <Property name='Badge Image' label={false} property={this.props.badgeclass.image} />
          <Property name='Name' property={this.props.badgeclass.name} />
          <Property name='Description' property={this.props.badgeclass.description} />
          <Property name='Criteria' property={this.props.badgeclass.criteria} />
        </div>

        <div className='property-group issuer'>
          <Property name='Issuer' property={this.props.issuer} />
        </div>

        <div className='property-group assertion'>
          <Property name='issue date' property={this.props.assertion.issuedOn} />
          <Property name='evidence link' property={this.props.assertion.evidence} />
        </div>
      </div>
    )
  }
});


var OpenBadge = React.createClass({
  /* props = {
    display: "thumbnail" / "detail" / "full",
    badge = {}
  }
  */
  getDefaultProps: function() {
    return {
      display: 'thumbnail',
      badge: fakeSerializedBadge
    };
  },

  innerRender: function(){
    switch(this.props.display){
      case 'detail':
        return ( <BadgeDisplayDetail {...this.props.badge} /> );
        break;
      case 'thumbnail': 
        return ( <BadgeDisplayThumbnail {...this.props.badge } /> );
        break;
      default:  // 'full'
        return ( <BadgeDisplayFull {...this.props.badge } /> );
    }
  },

  render: function(){
    return this.innerRender();
  }
});

// Export the Menu class for rendering:
module.exports.OpenBadge = OpenBadge;
