var React = require('react');
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;
var APIStore = require('../stores/APIStore');

var OpenBadgeList = React.createClass({
  /*
  this.props.badgeList = [
    {
            "recipient_id": "nate@ottonomy.net",
            "id": 8,
            "json": {
                "id": "https://app.achievery.com/badge-assertion/4613",
                "type": "Assertion",
                "uid": {
                    "type": "xsd:string",
                    "@value": "4613"
                },
                ...
            },
            "errors": []
        }
    ],
  ]
  */
  getDefaultProps: function() {
    return {
      badges: []
    };
  },
  render: function(){  

    //var badgesInList = this.props.badgeList.map(function(item, i){
    var badgesInList = this.props.badges.map(function(item, i){
      return (
        <OpenBadge 
          key={"key-" + item['id']}
          id={item['id']}
          display="thumbnail"
          json={item['json']}
          recipientId={item['recipient_id']}
          errors={item['errors']}
        />
      );
    }.bind(this));
    return (
      <div className="open-badge-list">
        { badgesInList }
      </div>
    );
  }
});

// Export the Menu class for rendering:
module.exports = OpenBadgeList;