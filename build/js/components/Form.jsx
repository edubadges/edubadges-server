var React = require('react');
var ReactPropTypes = React.PropTypes;
var EarnerActions = require('../actions/earner');
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var APIStore = require('../stores/APIStore');
var Dropzone = require('react-dropzone');


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
      ( <input name={this.props.name} value={this.props.value} className={this.classNameForInput()} type="text" onChange={this.props.handleChange} /> );
    }
    else if (this.props.inputType == "textarea"){
      return ( <textarea name={this.props.name} value={this.props.value} onChange={this.props.handleChange} /> );
    }
    else if (this.props.inputType == "select") {
      var selectOptions = this.props.selectOptions.map(function(option, index){
        return ( <option value={option} key={this.props.name + '-' + index}>{option}</option>);
      }.bind(this));
      return ( 
        <select name={this.props.name} value={this.props.value} className="input-xlarge" onChange={this.props.handleChange}>
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
  fileToDataURL: function(file){
    console.log("converting file type " + file.type);
    if (file.type && (file.type == 'image/png' || file.type == 'image/svg')){
      var reader = new FileReader();
      reader.onload = function(e) { this.setState({ imageData: reader.result}); }.bind(this);
      reader.readAsDataURL(file);
    }
    else
      return "";
  },
  getInitialState: function() {
    return {
      imageData: this.props.image ? this.fileToDataURL(this.props.image) : ""
    };
  },
  fileHandler: function(file){
    console.log("A file has been dropped on the Dropzone!");
    console.log(file);
    this.fileToDataURL(file);
    this.props.onDroppedImage(file);

  },
  render: function() {
    var imageDisplay = this.state.imageData ? (<img src={this.state.imageData} />) : "";
    return (
      <div className="control-group">
        <label className="control-label" htmlFor={this.props.name}>{this.props.label}</label>
        <div className="controls">
          <Dropzone handler={this.fileHandler} size={200} message="hello, world">
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
    image: ReactPropTypes.string, 
  },

  getDefaultProps: function() {
    return {
      initialState: "ready", // "ready", "waiting", "disabled", "complete"
      earner_description: "",
      action: '/earn/badges'
    };
  },
  getInitialState: function() {
    return {
      actionState: this.props.initialState,
      recipient_input: this.props.recipientIds[0] || "",
      earner_description: this.props.earner_description 
    };
  },
  handleImageDrop: function(file){
    this.setState({
      image: file
    });
  },
  handleChange: function(event){
    //reject change unless form is ready
    if (this.state.actionState != "ready"){
      event.stopPropagation();
      event.preventDefault();
      return;
    }

    var field = event.target.name;
    if (field == 'image'){
      var value = event.target.files[0];
    }
    else{
      var value = event.target.value;
    }
    var theChange = {};
    theChange[field] = value;
    this.setState(theChange);
  },

  handleSubmit: function(e){
    var data = {
      recipient_input: this.state.recipient_input,
      earner_description: this.state.earner_description,
    };
    var image = this.state.image;
    if (this.props.pk)
      data['pk'] = this.props.pk;

    this.setState({ actionState: 'waiting' });
    EarnerActions.submitEarnerBadgeForm(data, image);

    e.preventDefault(); 
    e.stopPropagation;
  },

  updateWithNewBadge: function(){
    var newBadge = APIStore.getCollectionLastItem('earnerBadges');
    console.log(newBadge);
    this.setState({
      result: newBadge,
      actionState: 'complete'
    });
  },
  componentDidMount: function() {
    APIStore.addListener('DATA_UPDATED_earnerBadges', this.updateWithNewBadge);
  },
  componentWillUnmount: function() {
    APIStore.removeListener('DATA_UPDATED_earnerBadges', this.updateWithNewBadge);
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
      imageDropbox = (<ImageDropbox onDroppedImage={this.handleImageDrop} image={this.state.image} />)
    }
    return (
      <div className="earner-badge-form-container">
        <form action={this.props.action} method="POST" className={this.state.actionState == "waiting" ? "form-horizontal disabled" : "form-horizontal"}>
          <fieldset>

            {imageDropbox}
            {formResult}

            <InputGroup name="image" inputType="filebutton" label="Badge Image" handleChange={this.handleChange} />

            <InputGroup name="earner_description" inputType="textarea" 
              label="Earner Annotation" value={this.state.earner_description} 
              handleChange={this.handleChange}
              />

            <InputGroup name="recipient_input" 
              inputType="select" selectOptions={this.props.recipientIds} 
              value={this.state.recipient_input} 
              defaultValue={this.props.recipientIds[0]} 
              handleChange={this.handleChange}
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
