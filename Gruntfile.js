var browserSync = require("browser-sync");

module.exports = function(grunt) {

    grunt.initConfig({

        srcPath: 'build/', // Any directories between your Gruntfile.js and your source
        destPath: 'breakdown/static/', // Any directories between your Gruntfile.js and your destination
        
        pkg: grunt.file.readJSON('package.json'),

        watch: {
            options: {
                spawn: false
            },
            scss: {
                files: '<%= srcPath %>**/*.scss',
                tasks: ['sass', 'autoprefixer', 'bs-inject']
            },
            staticFiles: {
                files: ['**/*.html','**/*.php', '**/*.js'],
                tasks: ['bs-inject']
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
        browserSync.reload(['**/*.html','**/*.php','**/*.css']);
    });

    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-shell-spawn');
    grunt.registerTask('default',['bs-init', 'watch']);

}