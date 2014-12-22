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

var jshint = require('gulp-jshint');
var stylish = require('gulp-jshint');

var uglify = require('gulp-uglify');
var size = require('gulp-size');
//var dateformat = require('dateformat');
// var rename = require('gulp-rename');
// var notify = require('gulp-notify');

// var yargs = require('yargs');
// var IS_PRODUCTION = yargs.argv.env == 'production' ? true : false;


//utility functions:
var logUpdate = function(taskString, duration){
  gutil.log('Updated \'' + clr.cyan(taskString) + '\' after ' + clr.magenta( duration + 'ms'));
}


// Define some paths.
var sourceWatchPaths = {
  css: ['./build/sass/**/*.scss'],
  js: ['./build/js/**/*.jsx', './build/js/**/*.js']
};

var sourceBuildPaths = {
  css: ['./build/sass/style.scss'],
  js: ['./build/js/app.jsx']
}

var destPaths = {
  css: './breakdown/static/css',
  js: './breakdown/static/js/'
}



/** PRODUCTION
 *
 *  Build for production. Run `gulp build` on the server or distribution packager.
 *
**/
gulp.task('build', function(){
  var bundler = browserify({
    entries: ['./build/js/app.jsx'], // Only need initial file, browserify finds the deps
    transform: [reactify], // We want to convert JSX to normal javascript
    debug: true, // Gives us sourcemapping
    cache: {}, packageCache: {}, fullPaths: true // Requirement of watchify
  });

  var jsbundle = bundler.bundle()
    .pipe(source('script.js'))
    .pipe(buffer())
    .pipe(uglify())
    .pipe(size({showFiles:true, gzip:true}))
    .pipe(gulp.dest('./breakdown/static/js/'));

  var cssbundle = gulp.src('./build/sass/**/*.scss')
    .pipe(sass())
    .pipe(concat('style.css'))
    .pipe(size({showFiles:true, gzip:true}))
    .pipe(gulp.dest('./breakdown/static/css/'))
});



/** Development
 *
 *  Watch+compile for production. Run `gulp` for default js/css watching tasks
 *
**/
gulp.task('watchScripts', function() {
  var bundler = browserify({
    entries: ['./build/js/app.jsx'], // Only need initial file, browserify finds the deps
    transform: [reactify], // We want to convert JSX to normal javascript
    debug: true, // Gives us sourcemapping
    cache: {}, packageCache: {}, fullPaths: true // Requirement of watchify
  });
  
  var watcher  = watchify(bundler);

  return watcher
  .on('update', function () { // When any files update
    var updateStart = Date.now();
    watcher.bundle() // Create new bundle that uses the cache for high performance
    .pipe(source('script.js'))
    .pipe(jshint())
    .pipe(jshint.reporter(stylish))
    .pipe(gulp.dest('./breakdown/static/js/'))
    .pipe(livereload());
    logUpdate('watchScripts', Date.now() - updateStart);
  })
  .bundle() // Create the initial bundle when starting the task
  .pipe(source('script.js'))
  .pipe(gulp.dest('./breakdown/static/js/'));
});

// I added this so that you see how to run two watch tasks
gulp.task('css', function () {
  gulp.watch('./build/sass/**/*.scss', function () {
    var updateStart = Date.now();
    var result = gulp.src('./build/sass/**/*.scss')
    .pipe(sass())
    .pipe(concat('style.css'))
    .pipe(gulp.dest('./breakdown/static/css/')).
    pipe(livereload());
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


