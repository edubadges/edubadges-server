var React = require('react');
var OpenBadge = require('../components/BadgeDisplay.jsx').OpenBadge;


var OpenBadgeList = React.createClass({

  render: function(){
    return (
      <div className="open-badge-list">
        <OpenBadge display="thumbnail" />
        <OpenBadge display="detail" />
        <OpenBadge display="full" />
      </div>
    );
  }
});

// Export the Menu class for rendering:
module.exports = OpenBadgeList;