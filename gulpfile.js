var gulp = require('gulp');
var source = require('vinyl-source-stream'); // Used to stream bundle for further handling
var buffer = require('vinyl-buffer');
var browserify = require('browserify');
var watchify = require('watchify');
var reactify = require('reactify'); 
var concat = require('gulp-concat');
var sass = require('gulp-sass');
var livereload = require('gulp-livereload');

var gutil = require('gulp-util')
var clr = gutil.colors

//var eslint = require('gulp-eslint');
//var eslintJsx = require('eslint-plugin-react');
var uglify = require('gulp-uglify');
var size = require('gulp-size');
//var dateformat = require('dateformat');



// Define some paths.
var sourceWatchPaths = {
  css: ['./build/sass/**/*.scss'],
  js: ['./build/js/**/*.jsx', './build/js/**/*.js']
};

var jsFiles = [
  {
    input      : ['./build/js/app.jsx'],
    output     : 'app.js',
    destination: './breakdown/static/js/'
  },
  {
    input      : ['./build/js/lti-app.jsx'],
    output     : 'lti-app.js',
    destination: './breakdown/static/js/'
  }
];

var destPaths = {
  css: './breakdown/static/css',
  js: './breakdown/static/js/'
};


/** HELPER FUNCTIONS
 *
 *  Reusable task component functions.
 */
var logUpdate = function(taskString, duration){
  gutil.log('Updated \'' + clr.cyan(taskString) + '\' after ' + clr.magenta( duration + 'ms'));
}
var logTheUgly = function(err){
  gutil.log(err);
}


var bundle = function(bundler, fileOptions, config){
  return bundler.bundle()
    .on('error', function(err){console.log(err);})
    .pipe(source(fileOptions.output))
    .pipe(buffer())
    //.pipe(config.production ? uglify().on('error', logTheUgly) : gutil.noop())
    .pipe(size({showFiles: true, gzip: true}))
    .pipe(gulp.dest(fileOptions.destination))
    .pipe(config.watching ? livereload() : gutil.noop());
};


/** PRODUCTION
 *
 *  Build for production. Run `gulp build` on the server or distribution packager.
 *
**/
gulp.task('build', function(){
  var cssbundle = gulp.src('./build/sass/**/*.scss')
    .pipe(sass())
    .pipe(concat('screen.css'))
    .pipe(size({showFiles:true, gzip:true}))
    .pipe(gulp.dest('./breakdown/static/css/'));

  var jsbundles = jsFiles.map(function(entry){
    var bundler = browserify({
      entries: [entry.input], // Only need initial file, browserify finds the deps
      transform: [reactify], // We want to convert JSX to normal javascript
      debug: true, // Gives us sourcemapping
      cache: {}, packageCache: {}, fullPaths: true // Requirement of watchify
    });

    return bundle(bundler, entry, {production: true, watching: false});

  });
});



/** Development
 *
 *  Watch+compile for production. Run `gulp` for default js/css watching tasks
 *
**/
gulp.task('watchScripts', function() {
  var jsbundles = jsFiles.map(function(entry){
    var bundler = browserify({
      entries: [entry.input], // Only need initial file, browserify finds the deps
      transform: [reactify], // We want to convert JSX to normal javascript
      debug: true, // Gives us sourcemapping
      cache: {}, packageCache: {}, fullPaths: true // Requirement of watchify
    });

    bundle(bundler, entry, {production: false, watching: true});

    var watcher  = watchify(bundler);
    return watcher.on('update', function(){
      var updateStart = Date.now();
      bundle(bundler, entry, {production: false, watching: true});
      logUpdate('watchScripts', Date.now() - updateStart);
    });


  });
});

// I added this so that you see how to run two watch tasks
gulp.task('css', function () {
  gulp.watch('./build/sass/**/*.scss', function () {
    var updateStart = Date.now();
    var result = gulp.src('./build/sass/**/*.scss')
    .pipe(sass())
    .pipe(concat('screen.css'))
    .pipe(gulp.dest('./breakdown/static/css/'))
    .pipe(size({showFiles:true, gzip:true}))
    .pipe(livereload());
    logUpdate('css', Date.now() - updateStart);
    return result;
  });
});



// Rerun tasks whenever a file changes.
gulp.task('watch', ['css', 'watchScripts'], function() {
  livereload.listen();
  gulp.watch(sourceWatchPaths.sass, ['css']);
});
 
// The default task (called when we run `gulp` from cli)
gulp.task('default', ['watch']);


