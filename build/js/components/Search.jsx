var React = require('react');

var Search = React.createClass({

    getInitialState: function() {
        return {
            'active': false,
            'populated': false,
        }
    },

    handleClick: function(e) {
        e.stopPropagation(); e.preventDefault();

        var value = this.refs.search.getDOMNode().value
        if (this.props.handleClick) {
            this.props.handleClick(value);
        }
    },
    close: function() {
        this.setState({'active': false, 'populated': false}, function() {
            this.refs.search.getDOMNode().value = '';
            if (this.props.handleClick)
                this.props.handleClick('');
        })
    },
    setPopulated: function() {
        this.setState({'populated': true})
    },
    setActive: function() {
        this.setState({'active': true}, function() {
            this.refs.search.getDOMNode().focus();
        })
    },
    handleMouseLeave: function() {
        if (!this.state.populated) {
            this.setState({'active': false})
        }
    },

    render: function() {
        var stateClasses = "";
        if (this.state.active)
            stateClasses += " is-active"
        if (this.state.populated)
            stateClasses += " is-populated"
        return (
            <form action="" className={"search_ "+stateClasses}>
                <fieldset onMouseEnter={this.setActive} onMouseLeave={this.handleMouseLeave}>
                    <input ref="search" type="text" placeholder="Search&hellip;" onFocus={this.setPopulated}/>
                    <button onClick={this.handleClick} className="search_-x-submit icon_ icon_-search icon_-notext" type="submit">Search</button>
                    <button onClick={this.close} className="search_-x-close icon_ icon_-small icon_-clear icon_-notext" type="button">Close</button>
                </fieldset>
            </form>);
    }
});

module.exports = {
    'Search': Search,
}
