var browserSync = require("browser-sync");

module.exports = function(grunt) {

	grunt.initConfig({

		path: 'static/', // These needs to match any folders between your Gruntfile.js and your scss or css folders eg. static/
        srcPath: 'build/', // Path to source files

		pkg: grunt.file.readJSON('package.json'),

		watch: {
			options: {
				spawn: false
			},
			scss: {
				files: '<%= srcPath %>scss/**/*.scss',
				tasks: ['sass', 'autoprefixer', 'bs-inject']
			},
            css: {
				files: '<%= path %>css/*.css',
				tasks: ['bs-inject']
            },
			staticFiles: {
				files: ['**/*.html','**/*.php'],
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
					dest: '<%= path %>css',
					ext: '.css'
				}]
			}
		},

		autoprefixer: {
			dist: {
				src: '<%= path %>css/screen.css'
			},
			options: {
				map: true
			}
		},

		shell: {
			breakdown: {
				command: 'breakdown',
				options: {
					stdout: true,
					stderr: true,
					failOnError: true,
					async: true
				}
			}
		},

        requirejs: {
          compile: {
            options: {
                logLevel: 1,
                baseUrl: 'src/js',

                name: 'lib/almond',
                include: 'app/main',
                wrap: true,

                optimize: 'uglify2',
                generateSourceMaps: true,

                out: 'static/js/compiled.js',
                findNestedDependencies: true,
                removeCombined: true,
                preserveLicenseComments: false,
                paths: {
                    'jquery': 'lib/jquery-1.10.2',
                    'jquery-ui': 'lib/jquery-ui-1.10.4',
                    'jquery-countdown': 'lib/jquery.countdown',
                    'jquery-djangoAjaxSetup': 'util/djangoAjaxSetup.jquery',
                    'ladda': 'lib/ladda.min',
                    'spin': 'lib/spin.min',
                    'modernizr': 'lib/modernizr.2.7.1.min',
                    'jbox': '../bower_components/jbox/Source/jBox.min',

                    'jquery-serializeObject': 'plugins/serializeObject.jquery',

                    "JSXTransformer": "lib/JSXTransformer",
                    "jsx": "lib/require.jsx",
                    "text": "lib/require.text",
                    "domReady": "../bower_components/requirejs-domready/domReady",

                    'react': '../bower_components/react/react-with-addons.min',
                    'react-dnd': 'lib/ReactDND.min',
                    'events': 'lib/events',
                    'object-assign': 'lib/object-assign',

                    'loadMore': 'util/loadMore',
                    'takeTestModal': 'util/takeTestModal',
                    'utils': 'util/utils',
                    'Constants': 'util/Constants',
                    'nativeModals': 'util/nativeModals',
                    'ajaxForms': 'util/ajaxForms',
                    'tabs': 'util/tabs',

                    'BaseAction': 'app/actions/abstract/BaseAction',
                    'ShowInSidebarAction': 'app/actions/ShowInSidebarAction',
                    'UpdateAssignmentStatusAction': 'app/actions/UpdateAssignmentStatusAction',
                    'ViewAssessmentResultsAction': 'app/actions/ViewAssessmentResultsAction',
                    'PopulateTakeTestModalAction': 'app/actions/PopulateTakeTestModalAction',
                    'ScrollIntoViewAction': 'app/actions/ScrollIntoViewAction',
                    'CreateTeacherNoteAction': 'app/actions/CreateTeacherNoteAction',

                    'teacherClassList': 'pages/teacherClassList',
                    'teacherTopicDetail': 'pages/teacherTopicDetail',
                    'teacherStudentDetail': 'pages/teacherStudentDetail',

                    'assignedTestSidebar': 'app/assignedTestSidebar',
                    'TeacherNote': 'app/components/TeacherNote',
                    'TeacherNoteList': 'app/components/TeacherNoteList',
                    'TeacherNoteForm': 'app/components/TeacherNoteForm',

                    'AssignmentBoard': 'app/components/AssignmentBoard',
                    'InterimCapabilityAssignmentAccordion': 'app/components/InterimCapabilityAssignmentAccordion',
                    'TargetCapabilityAssignmentWidget': 'app/components/TargetCapabilityAssignmentWidget',
                    'StudentProgressComponents': 'app/components/StudentProgressComponents',
                    'AssignmentActionMenu': 'app/components/AssignmentActionMenu',
                    'FavoriteComponents': 'app/components/FavoriteComponents',
                    'ActiveStudentGroupDropdown': 'app/components/ActiveStudentGroupDropdown',
                    'Tooltip': 'app/components/Tooltip',

                    'models': 'app/models',
                    'stores': 'app/stores',
                    'actions': 'app/actions',

                    'BaseStore': 'app/stores/abstract/BaseStore',
                    'ReadOnlyStore': 'app/stores/abstract/ReadOnlyStore',
                    'LocalStore': 'app/stores/abstract/LocalStore',
                    'AssignmentStatusStore': 'app/stores/AssignmentStatusStore',
                    'StudentStore': 'app/stores/StudentStore',
                    'AssignedTestStore': 'app/stores/AssignedTestStore',
                    'CurriculumStore': 'app/stores/CurriculumStore',
                    'CurrentUserStore': 'app/stores/CurrentUserStore',
                    'StudentGroupStore': 'app/stores/StudentGroupStore',
                    'FavoriteCourseStore': 'app/stores/FavoriteCourseStore',
                    'TeacherNoteStore': 'app/stores/TeacherNoteStore'

                },
                shim: {
                    'jquery-serializeObject': {
                        deps: ['jquery']
                    },
                    'jbox': {
                        deps: ['jquery']
                    },
                    'jquery-ui': {
                        deps: ['jquery']
                    },
                    'modernizr': {
                        exports: 'Modernizr'
                    }
                },
                map: {
                    // '*' means all modules will get 'jquery-djangoAjaxSetup'
                    // for their 'jquery' dependency.
                    '*': { 'jquery': 'jquery-djangoAjaxSetup' },

                    // 'jquery-djangoAjaxSetup' wants the real jQuery module
                    // though. If this line was not here, there would
                    // be an unresolvable cyclic dependency.
                    'jquery-djangoAjaxSetup': { 'jquery': 'jquery' }
                },
                onBuildWrite: function (moduleName, path, singleContents) {
                    return singleContents.replace(/jsx!/g, '');
                }
            }

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

    grunt.loadNpmTasks('grunt-contrib-requirejs');
	grunt.loadNpmTasks('grunt-autoprefixer');
	grunt.loadNpmTasks('grunt-contrib-sass');
	grunt.loadNpmTasks('grunt-contrib-watch');
	grunt.loadNpmTasks('grunt-shell-spawn');
	grunt.registerTask('default',['shell', 'bs-init', 'watch']);
	grunt.registerTask('monitor',['bs-init', 'watch']);

}
