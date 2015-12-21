var React = require('react');
var _ =  require('lodash');

// Components
var Button = require('../components/Button.jsx').Button;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Heading = require('../components/Heading.jsx').Heading;
var More = require('../components/Title.jsx').More;
var SubmitButton = require('../components/Button.jsx').SubmitButton;

// Stores
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');
var FormConfigStore = require('../stores/FormConfigStore');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;
var APISubmitData = require('../actions/api').APISubmitData;


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
      <h2 className="detail_-x-meta">{propName}</h2>
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
          var propertyValue = this.renderPropertyValue(this.props.property);
          var propertyLabel = this.props.label ? this.renderPropertyName(this.props.name) : undefined;

          if (propertyLabel) {
              return (
                <span className="x-owner">
                    { propertyLabel }
                    { propertyValue }
                </span>
            );
          }
          else {
              return (propertyValue);
          }
      }
      else {
          return (<span className="missingProperty badgeProperty"></span>);
      }
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
      selected: false,
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

    componentDidMount: function() {
        var badgeId = this.props.id;
        FormStore.addListener('FORM_DATA_UPDATED_EarnerCollectionCreateForm-' + badgeId, this.handleNewCollection);
        APIStore.addListener('DATA_UPDATED_earner_collections', this.handleAddedToNewCollection);
    },
    componentWillUnmount: function() {
        var badgeId = this.props.id;
        FormStore.removeListener('FORM_DATA_UPDATED_EarnerCollectionCreateForm-' + badgeId, this.handleNewCollection);
        APIStore.removeListener('DATA_UPDATED_earner_collections', this.handleAddedToNewCollection);
    },
    handleNewCollection: function(ev) {
        var badgeId = this.props.id;
        var formId = 'EarnerCollectionCreateForm-'+ badgeId;
        var newState = FormStore.getFormState(formId);
        if (newState.actionState === "complete") {
            // Add the Badge to the new Collection
            var newestCollection = APIStore.getCollectionLastItem('earner_collections')

            apiContext = {
                formId: formId,
                apiCollectionKey: "earner_collections",
                apiSearchKey: 'slug',
                apiSearchValue: newestCollection.slug,
                apiUpdateFieldWithResponse: 'badges',
                pushResponseToField: true,

                actionUrl: "/v1/earner/collections/"+ newestCollection.slug +"/badges",
                method: "POST",
                successHttpStatus: [200, 201],
                successMessage: "New collection created"
            };

            // Somehow we're still within a dispatcher here, so defer the execution
            setTimeout(function() { APISubmitData({id: badgeId}, apiContext) }, 0);
        }
    },
    handleAddedToNewCollection: function(ev) {
        var badgeId = this.props.id;
        var selectCollectionDialog = document.getElementById('select-collection-'+ badgeId);
        if (selectCollectionDialog && selectCollectionDialog.hasAttribute('open')) {
            selectCollectionDialog.close();
        }
        this.refs.selectDialog.dialog.update();
    },
    
  render: function() {
    var badgeName = this.props.json.badge.name['@value'];
    var badgeId = this.props.id;

    // New Collection Dialog
    var createCollectionFormType = "EarnerCollectionCreateForm";
    var createCollectionFormId = createCollectionFormType +"-"+ badgeId;
    var createCollectionFormProps = FormConfigStore.getConfig(createCollectionFormType, { formId: createCollectionFormId }, {});
    FormStore.getOrInitFormData(createCollectionFormId, createCollectionFormProps);

    var createCollectionActions=[
        <SubmitButton formType={createCollectionFormType} formId={createCollectionFormId} label="Add Collection" />
    ];
    var addToNewCollectionDialog = (
        <Dialog formId={createCollectionFormId} dialogId={"add-collection-"+ badgeId} key={"add-collection-"+ badgeId} actions={createCollectionActions} className="closable">
            <Heading size="small"
                     title="New Collection"
                     subtitle={badgeName +" will automatically be added to this collection."}/>

            <BasicAPIForm hideFormControls={true} actionState="ready" {...createCollectionFormProps} />
        </Dialog>);

    // Select Collection Dialog
    var collections = APIStore.getCollection("earner_collections").map(function(object) { return {name: object.name, slug:object.slug} });

    var selectCollectionFormType = "CollectionAddBadgeInstanceForm";
    var selectCollectionFormId = selectCollectionFormType +"-"+ badgeId;
    var selectCollectionFormProps = FormConfigStore.getConfig(selectCollectionFormType, { formId: selectCollectionFormId }, {
        badgeId: badgeId,
        collections: collections,
        defaultCollection: _.get(collections, "[0].slug", ''),
        badgeName: badgeName,
    });
    FormStore.initFormData(selectCollectionFormId, selectCollectionFormProps)

    var selectCollectionActions=[
        <SubmitButton formType={selectCollectionFormType} formId={selectCollectionFormId} label="Add" />
    ];
    var selectCollectionDialog = (
        <Dialog formId={selectCollectionFormId} dialogId={"select-collection-"+ badgeId} key={"select-collection-"+ badgeId} actions={selectCollectionActions} className="closable">
            <Heading size="small" title="Add to Collection" />

            <BasicAPIForm hideFormControls={true} actionState="ready" {...selectCollectionFormProps} />

            <DialogOpener className="l-vertical" dialog={addToNewCollectionDialog} dialogId={"add-collection-"+ badgeId} key={"add-collection-"+ badgeId}>
                <Button className="action_" label="CREATE NEW COLLECTION" propagateClick={true}/>
                <p>{badgeName +" will automatically be added to the new collection."}</p>
            </DialogOpener>
        </Dialog>);

    if (this.refs.selectDialog) {
        // Presumably the this.reactComponent created initially has a stale reference
        // to the old selectCollectionFormProps (without the new additional
        // fieldsMeta.collection.selectOptions) so re-rendering it does nothing new.
        // Here, as a work-around we pass it an entirely new reactComponent instead.
        this.refs.selectDialog.dialog.reactComponent = selectCollectionDialog;
        // this.refs.selectDialog.dialog.update();
    }

    var style = {};
    if (this.props.selected) {
        style = {border: '2px solid  #31383E'};
    }

    var hoverText = this.props.hoverText;

    return (
      <div className="card_" style={style}>
        <div className="badge_ viewdetails_" onClick={this.handleClick}>
            <Property name='Badge Image' label={false} property={this.props.json.image} width="128" height="128" />
            <div className="viewdetails_-x-details">
                <button className="button_ button_-solid button_-uppercase">{hoverText || "View Details"}</button>
            </div>
        </div>
        <div className="title_">
            <div>
                <h1 className="title_-x-primary truncate_"><Property name='Name' property={this.props.json.badge.name} /></h1>
                <p className="title_-x-secondary truncate_"><Property name='Issuer' property={this.props.json.badge.issuer.name} /></p>
            </div>
            <More>
                <div className="dropdown_">
                    <DialogOpener ref="selectDialog" dialog={selectCollectionDialog} dialogId={"select-collection-"+ badgeId} key={"select-collection-"+ badgeId}>
                        <button className="dropdown_-x-item"><span className="icon_ icon_-add">Add to Collection</span></button>
                    </DialogOpener>
                </div>
            </More>
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
      <div className="detail_" onClick={this.handleClick}>
          <div>
              <Property name='Badge Image' label={false} property={this.props.json.image} width="224" height="224" />
          </div>
  
          <ul>
              <li>
                <Property label={true} name='Criteria' property={this.props.json.badge.criteria} />
              </li>
              <li>
                <Property label={true} name='Issuer' property={this.props.json.badge.issuer.name} />
              </li>
              <li>
                <Property label={true} name='Issuer Website' property={this.props.json.badge.issuer.url} />
              </li>
              <li>
                <Property label={true} name='Issue Date' property={this.props.json.issuedOn} />
              </li>
              <li>
                <Property label={true} name='Expiration Date' property={this.props.json.expires} />
              </li>
              <li>
                <Property label={true} name='Evidence Link' property={this.props.json.evidence} />
              </li>
              <li>
                <Property label={true} name='Recipient' property={wrap_text_property(this.props.recipientId)} />
              </li>
          </ul>

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
        <Property name='Badge Image' label={false} property={this.props.json.image} width="72" height="72" className="collection_-x-item" />
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

