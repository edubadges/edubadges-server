var browserSync = require("browser-sync");

module.exports = function(grunt) {

    grunt.initConfig({

        srcPath: 'build/', // Any directories between your Gruntfile.js and your source
        destPath: 'breakdown/static/', // Any directories between your Gruntfile.js and your destination
        
        pkg: grunt.file.readJSON('package.json'),

        env: {
            dist: {
                NODE_ENV: 'production'
            }
        },

        watch: {
            options: {
                spawn: false,
                livereload: true
            },
            scss: {
                files: '<%= srcPath %>**/*.scss',
                tasks: ['sass', 'autoprefixer', 'bs-inject']
            },
            staticFiles: {
                files: ['**/*.html'],
                tasks: ['bs-inject']
            },
            browserify: {
                files: [
                    '<%= srcPath %>js/*.jsx',
                    '<%= srcPath %>*.js',
                    '<%= srcPath %>*.html',
                    '<%= srcPath %>js/**/*.jsx',
                    '<%= srcPath %>js/**/*.js',
                    '<%= srcPath %>pattern-library.html',
                    '<%= srcPath %>js/component-library.jsx'
                ],
                tasks: ['browserify:dev', 'bs-inject']
            }
        },

        browserify: {
            dev: {
                options: {
                    debug: true,
                    transform: ['reactify']
                },
                files: {
                    'breakdown/static/js/app.js': 'build/js/app.jsx',
                    'breakdown/static/js/lti-app.js': 'build/js/lti-app.jsx',
                    'breakdown/static/js/component-library.js': 'build/js/component-library.jsx'
                }
            },
            dist: {
                options: {
                    debug: false,
                    transform: ['reactify']
                },
                files: {
                    'build/js/temp/app.js': 'build/js/app.jsx',
                    'build/js/temp/lti-app.js': 'build/js/lti-app.jsx',
                    'breakdown/static/js/component-library.js': 'build/js/component-library.jsx'
                }
            }
        },

        uglify: {
            options: {
                sourceMap: false,
                compress: true,
                report: ['min', 'gzip'],
                preserveComments: 'some',
                screw_ie8: true
            },
            dist: {
                files: {
                    'breakdown/static/js/app.js': ['build/js/temp/app.js'],
                    'breakdown/static/js/lti-app.js': ['build/js/temp/lti-app.js']
                }
            }
        },

        sass: {
            dist: {
                options: {
                    style: 'nested'
                }, 
                files: [{
                    expand: true,
                    cwd: '<%= srcPath %>scss',
                    src: ['*.scss', '!_*.scss'],
                    dest: '<%= destPath %>css',
                    ext: '.css'
                },
                {
                    expand: true,
                    cwd: '<%= srcPath %>scss/legacy',
                    src: ['*.scss', '!_*.scss'],
                    dest: '<%= destPath %>css',
                    ext: '.css'
                }]
            }
        },

        autoprefixer: {
            dist: {
                src: '<%= destPath %>css/screen.css'
            },
            options: {
                map: true
            }
        }

    });

    grunt.registerTask("bs-init", function () {
        var done = this.async();
        browserSync({
            proxy: 'localhost:8000' // This needs to match your current server eg. localhost:5000 or mysite.design.concentricsky.com
        }, function (err, bs) {
            done();
        });
    });

    grunt.registerTask("bs-inject", function () {
        browserSync.reload(['**/*.html','**/*.css']);
    });

    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-browserify');
    grunt.loadNpmTasks('grunt-env');
    grunt.loadNpmTasks('grunt-shell-spawn');
    grunt.loadNpmTasks('grunt-inline');

    grunt.registerTask('default',['bs-init', 'sass', 'autoprefixer', 'browserify:dev', 'watch']);
    grunt.registerTask('dist', ['env:dist', 'sass', 'autoprefixer', 'browserify:dist', 'uglify']);
};
