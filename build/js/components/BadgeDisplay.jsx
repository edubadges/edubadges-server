var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;


var wrap_text_property = function(value){
  return {
    'type': 'xsd:string',
    '@value': value
  }
}

var Property = React.createClass({
  REQUIRED_VALUES_FOR_TYPE: {
    "xsd:string": ["@value"],
    "id": ["id"],
    "image": ["id"],
    "email": ["@value"]
  },
  getDefaultProps: function() {
    return {
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
      "xsd:string": this.renderStringValue,
      "id": this.renderLinkValue,
      "image": this.renderImageValue,
      "email": this.renderEmailValue
    };
    return KNOWN_TYPES[property.type](property);
  },
  renderStringValue: function(property){
    return (
      <span className={"propertyValue " + this.props.name}>{property['@value']}</span>
    );
  },
  renderLinkValue: function(value){
    // TODO: preventDefault() on thumbnail view
    //if (!this.props.linksClickable)

    return (
        <span className={"propertyValue " + this.props.name}>
          <a href={value.id} >{value.name || value.id }</a>
        </span>
      );
  },
  renderEmailValue: function(value){
    // TODO: preventDefault() on thumbnail view
    //if (!this.props.linksClickable)

    return (
        <span className={"propertyValue " + this.props.name}>
          <a href={"mailto:" + value['@value']} >{value['@value']}</a>
        </span>
      );
  },
  renderImageValue: function(value){
    return (
      <img className="propertyImage" src={value.id} alt={value.name || this.props.name} />
    );
  },
  hasRequiredValues: function(){
    var errorExists = false;
    var necessaryProps = this.REQUIRED_VALUES_FOR_TYPE[this.props.property.type];
    for (var i=0; i < necessaryProps.length; i++){
      if (!this.props.property.hasOwnProperty(necessaryProps[i]) || !this.props.property[necessaryProps[i]])
        errorExists = true;
    }
    return !errorExists;
  },
  canIRender: function(){
    return (
      this.props.property &&
      this.props.name && this.props.property.type &&
      this.REQUIRED_VALUES_FOR_TYPE.hasOwnProperty(this.props.property.type) &&
      this.hasRequiredValues()
    )
  },
  render: function(){
    if (this.canIRender()){
      return (
        <div className={"badgeProperty badgeProperty-type-" + this.props.property.type}>
          { this.props.label ? this.renderPropertyName(this.props.name) : null }
          { this.renderPropertyValue(this.props.property) }
        </div>
      );
    }
    else
      return (<span className="missingProperty badgeProperty"></span>);
  }
});

var BadgeValidationResult = React.createClass({
  render: function() {
    var message_types = {success: "success", error: "danger", warning: "warning"}
    return (
      <div className={"badge-validation-result alert alert-" + message_types[this.props.result]}>
        <div className="validator-name"><strong>{this.props.validator}</strong></div>
        <div className="validator-message">{this.props.message}</div>
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
  getDefaultProps: function() {
    return {
      json: {badge: {issuer:{}}}
    };
  },
  handleClick: function(){
    if (this.props.clickable)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
  },
  render: function() {
    var className = 'badge-display badge-display-thumbnail col-xs-3 col-md-2 col-lg-2';
    return (
      <div className={className} onClick={this.handleClick} >
        <Property name='Badge Image' label={false} property={this.props.json.image} />
        <Property name='Name' property={this.props.json.badge.name} />
        <Property name='Issuer' property={this.props.json.badge.issuer.name} />
      </div>
    );
  }
});


var BadgeDisplayDetail = React.createClass({
  handleClick: function(){
    if (this.props.clickable)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
  },
  render: function() {
    return (
      <div className='badge-display badge-display-detail col-xs-12' onClick={this.handleClick} >
        <div className='row'>

          <div className='property-group image col-xs-4'>
            <Property name='Badge Image' label={false} property={this.props.json.image} />
          </div>

          <div className='col-xs-8'>
            <div className='property-group badgeclass'>
              <Property name='Name' property={this.props.json.badge.name} />
              <Property name='Description' property={this.props.json.badge.description} />
              <Property name='Criteria' property={this.props.json.badge.criteria} />
            </div>

            <div className='property-group issuer'>
              <Property name='Issuer' property={this.props.json.badge.issuer.name} />
              <Property name='Website' label={false} property={this.props.json.badge.issuer.url} />
            </div>

            <div className='property-group assertion'>
              <Property name='Issue Date' property={this.props.json.issuedOn} />
              <Property name='Expiration Date' property={this.props.json.expires} />
              <Property name='Evidence Link' property={this.props.json.evidence} />
              <Property name='Recipient' property={wrap_text_property(this.props.recipientId)} />
            </div>
          </div>

        </div>
      </div>
    )
  }
});


var BadgeDisplayFull = React.createClass({
  handleClick: function(){
    if (this.props.clickable)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
  },
  render: function() {
    var errors = this.props.errors.map(function(validation, index){
      return (
        <BadgeValidationResult
          key={"valresult-" + index}
          validator={validation.validator}
          result={validation.result}
          message={validation.message}
          data={validation.data}
        />
      );
    });

    return (
      <div className='badge-display badge-display-full' onClick={this.handleClick}>
        <div className='property-group image col-xs-4'>
          <Property name='Badge Image' label={false} property={this.props.json.image} />
        </div>

        <div className='property-group badgeclass'>
          <Property name='Name' property={this.props.json.badge.name} />
          <Property name='Description' property={this.props.json.badge.description} />
          <Property name='Criteria' property={this.props.json.badge.criteria} />
        </div>

        <div className='property-group issuer'>
          <Property name='Issuer' property={this.props.json.badge.issuer.name} />
          <Property name='Website' label={false} property={this.props.json.badge.issuer.url} />
        </div>

        <div className='property-group assertion'>
          <Property name='Issue Date' property={this.props.json.issuedOn} />
          <Property name='Expiration Date' property={this.props.json.expires} />
          <Property name='Evidence Link' property={this.props.json.evidence} />
          <Property name='Recipient' property={wrap_text_property(this.props.recipientId)} />
        </div>

        <div className='property-group validations'>
          {validations}
        </div>
      </div>
    )
  }
});


var OpenBadge = React.createClass({
  proptypes: {
    id: React.PropTypes.number.isRequired,
    display: React.PropTypes.string,
    json: React.PropTypes.object.isRequired,
    errors: React.PropTypes.array,
    recipientId: React.PropTypes.string,
    clickable: React.PropTypes.bool,
    targetUrl: React.PropTypes.string
  },
  getDefaultProps: function() {
    return {
      display: 'thumbnail',
      errors: [],
      clickable: true
    };
  },

  render: function(){
    switch(this.props.display){
      case 'detail':
        return ( <BadgeDisplayDetail {...this.props} /> );
        break;
      case 'thumbnail': 
        return ( <BadgeDisplayThumbnail {...this.props} /> );
        break;
      default:  // 'full'
        return ( <BadgeDisplayFull {...this.props} /> );
    }
  }
});


// Export the Menu class for rendering:
module.exports.OpenBadge = OpenBadge;
module.exports.Property = Property;

