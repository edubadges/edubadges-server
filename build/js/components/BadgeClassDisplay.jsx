var _ = require('lodash');

var React = require('react');

// Stores
var APIStore = require('../stores/APIStore');

// Actions
var APISubmitData = require('../actions/api.js').APISubmitData;
var navigateLocalPath = require('../actions/clicks').navigateLocalPath;

// Components
var Button = require('../components/Button.jsx').Button;
var Dialog = require('../components/Dialog.jsx').Dialog;
var DialogOpener = require('../components/Dialog.jsx').DialogOpener;
var Heading = require('../components/Heading.jsx').Heading;
var Property = require('../components/BadgeDisplay.jsx').Property;

BadgeClassThumbnail = React.createClass({
  getDefaultProps: function() {
    return {
      handleClick: function(e){},
      showName: false
    };
  },
  render: function() {
    var name = "";
    if (this.props.showName) {
      name = (<p>{this.props.name}</p>);
    }
    return (
      <div
        className="badgeclass-display badge-display-thumbnail"
        onClick={this.props.handleClick}
      >
        <img src={this.props.image} alt={this.props.name} />
        {name}
      </div>
    );
  }
});

BadgeClassDetail = React.createClass({
  render: function() {

    return (
      <div className="detail_">
        <div>
          <img src={this.props.image} width="112" height="112" />
        </div>
        <ul>
          <li>
            <h2 className="detail_-x-meta">Criteria</h2>
            <p>{this.props.json.criteria}</p>
          </li>
          <li>
            <h2 className="detail_-x-meta">Issuer</h2>
            <p>{this.props.issuer.name}</p>
          </li>
          <li>
            <h2 className="detail_-x-meta">Issuer Website</h2>
            <p>{this.props.issuer.json.url}</p>
          </li>
          <li className="detail_-x-footer">Created on <strong>{this.props.created_at}</strong> by <strong>{this.props.created_by}</strong></li>
        </ul>
      </div>
    )
  }
});

BadgeClassTable = React.createClass({

    componentDidMount: function() {
        // TODO: Presumption of deletion
        APIStore.addListener('DATA_UPDATED_issuer_badgeclasses', this.handleDeletedBadge);
    },
    componentWillUnmount: function() {
        APIStore.removeListener('DATA_UPDATED_issuer_badgeclasses', this.handleDeletedBadge);
    },

    handleDeletedBadge: function() {
        // TODO: Success message?
        this.forceUpdate();
    },

    navigateToBadgeClassDetail: function(badgeClassSlug) {
        var badgeClassDetailPath = "/issuer/issuers/" + this.props.issuerSlug + "/badges/" + badgeClassSlug;
        navigateLocalPath(badgeClassDetailPath);
    },

    deleteBadgeClass: function(badgeClass) {
        apiContext = {
            apiCollectionKey: "issuer_badgeclasses",
            apiSearchKey: 'slug',
            apiSearchValue: badgeClass.slug,

            actionUrl: "/v1/issuer/issuers/"+ this.props.issuerSlug +"/badges/"+ badgeClass.slug,
            method: "DELETE",
            successHttpStatus: [200, 204],
            successMessage: "Badge class deleted."
        };

        APISubmitData(null, apiContext);
    },

    getRemoveButton: function(badgeClass) {
        if (badgeClass.recipient_count > 1) {
            return (
                <Button className="button_ button_-tertiary is-disabled" label="Remove"
                    popover="All instances of this badge must be revoked before removing it." />);
        }
        else {
            var actions=[
                <Button label="Remove"
                    onClick={this.deleteBadgeClass.bind(null, badgeClass)} />];
            var dialog = (
                <Dialog dialogId={"remove-badgeclass-"+ badgeClass.id} actions={actions} className="closable">
                    <Heading size="small"
                                title="Remove Badge"
                                subtitle="Are you sure you want to remove this badge?"/>
                </Dialog>);
            return (
                <DialogOpener dialog={dialog} dialogId={"remove-badgeclass-"+ badgeClass.id}>
                    <Button className="button_ button_-tertiary" label="Remove" propagateClick={true} />
                </DialogOpener>);
        }
    },

    render: function() {
        var badgeClasses = this.props.badgeClasses.map(function(badgeClass, i) {

            var removeButton = this.getRemoveButton(badgeClass);

            return (
                <tr>
                    <th scope="row" onClick={this.navigateToBadgeClassDetail.bind(null, badgeClass.slug)}>
                        <div className="l-horizontal">
                            <div>
                                <button><img src={badgeClass.image} width="48" height="48" alt="issuer description" /></button>
                                <button className="truncate_ action_ action_-tertiary">{badgeClass.name}</button>
                            </div>
                        </div>
                    </th>
                    <td>{badgeClass.recipient_count}</td>
                    <td>
                        <div className="l-horizontal">
                            <div>
                                <Button className="button_ button_-tertiary is-disabled" label="Issue" />
                                <Button className="button_ button_-tertiary is-disabled" label="Edit" />
                                {removeButton}
                            </div>
                        </div>
                    </td>
                </tr>
            );
        }.bind(this));

        return (
            <table className="table_">
                <thead>
                    <tr>
                        <th scope="col">Badge</th>
                        <th scope="col">No. of Recipients</th>
                        <th scope="col">Actions</th>
                    </tr>
                </thead>

                <tbody>
                    {badgeClasses}
                </tbody>

            </table>
        );
    },
});

BadgeClassList = React.createClass({
  getDefaultProps: function() {
    return {
      display: 'thumbnail',
      perPage: 4,
      currentPage: 1,
      showNameOnThumbnail: false,
      emptyMessage: "There are no badges defined yet.",
      includeNullItem: false,
      handleNullClick: function(e) {},
    };
  },
  render: function() {
    var perPage = this.props.perPage == -1 ? _.get(this.props, 'badgeClasses.length') : this.props.perPage;

    var badgeClasses = this.props.badgeClasses.slice(
      perPage * (this.props.currentPage-1),
      perPage + perPage * (this.props.currentPage-1)
    ).map(function(bc, i){
      var properties = {
        image: bc.image,
        name: bc.name,
        slug: bc.slug,
        key: "bc-" + i,
        showName: this.props.showNameOnThumbnail
      }


      if (this.props.display == 'thumbnail'){
        var handleClick = function(e){};
        var providedHandler = this.props.handleClick
        if (providedHandler) {
          handleClick = function(e) { providedHandler(e, bc); };
        }
        return (
          <BadgeClassThumbnail {...properties} handleClick={handleClick} />
        );
      }
      else {
        var badgeclassPath = "/issuer/issuers/" + this.props.issuerSlug + "/badges/" + bc.slug;
        var handleClick = function(e){navigateLocalPath(badgeclassPath);};
        var providedHandler = this.props.handleClick;
        if (providedHandler) {
          handleClick = function(e) { providedHandler(e, bc); };
        }
        return (
          <BadgeClassDetail {...bc} key={'bc-' + i} handleClick={handleClick} />
        );
      }
    }.bind(this));
    if (badgeClasses.length < 1) {
      badgeClasses = this.props.emptyMessage;
    } else if (this.props.includeNullItem) {
      badgeClasses.push(<div key={"nullItem"}
                          className="badgeclass-display badgeclass-display-none col-xs-3"
                          onClick={this.props.handleNullClick}
                          >
                          <img src="/static/images/none.png" alt="No Badge" />
                          <p>No Badge</p>
                        </div>);
    }
    return (
      <div className="container-fluid">
        <div className="open-badge-list">
          {badgeClasses}
        </div>
      </div>
    );
  }

});


module.exports = {
  BadgeClassTable: BadgeClassTable,
  BadgeClassList: BadgeClassList,
  BadgeClassDetail: BadgeClassDetail
};
