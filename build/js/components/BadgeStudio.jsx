var React = require('react');
var ColorPicker = require('react-color');

var _ = require('lodash');

// Components
var Button = require('../components/Button.jsx').Button;
var StudioCanvas = require('../components/StudioCanvas.jsx').StudioCanvas;


var StudioNavItem = React.createClass({
    render: function() {
        var dataLabel = this.props['data-label'];
        var linkClass = this.props.isActive ? "gallerynav_-x-item gallerynav_-is-active" : "gallerynav_-x-item";
        return (
            <li>
                <a {...this.props} className={linkClass} href={"#tab-"+dataLabel}>
                    <span className={"icon_ icon_-large icon_-"+dataLabel}>{this.props.children}</span>
                </a>
            </li>
        )
    },
});

var StudioOptionList = React.createClass({
    propTypes: {
        tab: React.PropTypes.string.isRequired,
        assets: React.PropTypes.array,
        selected: React.PropTypes.string,
    },

    render: function() {
        var assets;
        if (this.props.assets) {
            assets = this.props.assets.map(function(asset, i) {
                var checked = (this.props.selected == asset);
                if (this.props.palettes[asset]){
                    return (
                        <li key={i} onClick={this.props.onClick} data-label={asset}>
                            <label className={"imageselect_ "+(checked ? "imageselect_-is-checked" : "")} htmlFor="imageselect">
                                <input type="radio" name="imageselect" id="imageselect" value="imageselect" />
                                <span className="imageselect_-x-graphic ">
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
                    img = "None";
                }
                var inset = (this.props.tab == 'graphics' && asset) ? " imageselect_-inset" : "";
                return (
                    <li key={i} onClick={this.props.onClick} data-label={asset}>
                        <label className={"imageselect_ "+(checked ? "imageselect_-is-checked" : "")+inset} htmlFor={asset}>
                            <input type="radio" name="imageselect" value={asset} />
                            <span className="imageselect_-x-graphic ">
                                {img}
                            </span>
                        </label>
                    </li>
                )
            }.bind(this));
        }

        return (
            <section id="tab-shapes">
                <h2 className="wrap_ wrap_-dark wrap_-borderbottom label_ l-studio-x-header">Badges</h2>
                <div className="l-studio-x-list">
                    <style htmlType="text/css">
                        {".flexbox-fix {display: -webkit-box; display: -moz-box; display: -ms-flexbox; display: -webkit-flex; display: flex; }"}
                    </style>
                    <div className="l-studio-x-colorpicker">
                        <ColorPicker type="compact" color={this.props.selectedColor} onChangeComplete={this.props.onColorChange}/>
                    </div>
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
                shapes: [
                'circle.svg', 'hexagon.svg', 'shield.svg', 'diamond.svg', 'shield-1.svg',
                'shape-25.svg', 'shape-27.svg', 'shape-28.svg', 'shape-29.svg', 
                'shape-1.svg', 'shape-2.svg', 'shape-3.svg', 'shape-4.svg', 'shape-5.svg', 'shape-6.svg', 
                'shape-7.svg', 'shape-8.svg', 'shape-9.svg', 'shape-10.svg', 'shape-11.svg', 'shape-12.svg', 
                'shape-13.svg', 'shape-14.svg', 'shape-15.svg', 'shape-16.svg', 'shape-17.svg', 'shape-18.svg', 
                'shape-19.svg', 'shape-20.svg', 'shape-21.svg', 'shape-22.svg', 'shape-23.svg', 'shape-24.svg',
                 ],
                graphics: [undefined,
                    'maple-leaf.png', 'airplane.png', 'approve.png', 'award.png', 'baggage.png', 'battery.png',
                    'beaker.png', 'beer.png', 'bell.png', 'car.png', 'cd.png', 'cinema.png', 'climbing.png',
                    'cocktail-glass.png', 'coffeeshop.png', 'cycling.png', 'factory.png', 'film.png', 'fir-tree.png',
                    'fire-extinguisher.png', 'hiker.png', 'horseback-trail.png', 'hospital-sign.png', 'iphone.png',
                    'keyhole.png', 'light-bulb.png', 'lock.png', 'mental-health.png', 'mushroom.png', 'power.png',
                    'puzzle.png', 'recycle.png', 'ship.png', 'sun.png', 'swimming.png', 'telephone.png',
                    'traffic-cone.png', 'trophy.png', 'umbrella.png', 'white-star.png', 'wireless.png', 'wrench.png', 
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
                shapes: 'circle.svg',
                graphics: undefined,
                colors: 'blue-green',
                backgroundColor: '#0062b1',
                foregroundColor: '#fcdc00'
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
                blob.name = "custombadge.png";
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

        var tab = this.state.activeTab;
        var colorChange = function(color) {
            var selected = this.state.selectedOptions
            if (tab == "shapes") {
                selected['backgroundColor'] = '#'+color.hex
            }
            else if (tab == "graphics") {
                selected['foregroundColor'] = '#'+color.hex
            }
            this.setState({'selectedOptions': this.state.selectedOptions})
        }.bind(this)
        return (
            <form className="l-studio wrap_ wrap_-borderbottom">
                <nav className="wrap_ wrap_-shadow wrap_-dark">
                    <h1 className="wrap_ wrap_-dark wrap_-borderbottom textindent_ l-studio-x-header">Badge Studio</h1>
                    <ul className="gallerynav_">
                        <StudioNavItem
                            onClick={this.handleTabClick}
                            isActive={this.state.activeTab == "shapes"}
                            data-label="shapes">Shapes</StudioNavItem>
                        <StudioNavItem
                            onClick={this.handleTabClick}
                            isActive={this.state.activeTab == "graphics"}
                            data-label="graphics">Graphics</StudioNavItem>
                    </ul>
                </nav>
                <div className="wrap_ wrap_-borderright">
                    <StudioOptionList
                        onClick={this.handleOptionClick}
                        tab={this.state.activeTab}
                        assets={this.props.assets[this.state.activeTab]}
                        palettes={this.props.palettes}
                        selected={this.state.selectedOptions[this.state.activeTab]}
                        onColorChange={colorChange}
                        selectedColor={this.state.activeTab == "shapes" ? this.state.selectedOptions.backgroundColor : this.state.selectedOptions.foregroundColor}
                        />
                </div>
                <div className="wrap_ wrap_-body">
                    <div>
                        <div className="canvas_">
    						<StudioCanvas ref={"studio_canvas"}
                                width={this.props.canvas.width}
                                height={this.props.canvas.height}
                    			graphic={this.state.selectedOptions.graphics}
                                shape={this.state.selectedOptions.shapes}
                                backgroundColor={this.state.selectedOptions.backgroundColor}
                                graphicColor={this.state.selectedOptions.foregroundColor}

                    		/>                        
                        </div>
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
