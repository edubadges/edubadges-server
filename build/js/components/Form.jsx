var React = require('react');
var ReactPropTypes = React.PropTypes;
var _ = require('lodash');

// Stores
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');

// Components
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var Dropzone = require('react-dropzone');
var LoadingIcon = require('../components/Widgets.jsx').LoadingIcon;

// Actions
var EarnerActions = require('../actions/earner');
var FormActions = require('../actions/forms');



/* Form components */
var InputGroup = React.createClass({
  propTypes: {
    name: ReactPropTypes.string,
    label: ReactPropTypes.string,
    inputType: ReactPropTypes.string,
    selectOptions: ReactPropTypes.arrayOf(ReactPropTypes.string),
    handleChange: ReactPropTypes.func,
    placeholder: ReactPropTypes.string
  },
  classNameForInput: function(){
    var classes = {
      "filebutton": "input-file",
      "textarea": "input-textarea form-control", //wrong. double-check. http://getbootstrap.com/components/#input-groups says you can't use textarea in .input-group
      "select": "input-group-select",
      "text": "form-control",
      "checkbox": "input-checkbox"
    };
    return classes[this.props.inputType];
  },
  theInput: function(){
    if (this.props.inputType == "filebutton"){
      // TODO: Add accept='image/*' ??
      return ( <input name={this.props.name} value={this.props.value} className={this.classNameForInput()} type="file" onChange={this.props.handleChange} /> );
    }
    else if (this.props.inputType == "text"){
      return ( <input name={this.props.name} value={this.props.value} className={this.classNameForInput()} type="text" onChange={this.props.handleChange} onBlur={this.props.handleBlur} /> );
    }
    else if (this.props.inputType == "textarea"){
      return ( <textarea name={this.props.name} value={this.props.value} className={this.classNameForInput()} onChange={this.props.handleChange} onBlur={this.props.handleBlur} /> );
    }
    else if (this.props.inputType == "checkbox"){
      return ( <input type="checkbox" name={this.props.name} checked={this.props.value} className={this.classNameForInput()} onChange={this.props.handleChange} /> );
    }
    else if (this.props.inputType == "select") {
      var selectOptions = this.props.selectOptions.map(function(option, index){
        return ( <option value={option} key={this.props.name + '-' + index}>{option}</option>);
      }.bind(this));
      return ( 
        <select name={this.props.name} value={this.props.value} className="input-xlarge" onChange={this.props.handleChange} onBlur={this.props.handleBlur} >
          { selectOptions }
        </select>
      );
    }
  },
  render: function(){
    return (
      <div className={"control-group form-group-" + this.props.name}>
        <label className="control-label" htmlFor={this.props.name}>{this.props.label}</label>
        <div className="controls">
          { this.theInput() }
        </div>
      </div>
    )
  }
});

/* A droppable zone for image files. Must send in handler(file) for when images are dropped and set image prop with that file from above. */
var ImageDropbox = React.createClass({
  validateFileType: function(file){
    if (file instanceof File && (file.type && (file.type == 'image/png' || file.type == 'image/svg+xml')))
      return true;
  },
  fileHandler: function(files){
    file = files[0];
    if (this.validateFileType(file)){
      this.props.onDroppedImage(file);
    }
  },
  render: function() {
    var imageDisplay = this.props.imageData ? (<img src={this.props.imageData} />) : (<div className="dropzone-empty"><i className="fa fa-arrow-down"></i>Drop {this.props.imageDescription || "Badge"} Here<br/><small>or Click to Select</small></div>);
    var dropzoneStyle = {};
    return (
      <div className="control-group form-group-dropzone">
        <label className="control-label" htmlFor={this.props.name}>{this.props.label}</label>
        <div className={ "controls"}>
          <Dropzone onDrop={this.fileHandler} style={dropzoneStyle}>
            {imageDisplay}
          </Dropzone>
        </div>
      </div>
    );
  }
});


var SubmitButton = React.createClass({
  handleClick: function(e){
    if (!this.props.isDisabled)
      this.props.handleClick(e);
    e.preventDefault();
    e.stopPropagation();
  },
  render: function() {
    return (
      <div className="control-group submit-button">
        <label className="control-label sr-only" htmlFor={this.props.name}>{ this.props.label || "Submit" }</label>
        <div className="controls">
          <button name={this.props.name} className="btn btn-primary" onClick={this.handleClick}>{this.props.label || "Submit" }</button>
        </div>
      </div>
    );
  }
});

var ResetButton = React.createClass({
  render: function() {
    return (
      <div className="control-group reset-button">
        <label className="control-label sr-only" htmlFor={this.props.name}>{ this.props.label || "Reset" }</label>
        <div className="controls">
          <button name={this.props.name} className="btn btn-danger" onClick={this.props.handleClick}>{this.props.label || "Reset" }</button>
        </div>
      </div>
    );
  }
});

var PlainButton = React.createClass({
  render: function() {
    return (
      <div className="control-group button">
        <label className="control-label sr-only" htmlFor={this.props.name}>{this.props.label}</label>
        <div className="controls">
          <button name={this.props.name} className="btn btn-default" onClick={this.props.handleClick}>{this.props.label}</button>
        </div>
      </div>
    );
  }
});






BasicAPIForm = React.createClass({
  getInitialState: function() {
    return FormStore.getFormState(this.props.formId);
  },
  componentDidMount: function() {
    FormStore.addListener('FORM_DATA_UPDATED_' + this.props.formId, this.handlePatch);
    if (this.props.submitImmediately)
      this.handleSubmit();
  },
  componentWillUnmount: function() {
    FormStore.removeListener('FORM_DATA_UPDATED_' + this.props.formId, this.handlePatch);
  },
  handleChange: function(event){
    //reject change unless form is ready
    if (this.isMounted() && this.state.actionState != "ready"){
      event.stopPropagation();
      event.preventDefault();
      return;
    }
    var change = {};

    // Update Store immediately for checkbox fields
    if (this.props.fieldsMeta[event.target.name].inputType == 'checkbox') {
      change[event.target.name] = (!_.get(this.state, event.target.name)) ? "on": false;
      FormActions.patchForm(this.props.formId, change);

      return;
    }

    change[event.target.name] = event.target.value;
    this.setState(change);
  },
  // When an input field is blurred, a form patch is submitted if its value has changed.
  // Does not apply to the image upload field
  handleBlur: function(event){
    var patch = {}
    var field = event.target.name;
    var currentValue = FormStore.getFieldValue(this.props.formId, field);
    if (currentValue !== event.target.value){
      patch[field] = event.target.value;
      FormActions.patchForm(this.props.formId, patch);
    }
  },
  // This catches the result from form update and applies it to the formstate. 
  // On submit, it is how the result gets displayed.
  handlePatch: function(){
    // this is bound...
    if (this.isMounted()){
      var newState = FormStore.getFormState(this.props.formId);
      this.setState(newState);
    }
  },
  handleSubmit: function(e){
    if (typeof e !== 'undefined'){
      e.preventDefault(); 
      e.stopPropagation();
    }
    
    if (this.state.actionState != "waiting")
      FormActions.submitForm(this.props.formId, this.props.formType);
  },
  handleReset: function(e){
    e.preventDefault();
    e.stopPropagation();

    FormActions.resetForm(this.props.formId);
    if (this.props.handleCloseForm){
      this.props.handleCloseForm();
    }
  },
  handleImageDrop: function(file){
    // To make sure any changes within the focused element are recorded in the form state
    document.activeElement.blur();

    var reader = new FileReader();
    reader.onload = function(e) {
      if (this.isMounted()){
        FormActions.patchForm(this.props.formId, { image: file, imageData: reader.result });
      }
    }.bind(this);
    reader.readAsDataURL(file);

  },
  render: function() {
    var messageText = _.get(this.state, 'message.content'),
        messageDescription = (_.get(this.state.message, 'detail.detail')) ? (<p>{_.get(this.state.message, 'detail.detail')}</p>) : null;
        // TODO: Create pattern library modules for the different types of content that could be in this.state.message.detail
        messageDetail = (this.state.message && this.state.message.detail) ? (
            <div className='message-x-detail'>
              <h4>{_.get(this.state.message, 'detail.message', JSON.stringify(this.state.message.detail))}</h4>
              {messageDescription}
            </div>
        ) : null;
    var activeColumns = "",
        activeMessage = (this.state.message) ? (<div className={"alert alert-" + this.state.message.type}>
          {messageText}
          {messageDetail}
        </div>) : "",
        activeHelpText = !this.state.message && this.props.helpText ? <div className="form-help-text">{this.props.helpText}</div> : "",
        formControls = "",
        closeButton = this.props.handleCloseForm ? (<PlainButton name="close" label="Cancel" handleClick={this.handleReset} />) : "",
        loadingIcon = this.state.actionState == "waiting" ? (<LoadingIcon />) : "";
    if (["ready", "waiting"].indexOf(this.state.actionState) > -1){

      activeColumns = this.props.columns.map(function(item, i){
        var thisColumnItems = item.fields.map(function(fieldKey, j){
          var inputType = this.props.fieldsMeta[fieldKey].inputType;
          var value = this.state[fieldKey];
          var label = this.props.fieldsMeta[fieldKey].label;
          var required = this.props.fieldsMeta[fieldKey].required;
          
          if (inputType == 'image'){
            return (
              <div className="image-input" key={this.props.formId + "-form-field-" + i + '-' + j}>
                <ImageDropbox
                  onDroppedImage={this.handleImageDrop}
                  image={this.state.image}
                  imageData={this.state.imageData}
                  imageDescription={this.props.formType == "IssuerCreateUpdateForm" ? "Image": "Badge"}
                />
              </div>
            );
          }
          else if (inputType == 'select'){
            return (
              <InputGroup name={fieldKey} key={this.props.formId + "-form-field-" + i + '-' + j}
                inputType={inputType} selectOptions={this.state.fields[fieldKey].selectOptions} 
                value={value} 
                defaultValue={this.state.fields[fieldKey].defaultValue || this.state.fields[fieldKey].selectOptions[0]} 
                handleChange={this.handleChange}
                handleBlur={this.handleBlur}
                label={label}
              />
            );
          }
          else if (inputType == 'checkbox'){
            return (
              <InputGroup name={fieldKey} key={this.props.formId + "-form-field-" + i + '-' + j}
                inputType={inputType} 
                value={value} 
                handleChange={this.handleChange}
                handleBlur={this.handleBlur}
                label={label}
              />
            );
          }
          else if (["text", "textarea"].indexOf(inputType) > -1) {
            // for input types 'text', 'textarea'
            return (
              <InputGroup name={fieldKey} 
                key={this.props.formId + "-form-field-" + i + '-' + j}
                inputType={inputType}
                value={value} label={label} 
                handleChange={this.handleChange} 
                handleBlur={this.handleBlur}
              />
            );
          }
          else if (inputType == 'divider'){
            return (<p className="divider" key={"divider-" + i}><strong>{label}</strong></p>);
          }
        }.bind(this));
        return (
          <div className={item.className} key={this.props.formId + "-form-column-" + i}>
            {thisColumnItems}
          </div>
        );
      }.bind(this));
      formControls = (
        <div className="row form-controls">
          <SubmitButton name="submit" label={_.get(this.props, 'formControls.submit.label')} handleClick={this.handleSubmit} />
          {closeButton}
          {loadingIcon}
        </div>
      );
    }
    else {
      formControls = (
        <div className="row form-controls">
          {closeButton}
        </div>
      );
    }


    return (
      <div className="form-container issuer-notification-form-container">
        {activeMessage} {activeHelpText}
        <div className={this.state.actionState == "waiting" ? "form-horizontal disabled" : "form-horizontal"}>
          <div className="container-fluid">
            <fieldset className="row">
              {activeColumns}
            </fieldset>
          </div>
          {formControls}
        </div>
      </div>
    );
  }
});


// Export the Menu class for rendering:
module.exports.BasicAPIForm = BasicAPIForm;
