var React = require('react');
var ReactPropTypes = React.PropTypes;

// Stores
var APIStore = require('../stores/APIStore');
var FormStore = require('../stores/FormStore');

// Components
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var Dropzone = require('react-dropzone');

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
    value: React.PropTypes.string,
    handleChange: ReactPropTypes.func,
    placeholder: ReactPropTypes.string
  },
  classNameForInput: function(){
    var classes = {
      "filebutton": "input-file",
      "textarea": "input-textarea", //wrong. double-check. http://getbootstrap.com/components/#input-groups says you can't use textarea in .input-group
      "select": "input-group-select"
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
      return ( <textarea name={this.props.name} value={this.props.value} onChange={this.props.handleChange} onBlur={this.props.handleBlur} /> );
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
      <div className="control-group">
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
    if (file instanceof File && (file.type && (file.type == 'image/png' || file.type == 'image/svg')))
      return true;
    else
      console.log("FILE DID NOT SEEM TO VALIDATE.")
  },
  fileHandler: function(file){
    console.log("A file has been dropped on the Dropzone!");
    console.log(file);
    if (this.validateFileType(file)){
      this.props.onDroppedImage(file);
    }
  },
  render: function() {
    var imageDisplay = this.props.imageData ? (<img src={this.props.imageData} />) : "";
    return (
      <div className="control-group">
        <label className="control-label" htmlFor={this.props.name}>{this.props.label}</label>
        <div className="controls">
          <Dropzone handler={this.fileHandler} size={200} message="Drop badge image here">
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
      <div className="control-group">
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
      <div className="control-group">
        <label className="control-label sr-only" htmlFor={this.props.name}>{ this.props.label || "Reset" }</label>
        <div className="controls">
          <button name={this.props.name} className="btn btn-danger" onClick={this.props.handleClick}>{this.props.label || "Reset" }</button>
        </div>
      </div>
    );
  }
});

var LoadingIcon = React.createClass({
  render: function(){
    return (
      <div className="loading-icon" >
        <span className='sr-only'>Loading...</span>
      </div>
    )
  }
});


/* EarnerBadgeForm 
 * A form that allows the user to upload a new badge, indicate which of their verified email 
 * addresses the badge belongs to, and then see the uploaded badge.
 */
var EarnerBadgeForm = React.createClass({
  propTypes: {
    action: ReactPropTypes.string,
    formId: ReactPropTypes.string,
    recipientIds: ReactPropTypes.arrayOf(ReactPropTypes.string),
    pk: ReactPropTypes.number,
    initialState: ReactPropTypes.object
  },

  getDefaultProps: function() {
    return {
      action: '/earn/badges'
    };
  },
  getInitialState: function() {
    return this.props.initialState;
  },
  // NO, this is wrong. The App.jsx should be passing props to this component
  updateFromFormData: function(){
    formData = FormStore.getFormData(this.props.formId);
    this.setState(formData);
  },

  // Mount/unmount the change handler based on this component's lifecycle, but use the fn passed 
  // in as props to mutage state, because App.jsx is where state is managed.
  componentDidMount: function() {
    FormStore.addListener('FORM_DATA_UPDATED_EarnerBadgeForm', this.handlePatch);
  },
  componentWillUnmount: function() {
    FormStore.removeListener('FORM_DATA_UPDATED_EarnerBadgeForm', this.handlePatch);
  },
  handleImageDrop: function(file){
    // To make sure any changes within the focused element are recorded in the form state
    document.activeElement.blur();

    var reader = new FileReader();
    reader.onload = function(e) {
      if (this.isMounted()){
        FormActions.patchForm(this.props.formId, { image: file, imageData: reader.result });
      }
      else
        console.log("TRIED TO SET FILE TO STATE, FAILED. WAS BUSY MOUNTING."); 
    }.bind(this);
    reader.readAsDataURL(file);

  },
  // handleChange fires on changes to the DOM value of form elements, updating state locally
  handleChange: function(event){
    //reject change unless form is ready
    if (this.state.actionState != "ready"){
      event.stopPropagation();
      event.preventDefault();
      return;
    }

    var field = event.target.name;

    // if file case, shortcut to image handling
    if (field == 'image'){
      var value = event.target.files[0];
      this.handleImageDrop(value);
    }

    // for other changes, manage locally
    else{
      var value = event.target.value;
      var theChange = {};
      theChange[field] = value;
      if (this.isMounted())
        this.setState(theChange);
      else{
        console.log("This probably should never fire: form value changed as it was unmounting..")
        FormActions.patchForm(this.props.formId, theChange);
      }
    }
    
  },
  // When an input field is blurred, a form patch is submitted if its value has changed.
  // Does not apply to the image upload field
  handleBlur: function(event){
    var patch = {}
    var field = event.target.name;
    var currentData = FormStore.getFormData(this.props.formId);
    if (currentData[field] !== event.target.value){
      patch[field] = event.target.value;
      FormActions.patchForm(this.props.formId, patch);
    }
  },
  // This catches the result from form update and applies it to the formstate. 
  // On submit, it is how the result gets displayed.
  handlePatch: function(){
    // 'this' is bound: EarnerBadgeForm
    
    if (this.isMounted()){
      var newState = FormStore.getFormData(this.props.formId);
      this.setState(newState);
    }
  },

  handleSubmit: function(e){
    e.preventDefault(); 
    e.stopPropagation();

    if (this.state.actionState != "waiting")
      FormActions.submitForm(this.props.formId);
    
  },
  handleReset: function(e){
    e.preventDefault();
    e.stopPropagation();

    if(!this.props.pk){
      FormActions.patchForm(this.props.formId, {
        recipient_input: this.props.recipientIds[0],
        earner_description: "",
        image: undefined,
        imageData: "",
        actionState: "ready", 
        result: undefined,
        message: undefined
      });
    }
    else {
      // TODO: write case for resetting edited form to the original badge info.
    }
      
  },

  render: function(){
    var messageAlert = (this.state.message) ? (<div className={"alert alert-" + this.state.message.type} >{this.state.message.content}</div>) : "";
    var loadingIcon = this.state.actionState == "waiting" ? (<LoadingIcon />) : "";
    var formResult = "";
    if (this.state.result){
      item = this.state.result;
      formResult = (<OpenBadge 
        pk={item.badge.pk}
        display="detail"
        image={ item.badge.image }
        badge={ item.badge.full_badge_object }
        earner={ item.badge.recipient_input }
        setActiveBadgeId={ function(event){return;} }
        handleCloseClick={this.handleReset}
      />)
    }
    var activeInputs = "";
    if (this.state.actionState == "ready" || this.state.actionState == "waiting"){
      activeInputs = (
        <fieldset>
          <ImageDropbox onDroppedImage={this.handleImageDrop} image={this.state.image} imageData={this.state.imageData} />

          <InputGroup name="image" inputType="filebutton" 
            label="Badge Image" handleChange={this.handleChange} 
            handleBlur={this.handleBlur}
          />

          <InputGroup name="earner_description" inputType="textarea" 
            label="Earner Annotation" value={this.state.earner_description} 
            handleChange={this.handleChange} handleBlur={this.handleBlur}
          />

          <InputGroup name="recipient_input" 
            inputType="select" selectOptions={this.props.recipientIds} 
            value={this.state.recipient_input} 
            defaultValue={this.props.recipientIds[0]} 
            handleChange={this.handleChange}
            handleBlur={this.handleBlur}
          />

          <SubmitButton name="submit" handleClick={this.handleSubmit} />
        </fieldset>
      );
    }
    return (
      <div className="form-container earner-badge-form-container">
        <form action={this.props.action} method="POST" className={this.state.actionState == "waiting" ? "form-horizontal disabled" : "form-horizontal"}>
            {messageAlert}
            {formResult}
            {activeInputs}
            
            <ResetButton name="reset" handleClick={this.handleReset} />
            { loadingIcon }
        </form>
        
      </div>
    )
  }
});

IssuerNotificationForm = React.createClass({
  getInitialState: function() {
    return this.props.initialState;
  },  
  // Mount/unmount the change handler based on this component's lifecycle, but use the fn passed 
  // in as props to mutage state, because App.jsx is where state is managed.
  componentDidMount: function() {
    FormStore.addListener('FORM_DATA_UPDATED_IssuerNotificationForm', this.handlePatch);
  },
  componentWillUnmount: function() {
    FormStore.removeListener('FORM_DATA_UPDATED_IssuerNotificationForm', this.handlePatch);
  },
  handleChange: function(event){
    
    //reject change unless form is ready
    if (this.state.actionState != "ready"){
      event.stopPropagation();
      event.preventDefault();
      return;
    }
    var field = event.target.name;
    var value = event.target.value;

    var theChange = {};
    theChange[field] = value;
    if (this.isMounted())
      this.setState(theChange);
    else{
      console.log("This probably should never fire: form value changed as it was unmounting..")
      FormActions.patchForm(this.props.formId, theChange);
    }
  },
  // When an input field is blurred, a form patch is submitted if its value has changed.
  // Does not apply to the image upload field
  handleBlur: function(event){
    var patch = {}
    var field = event.target.name;
    var currentData = FormStore.getFormData(this.props.formId);
    if (currentData[field] !== event.target.value){
      patch[field] = event.target.value;
      FormActions.patchForm(this.props.formId, patch);
    }
  },
  // This catches the result from form update and applies it to the formstate. 
  // On submit, it is how the result gets displayed.
  handlePatch: function(){
    // 'this' is bound: EarnerBadgeForm
    
    if (this.isMounted()){
      var newState = FormStore.getFormData(this.props.formId);
      this.setState(newState);
    }
  },
  handleSubmit: function(e){
    e.preventDefault(); 
    e.stopPropagation();
    if (this.state.actionState != "waiting")
      FormActions.submitForm(this.props.formId);
  },
  handleReset: function(e){
    e.preventDefault();
    e.stopPropagation();

    FormActions.patchForm(this.props.formId, {
      email: "",
      url: "",
      actionState: "ready", 
      result: undefined,
      message: undefined
    });
      
  },
  render: function() {
    var messageAlert = (this.state.message) ? (<div className={"alert alert-" + this.state.message.type} >{this.state.message.content}</div>) : "";
    var loadingIcon = this.state.actionState == "waiting" ? (<LoadingIcon />) : "";
    var activeInputs = "";
    if (this.state.actionState == "ready" || this.state.actionState == "waiting"){
      activeInputs = (
        <fieldset>
          <InputGroup name="url" inputType="text" value={this.state.url}
            label="Assertion URL" handleChange={this.handleChange} 
            handleBlur={this.handleBlur}
          />

          <InputGroup name="email" inputType="text" 
            label="Earner Email Address" value={this.state.email} 
            handleChange={this.handleChange} handleBlur={this.handleBlur}
          />

          <SubmitButton name="submit" handleClick={this.handleSubmit} />
        </fieldset>
      );
    }
    return (
      <div className="form-container issuer-notification-form-container">
        <form action={this.props.action} method="POST" className={this.state.actionState == "waiting" ? "form-horizontal disabled" : "form-horizontal"}>
            {messageAlert}
            {activeInputs}
            
            <ResetButton name="reset" handleClick={this.handleReset} />
            { loadingIcon }
        </form>
      </div>
    );
  }
});

// Export the Menu class for rendering:
module.exports.EarnerBadgeForm = EarnerBadgeForm;
module.exports.IssuerNotificationForm = IssuerNotificationForm;
