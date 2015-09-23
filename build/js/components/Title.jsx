var React = require('react');

var Title = React.createClass({
    getDefaultProps: function() {
        return {
            title: "Title",
            subtitle: undefined,
            options: undefined,
            centered: false,
            truncate: false,
        };
    },

    render: function() {
        var headerClassList = [];
        if (this.props.centered) headerClassList.push('title_-x-centered');
        if (this.props.truncate) headerClassList.push('truncate_');

        var title = this.props.subtitle ?
            (<div>
                <h1 className="title_-x-primary">{this.props.title}</h1>
                <p className="title_-x-secondary">{this.props.subtitle}</p>
             </div>) :
            (<div>
                <h1 className={headerClassList.join(' ')}>{this.props.title}</h1>
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
