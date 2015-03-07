var React = require('react');

var Property = React.createClass({
  /* props = {
    name: "Text",
    label: true,
    property: {
      type: "link",
      text "alt-text or link text",
      href: "image or link URL"
      }
    }
  }
  */
  REQUIRED_VALUES_FOR_TYPE: {
    "text": ["text"],
    "link": ["href"],
    "image": ["text", "href"]
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
      "text": this.renderStringValue,
      "link": this.renderLinkValue,
      "image": this.renderImageValue,
    };
    return KNOWN_TYPES[property.type](property);
  },
  renderStringValue: function(property){
    return (
      <span className={"propertyValue " + this.props.name}>{property.text}</span>
    );
  },
  renderLinkValue: function(value){
    // TODO: preventDefault() on thumbnail view
    //if (!this.props.linksClickable)

    return (
        <span className={"propertyValue " + this.props.name}>
          <a href={value.href} >{value.text || value.href }</a>
        </span>
      );
  },
  renderImageValue: function(value){
    return (
      <img className="propertyImage" src={value.href} alt={value.text} />
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
  handleClick: function(){
    this.props.setActiveBadgeId(this.props.id);
  },
  render: function() {
    var className = 'badge-display badge-display-thumbnail col-xs-3 col-md-2 col-lg-2';
    if (this.props.isActive)
      className += ' badge-display-active';
    return (
      <div className={className} onClick={this.handleClick} >
        <Property name='Badge Image' label={false} property={this.props.image} />
        <Property name='Name' label={false} property={this.props.badgeclass.name} />
        <Property name='Issuer' label={false} property={this.props.issuerorg} linksClickable={false}/>
      </div>
    );
  }
});


var BadgeDisplayDetail = React.createClass({
  render: function() {
    return (
      <div className='badge-display badge-display-detail col-xs-12'>
        <div className='row'>

          <div className='property-group image col-xs-4'>
            <Property name='Badge Image' label={false} property={this.props.image} />
          </div>

          <div className='col-xs-8'>
            <div className='property-group badgeclass'>
              <Property name='Name' property={this.props.badgeclass.name} />
              <Property name='Description' property={this.props.badgeclass.description} />
              <Property name='Criteria' property={this.props.badgeclass.criteria} />
            </div>

            <div className='property-group issuer'>
              <Property name='Issuer' property={this.props.issuerorg} />
            </div>

            <div className='property-group assertion'>
              <Property name='Issue Date' property={this.props.assertion.issuedOn} />
              <Property name='Expiration Date' property={this.props.assertion.expires} />
              <Property name='Evidence Link' property={this.props.assertion.evidence} />
              <Property name='Recipient' property={this.props.recipientId} />
            </div>
          </div>

        </div>
      </div>
    )
  }
});


var BadgeDisplayFull = React.createClass({
  render: function() {
    var validations = this.props.validations.map(function(validation, index){
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
      <div className='badge-display badge-display-full'>
        <div className='property-group image col-xs-4'>
          <Property name='Badge Image' label={false} property={this.props.image} />
        </div>

        <div className='property-group badgeclass'>
          <Property name='Name' property={this.props.badgeclass.name} />
          <Property name='Description' property={this.props.badgeclass.description} />
          <Property name='Criteria' property={this.props.badgeclass.criteria} />
        </div>

        <div className='property-group issuer'>
          <Property name='Issuer' property={this.props.issuerorg} />
        </div>

        <div className='property-group assertion'>
          <Property name='Issue Date' property={this.props.assertion.issuedOn} />
          <Property name='Expiration Date' property={this.props.assertion.expires} />
          <Property name='Evidence Link' property={this.props.assertion.evidence} />
          <Property name='Recipient' property={this.props.recipientId} />
        </div>

        <div className='property-group validations'>
          {validations}
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
      display: 'thumbnail'
    };
  },

  innerRender: function(){
    switch(this.props.display){
      case 'detail':
        return ( <BadgeDisplayDetail image={this.props.image} pk={this.props.pk} {...this.props.badge } recipientId={this.props.recipientId} /> );
        break;
      case 'thumbnail': 
        return ( <BadgeDisplayThumbnail image={this.props.image} id={this.props.id} pk={this.props.pk} isActive={this.props.isActive} setActiveBadgeId={this.props.setActiveBadgeId} {...this.props.badge } /> );
        break;
      default:  // 'full'
        return ( <BadgeDisplayFull image={this.props.image} pk={this.props.pk} {...this.props.badge } validations={this.props.validations} recipientId={this.props.recipientId} /> );
    }
  },

  render: function(){
    return this.innerRender();
  }
});

var EarnerBadge = React.createClass({
  render: function() {
    var earnerProperty = {
      type: "text",
      text: this.props.earner
    };

    var validations = null;
    if(typeof this.props.badge.errors !== 'undefined' && typeof this.props.badge.notes !== 'undefined')
      validations = this.props.badge.notes.concat(this.props.badge.errors); 
    
    return (
      <div className="earner-badge-display">
        <OpenBadge
          display={this.props.display}
          id={this.props.id}
          badge={this.props.badge.full_badge_object}
          validations={validations}
          image={this.props.badge.image}
          isActive={this.props.isActive}
          setActiveBadgeId={this.props.setActiveBadgeId}
          recipientId={earnerProperty}
        />
      </div>
    );
  }
});

// Export the Menu class for rendering:
module.exports.OpenBadge = OpenBadge;
module.exports.EarnerBadge = EarnerBadge;
