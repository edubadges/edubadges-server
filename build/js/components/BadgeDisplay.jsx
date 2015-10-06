var React = require('react');
var _ =  require('lodash');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;


var wrap_text_property = function(value){
  return {
    'type': 'xsd:string',
    '@value': value
  };
};

var Property = React.createClass({
  REQUIRED_VALUES_FOR_TYPE: {
    "xsd:string": ["@value"],
    "@id": ["id"],
    "id": ["id"],
    "image": ["id"],
    "email": ["@value"]
  },
  getDefaultProps: function() {
    return {
      label: false,
      linksClickable: true
    };
  },
  renderPropertyName: function(propName){
    return ( 
      <span>{propName}</span>
    );
  },
  renderPropertyValue: function(property){
    var KNOWN_TYPES = {
      "xsd:string": this.renderStringValue,
      "id": this.renderLinkValue,
      "@id": this.renderLinkValue,
      "image": this.renderImageValue,
      "email": this.renderEmailValue
    };
    var props = _.omit(this.props, ['name', 'label', 'property']);
    return KNOWN_TYPES[property.type](property, props);
  },
  renderStringValue: function(property, props){
    return (
      <span {...props}>{property['@value']}</span>
    );
  },
  renderLinkValue: function(value, props){
    // TODO: preventDefault() on thumbnail view
    //if (!this.props.linksClickable)

    return (
        <a href={value.id} {...props}>{value.name || value.id }</a>
      );
  },
  renderEmailValue: function(value, props){
    // TODO: preventDefault() on thumbnail view
    //if (!this.props.linksClickable)

    return (
        <a href={"mailto:" + value['@value']} {...props}>{value['@value']}</a>
      );
  },
  renderImageValue: function(value, props){
    return (
      <img src={value.id} alt={value.name || this.props.name} {...props} />
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
    if (this.canIRender()) {
      return (
        <span className="x-owner">
          { this.props.label ? this.renderPropertyName(this.props.name) : null }
          { this.renderPropertyValue(this.props.property) }
        </span>
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
      json: {badge: {issuer:{}}},
      columnClass: 'col-xs-3',
      selected: false
    };
  },
  handleClick: function(){
    if (this.props.clickable && !this.props.handleClick)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
    else if (this.props.handleClick)
      this.props.handleClick(this.props.id);
  },
  render: function() {
    return (
      <div className="card_">
        <div className="badge_ viewdetails_" onClick={this.handleClick}>
            <Property name='Badge Image' label={false} property={this.props.json.image} width="128" height="128" />
            <div className="viewdetails_-x-details">
                <button className="button_ button_-solid button_-uppercase">View Details</button>
            </div>
        </div>
        <div className="title_">
            <div>
                <h1 className="title_-x-primary truncate_"><Property name='Name' property={this.props.json.badge.name} /></h1>
                <p className="title_-x-secondary truncate_"><Property name='Issuer' property={this.props.json.badge.issuer.name} /></p>
            </div>
        </div>
      </div>
    );
  }
});


var BadgeDisplayDetail = React.createClass({
  getDefaultProps: function() {
    return {
      columnClass: 'col-xs-12', 
      selected: false
    };
  },
  handleClick: function(){
    if (this.props.clickable && !this.props.handleClick)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
    else if (this.props.handleClick)
      this.props.handleClick(this.props.id);
  },
  wrapperClass: function(){
    return this.props.columnClass + ' badge-display badge-display-detail selected-' + this.props.selected;
  },
  render: function() {
    return (
      <div className={this.wrapperClass()} onClick={this.handleClick} >
        <div className='row'>

          <div className='property-group image'>
            <Property name='Badge Image' label={false} property={this.props.json.image} />
          </div>

          <div className=''>
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
    if (this.props.clickable && !this.props.handleClick)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
    else if (this.props.handleClick)
      this.props.handleClick(this.props.id);
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
      <div className='badge-display-full form-horizontal' onClick={this.handleClick}>
        <div className='property-group image col-xs-2'>
          <Property name='Badge Image' label={false} property={this.props.json.image} />
        </div>

        <div className='property-group badgeclass'>
          <Property name='Name' property={this.props.json.badge.name} />
          <Property name='Description' property={this.props.json.badge.description} />
          <Property name='Criteria' property={this.props.json.badge.criteria} />
        </div>

        <div className='property-group issuer'>
          <Property name='Issuer' property={this.props.json.badge.issuer.name} />
          <Property name='Issuer Website' property={this.props.json.badge.issuer.url} />
        </div>

        <div className='property-group assertion'>
          <Property name='Issue Date' property={this.props.json.issuedOn} />
          <Property name='Expiration Date' property={this.props.json.expires} />
          <Property name='Evidence Link' property={this.props.json.evidence} />
          <Property name='Recipient' property={wrap_text_property(this.props.recipientId)} />
        </div>

        <div className='property-group validations'>
          {errors}
        </div>
      </div>
    )
  }
});


var BadgeDisplayImage = React.createClass({
  getDefaultProps: function() {
    return {
      columnClass: "col-xs-3",
      selected: false
    };
  },
  handleClick: function(){
    if (this.props.clickable && !this.props.handleClick)
      navigateLocalPath(
        this.props.targetUrl || '/earner/badges/' + this.props.id
      );
    else if (this.props.handleClick)
      this.props.handleClick(this.props.id);
  },
  wrapperClass: function(){
    return this.props.columnClass + ' more-link-fake-badge badge-display-image selected-' + this.props.selected;
  },
  render: function() {
    if (this.props.type == 'more-link'){
      return (
        <div className={this.wrapperClass()} onClick={this.handleClick}>
          <span className="more-link-text">{this.props.json.badge.name['@value']}</span>
        </div>
      );
    }
    return (
      <div className={'badge-display-image ' + this.props.columnClass} onClick={this.handleClick}>
        <Property name='Badge Image' label={false} property={this.props.json.image} />
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
    handleClick: React.PropTypes.func,
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
      case 'image only': 
        return ( <BadgeDisplayImage {...this.props} /> );
        break;
      default:  // 'full'
        return ( <BadgeDisplayFull {...this.props} /> );
    }
  }
});


var EmptyOpenBadge = React.createClass({
  render: function() {
    var fakeBadgeJSON = {
      "id": ":_0",
      "type": "Assertion",
      "badge": {
        "id": ":_1",
        "type": "BadgeClass",
        "name": {
          "type": "xsd:string",
          "@value": "No badges yet"
        },
        "description": {
          "type": "xsd:string",
          "@value": "You have no badges uploaded yet. Click to add a new badge."
        },
        "issuer": {
          "name": ""
        }
      },
      "image": {
        "type": "image",
        "id": "https://placeholdit.imgix.net/~text?txtsize=19&txt=Upload%20your%20Badges&w=200&h=200"
      }
    };

    return (
      <div className="emptyBadge" onClick={this.props.clickEmptyBadge}>
        <OpenBadge 
          id={-1}
          json={fakeBadgeJSON}
          display={this.props.display || 'thumbnail'}
          errors={[]}
          clickable={false}
        />
      </div>
    );
  }
});


// Export the Menu class for rendering:
module.exports.OpenBadge = OpenBadge;
module.exports.EmptyOpenBadge = EmptyOpenBadge;
module.exports.Property = Property;

