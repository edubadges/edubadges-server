var React = require('react');

var Title = React.createClass({
    getDefaultProps: function() {
        return {
            title: "Title",
            subtitle: undefined,
            options: undefined,
            centered: false,
        }
    },

    render: function() {
        var title = this.props.subtitle ?
            (<div>
                <h1 className="title_-x-primary">{this.props.title}</h1>
                <p className="title_-x-secondary">{this.props.subtitle}</p>
             </div>) :
            (<div>
                <h1 className={this.props.centered ? 'title_-x-centered' : ''}>{this.props.title}</h1>
             </div>);
        var options = this.props.options ? (
            <div>
                <button className="icon_ icon_-notext icon_-right icon_-more">Options</button>
            </div>) : "";
        return (
            <div className="title_">
                {title}
                {options}
            </div>);
    }
});


module.exports = {
    Title: Title
};
