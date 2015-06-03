var React = require('react');

// Actions
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;


// Components
var Property = require('../components/BadgeDisplay.jsx').Property;
var EarnerBadgeList = require('../components/EarnerBadgeList.jsx');

var CollectionBadgeList = React.createClass({
  render: function() {
    return (
      <div className='collection-badgeclasses-list'>
        {badges}
      </div>
    );
  }
});


var EarnerCollection = React.createClass({
  handleClick: function(){
    if (this.props.clickable)
      navigateLocalPath(
        this.props.targetUrl || '/earner/collections/' + this.props.slug
      );
  },
  render: function() {
    return (
      <div className={"earner-badge-collection collection-" + this.props.display} onClick={this.handleClick}>
        <Property name='Name' property={{type:'xsd:string', '@value': this.props.name}} />
        <Property name='Description' property={{type: 'xsd:string', '@value': this.props.description}} />
        <EarnerBadgeList display="card" badges={this.props.badgeList} />
      </div>
    );
  }
});

/* 
  EarnerCollectionList: 
*/
var EarnerCollectionList = React.createClass({
  getDefaultProps: function() {
    return {
      display: 'thumbnail',
      clickable: true
    };
  },
  render: function() {
    var collections = this.props.collections.map(function(item, i){
      return (
        <EarnerCollection
          key={'collection-' + i}
          name={item.name}
          slug={item.slug}
          description={item.description}
          badgeList={item.badgeList || []}
          display={this.props.display}
          clickable={this.props.clickable}
        />
      );
    }.bind(this));
    return (
      <div className="earner-collection-list">
        {collections}
      </div>
    );
  }
});


module.exports = {
  EarnerCollectionList: EarnerCollectionList,
  EarnerCollection: EarnerCollection
};
