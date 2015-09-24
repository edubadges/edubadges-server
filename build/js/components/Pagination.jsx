var React = require('react');
var ClickActions = require('../actions/clicks');

var Pagination = React.createClass({
    getDefaultProps: function() {
        return {
            first: undefined,
            last: undefined,
            next: undefined,
            prev: undefined,
            page: 1,
            perPageCount: 35,
            thisPageCount: undefined,
            totalPages: undefined,
            totalCount: undefined,
            checkingProgress: true,
            verboseName: undefined,
        };
    },

    handleClickNext: function() { if (this.props.next) { ClickActions.navigateLocalPath(this.props.next); } },
    handleClickPrev: function() { if (this.props.prev) { ClickActions.navigateLocalPath(this.props.prev); } },
    handleClickFirst: function() { if (this.props.first) { ClickActions.navigateLocalPath(this.props.first); } },
    handleClickLast: function() { if (this.props.last) { ClickActions.navigateLocalPath(this.props.last); } },

    render: function() {

        var first = this.props.first ?
            ( <button className="icon_ icon_-notext icon_-first" onClick={this.handleClickFirst}>First</button> ) :
            ( <button className="icon_ icon_-notext icon_-first" disabled="disabled">First</button> );

        var previous = this.props.prev ?
            ( <button className="icon_ icon_-notext icon_-previous" onClick={this.handleClickPrev}>Previous</button> ) :
            ( <button className="icon_ icon_-notext icon_-previous" disabled="disabled">Previous</button> );

        var next = this.props.next ?
            ( <button className="icon_ icon_-notext icon_-next" onClick={this.handleClickNext}>Next</button> ) :
            ( <button className="icon_ icon_-notext icon_-next" disabled="disabled">Next</button> );

        var last = this.props.last ?
            ( <button className="icon_ icon_-notext icon_-next" onClick={this.handleClickLast}>Last</button> ) :
            ( <button className="icon_ icon_-notext icon_-next" disabled="disabled">Last</button> );


        var idxFirst = 1+(this.props.page-1)*this.props.perPageCount;
        var idxLast = (this.props.page-1)*this.props.perPageCount + this.props.thisPageCount;
        var totalCount = this.props.totalCount ? "of "+this.props.totalCount : "";
        var totalPages = this.props.totalPages ? (<p>of {this.props.totalPages}</p>) : "";

        var progress = this.props.checkingProgress ? (<p className="pagination_-x-status">Checking for new badges …</p>) : "";

        return (
            <div className="pagination_">
                <div>
                    <nav>
                        {first}
                        {previous}
                        <form action="">
                            <p>Page {this.props.page}</p>
                            {totalPages}
                        </form>
                        {next}
                        {last}
                    </nav>
                    {progress}
                </div>
                <p>Displaying {idxFirst}-{idxLast} {this.props.verboseName} {totalCount}</p>
            </div>);
    }
});

module.exports = {
    Pagination: Pagination
};
