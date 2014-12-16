var gulp = require('gulp');
var browserify = require('gulp-browserify');  // Bundles JS.
var del = require('del');  // Deletes files.
var reactify = require('reactify');  // Transforms React JSX to JS.
var source = require('vinyl-source-stream');
var sass = require('gulp-sass');
var rename = require('gulp-rename');
var livereload = require('gulp-livereload');
 
// Define some paths.
var sourcePaths = {
  sass: ['./build/sass/style.scss'],
  app_js: ['./build/js/app.jsx']
};
var destPaths = {
  css: './breakdown/static/css',
  js: './breakdown/static/js/'
}

gulp.task('sass', function(){
  gulp.src(sourcePaths.sass)
    .pipe(sass())
    .pipe(gulp.dest(destPaths.css))
    .pipe(livereload());
});
 
// Our JS task. It will Browserify our code and compile React JSX files.
gulp.task('js', function() {
  // Browserify/bundle the JS.
  gulp.src(sourcePaths.app_js)
    .pipe(browserify({
      transform: reactify
    })).
    pipe(rename("script.js"))
    .pipe(gulp.dest(destPaths.js))
    .pipe(livereload());
});
 
// Rerun tasks whenever a file changes.
gulp.task('watch', function() {
  livereload.listen();
  gulp.watch(sourcePaths.sass, ['sass']);
  gulp.watch(sourcePaths.app_js, ['js']);
});
 
// The default task (called when we run `gulp` from cli)
gulp.task('default', ['watch', 'sass', 'js']);