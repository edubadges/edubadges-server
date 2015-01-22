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
      ( <input name={this.props.name} value={this.props.value} className={this.classNameForInput()} type="text" onChange={this.props.handleChange} onBlur={this.props.handleBlur} /> );
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
    recipientIds: ReactPropTypes.arrayOf(ReactPropTypes.string),
    selectedRecipientId: ReactPropTypes.string,
    pk: ReactPropTypes.number,
    earner_description: ReactPropTypes.string,
    imageData: ReactPropTypes.string, 
    message: ReactPropTypes.string
  },

  getDefaultProps: function() {
    return {
      actionState: "ready", // "ready", "waiting", "disabled", "complete"
      intial_earner_description: "",
      action: '/earn/badges'
    };
  },
  getInitialState: function() {
    return {
      recipient_input: this.props.recipientIds[0] || "",
      earner_description: this.props.earner_description,
      actionState: this.props.actionState 
    };
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
    console.log("Handling image drop...");

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
    if (this.props.actionState != "ready"){
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
    console.log("TIME TO PATCH THE FORM");
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
    console.log("EarnerBadgesForm sees that its state has been updated in the FormStore.");
    // 'this' is bound: EarnerBadgeForm
    console.log(FormStore.getFormData(this.props.formId))
    if (this.isMounted())
      this.setState(FormStore.getFormData(this.props.formId));
  },

  handleSubmit: function(e){
    e.preventDefault(); 
    e.stopPropagation();

    console.log("GOING TO SUBMIT THE EARNER FORM");
    FormActions.submitForm(this.props.formId);
    
  },

  render: function(){
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
      />)
    }
    var imageDropbox = "";
    if (this.state.actionState == "ready" || this.state.actionState == "waiting"){
      imageDropbox = (<ImageDropbox onDroppedImage={this.handleImageDrop} image={this.state.image} imageData={this.state.imageData} />)
    }
    return (
      <div className="earner-badge-form-container">
        <form action={this.props.action} method="POST" className={this.state.actionState == "waiting" ? "form-horizontal disabled" : "form-horizontal"}>
          <fieldset>

            {imageDropbox}
            {formResult}

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
            { loadingIcon }
          </fieldset>
        </form>
        
      </div>
    )
  }
});

// Export the Menu class for rendering:
module.exports.EarnerBadgeForm = EarnerBadgeForm;
