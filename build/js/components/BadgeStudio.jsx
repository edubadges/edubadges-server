var React = require('react');

var _ = require('lodash');

// Components
var Button = require('../components/Button.jsx').Button;
var StudioCanvas = require('../components/StudioCanvas.jsx').StudioCanvas;


var StudioNavItem = React.createClass({
    render: function() {
        return (
            <li>
                <a {...this.props} className="gallerynav_-x-item gallerynav_-is-active" href="#tab-shapes">
                    <span className="icon_ icon_-shapes icon_-large">{this.props.children}</span>
                </a>
            </li>
        )
    },
});

var StudioOptionList = React.createClass({
    propTypes: {
        tab: React.PropTypes.string.isRequired,
        assets: React.PropTypes.array,
    },

    render: function() {
        var assets;
        if (this.props.assets) {
            assets = this.props.assets.map(function(asset, i) {
                if (this.props.palettes[asset]){
                    return (
                        <li key={i} onClick={this.props.onClick} data-label={asset}>
                            <label className="imageselect_" htmlFor="imageselect">
                                <input type="radio" name="imageselect" id="imageselect" value="imageselect" />
                                <span className="imageselect_-x-graphic">
                                    <span className="imageselect_-x-color" style={{'backgroundColor': this.props.palettes[asset][0]}}>
                                        {asset.split('-')[0]}</span>
                                    <span className="imageselect_-x-color" style={{'backgroundColor': this.props.palettes[asset][1]}}>
                                        {asset.split('-')[1]}</span>
                                </span>
                                <span className="imageselect_-x-description">{asset}</span>
                            </label>
                        </li>
                    );
                }

                var img;
                if (asset) {
                    img = (<img src={"/static/badgestudio/"+ this.props.tab +"/"+ asset} width="100" height="100" />);
                } else {
                    img = (<img src={"/static/badgestudio/none.png"} width="100" height="100" />);
                }
                return (
                    <li key={i} onClick={this.props.onClick} data-label={asset}>
                        <label className="imageselect_" htmlFor={asset}>
                            <input type="radio" name="imageselect" value={asset} />
                            {img}
                        </label>
                    </li>
                )
            }.bind(this));
        }

        return (
            <section id="tab-shapes">
                <h2 className="wrap_ wrap_-dark wrap_-borderbottom label_ l-studio-x-header">Badges</h2>
                <div>
                    <ul className="l-wrappinglist">
                        {assets}
                    </ul>
                </div>
            </section>
        )
    }
});

var BadgeStudio = React.createClass({
    _canvas: undefined,

    getDefaultProps: function() {
        return {
            badgeDetail: undefined,
            canvas: {
                width: 280,
                height: 280,
            },
            assets: {
                shapes: ['circle.svg', 'circle-1.svg', 'rope-1.svg', 'shield-1.svg', 'starburst-1.svg'],
                backgrounds: ['paisley.png', 'swirl.png', 'feathers.png', 'china.png', 'confectionary.png', undefined],
                graphics: [
                    'maple-leaf.png', 'airplane.png', 'approve.png', 'award.png', 'baggage.png', 'battery.png',
                    'beaker.png', 'beer.png', 'bell.png', 'car.png', 'cd.png', 'cinema.png', 'climbing.png',
                    'cocktail-glass.png', 'coffeeshop.png', 'cycling.png', 'factory.png', 'film.png', 'fir-tree.png',
                    'fire-extinguisher.png', 'hiker.png', 'horseback-trail.png', 'hospital-sign.png', 'iphone.png',
                    'keyhole.png', 'light-bulb.png', 'lock.png', 'mental-health.png', 'mushroom.png', 'power.png',
                    'puzzle.png', 'recycle.png', 'ship.png', 'sun.png', 'swimming.png', 'telephone.png',
                    'traffic-cone.png', 'trophy.png', 'umbrella.png', 'white-star.png', 'wireless.png', 'wrench.png', 
                    undefined
                ],
                colors: ['blue-green', 'aqua-purple', 'gray-red']
            },
            palettes: {
                'blue-green': ['#617697', '#88aa5a'],
                'aqua-purple': ['#27b2b7', '#524557'],
                'gray-red': ['#d4d4d4', '#cd0000']
            },
			handleBadgeComplete: undefined
        };
    },

    getInitialState: function() {
        return {
            activeTab: 'shapes',
            selectedOptions: {
                shapes: undefined,
                backgrounds: undefined,
                graphics: undefined,
                colors: undefined
            },
        };
    },

    handleTabClick: function(ev) {
        this.setState({activeTab: ev.currentTarget.dataset.label});
    },

    handleOptionClick: function(ev) {
        ev.stopPropagation(); ev.preventDefault();
        var selectedOptions = this.state.selectedOptions || {};
        selectedOptions[this.state.activeTab] = ev.currentTarget.dataset.label;
        this.setState({selectedOptions: selectedOptions});
    },

    getColors: function(){
        // Take the filename of the palette image and return the array of the background and foreground
        // colors that it represents.
        if (this.state.selectedOptions.colors) {
            return this.props.palettes[this.state.selectedOptions.colors];
        }
        return [undefined, undefined];
    },

    saveCanvas: function(instance) {
        this._canvas = instance;
    },

    handleBadgeComplete: function(e) {
        e.stopPropagation();
        e.preventDefault();

        var dataURL;
        var blob;
        if (this.refs.studio_canvas) {
            this.refs.studio_canvas.studio.canvas.deactivateAll().renderAll();
            dataURL = this.refs.studio_canvas.studio.canvas.toDataURL({format: 'png', multiplier: 400 / this.props.canvas.width});
            blob = window.dataURLtoBlob && window.dataURLtoBlob(dataURL);
            if (blob) {
                // turn blob into a File
                blob.lastModifiedDate = new Date();
                blob.name = "custom badge";
            }
        } else {
            console.log("Error: unable to find badge studio dataURL")
        }
        if (this.props.handleBadgeComplete)
            this.props.handleBadgeComplete(dataURL, blob);
    },

    handleCancel: function(e) {
        e.stopPropagation();
        e.preventDefault();
        if (this.props.handleBadgeComplete)
            this.props.handleBadgeComplete();
    },

    render: function() {
        var badgeName = _.get(this.props.badgeDetail, 'name')
        var badgeDescription = _.get(this.props.badgeDetail, 'description')
        var badgeCriteria = _.get(this.props.badgeDetail, 'criteria')

        var name = badgeName ? (<li><h2 className="detail_-x-meta">Name</h2>
                                <p>{_.get(this.props.badgeDetail, 'name')}</p></li>) : "";
        var description = badgeDescription ? (<li><h2 className="detail_-x-meta">Description</h2>
                                <p>{_.get(this.props.badgeDetail, 'description')}</p></li>) : "";
        var criteria = badgeCriteria ? (<li><h2 className="detail_-x-meta">Criteria</h2>
                                <p>{_.get(this.props.badgeDetail, 'criteria')}</p></li>) : "";
        var detail = (
            <div className="detail_">
            <ul>
                {name}
                {description}
                {criteria}
            </ul>
            </div>
        );
        return (
            <form className="l-studio wrap_ wrap_-borderbottom">
                <nav className="wrap_ wrap_-shadow wrap_-dark">
                    <h1 className="wrap_ wrap_-dark wrap_-borderbottom textindent_ l-studio-x-header">Badge Studio</h1>
                    <ul className="gallerynav_">
                        <StudioNavItem onClick={this.handleTabClick} data-label="shapes">Shapes</StudioNavItem>
                        <StudioNavItem onClick={this.handleTabClick} data-label="backgrounds">Backgrounds</StudioNavItem>
                        <StudioNavItem onClick={this.handleTabClick} data-label="graphics">Graphics</StudioNavItem>
                        <StudioNavItem onClick={this.handleTabClick} data-label="colors">Colors</StudioNavItem>
                    </ul>
                </nav>
                <div className="wrap_ wrap_-borderright">
                    <StudioOptionList
                        onClick={this.handleOptionClick}
                        tab={this.state.activeTab}
                        assets={this.props.assets[this.state.activeTab]}
                        palettes={this.props.palettes}/>
                </div>
                <div className="wrap_ wrap_-body">
                    <div>
						<StudioCanvas ref={"studio_canvas"}
                            width={this.props.canvas.width}
                            height={this.props.canvas.height}
                            backgroundPattern={this.state.selectedOptions.backgrounds}
                			graphic={this.state.selectedOptions.graphics}
                            shape={this.state.selectedOptions.shapes}
                            backgroundColor={this.getColors()[0]}
                            graphicColor={this.getColors()[1]}

                		/>                        
                        {detail}
                    </div>

                    <div className="wrap_  wrap_-dark wrap_-borderbottom  l-studio-x-header l-horizontalright">
                        <button onClick={this.handleCancel} className="button_ button_-secondary">Cancel</button>
                        <button onClick={this.handleBadgeComplete} className="button_ ">Save</button>
                    </div>
                </div>
            </form>
        )
    },
});

module.exports = {
    BadgeStudio: BadgeStudio,
}
