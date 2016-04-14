/**
 * Copyright Kitware Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* global module, require */

module.exports = function (grunt) {
  var path = require('path');

  var defaultTasks = [
    'build-default'
  ];

  // Pass a "--env=<value>" argument to grunt. Default value is "dev".
  var environment = grunt.option('env') || 'dev';

  // Returns a json string containing information from the current git repository.
  var versionInfoObject = function () {
    var gitVersion = grunt.config.get('gitinfo');
    var local = gitVersion.local || {};
    var branch = local.branch || {};
    var current = branch.current || {};
    return JSON.stringify(
      {
        git: !!current.SHA,
        SHA: current.SHA,
        shortSHA: current.shortSHA,
        date: grunt.template.date(new Date(), 'isoDateTime', true),
        apiVersion: grunt.config.get('pkg').version,
        describe: gitVersionObject
      },
      null,
      '  '
    );
  };

  /* Ideally, we would add version information for each library we use to
   * this object. */
  var libVersionInfoObject = function () {
    return JSON.stringify({
      date: grunt.template.date(new Date(), 'isoDateTime', true)
    }, null, '  ');
  };
  var gitVersionObject;

  // Project configuration.
  grunt.config.init({
    pkg: grunt.file.readJSON('package.json'),

    clean: {
      libs: [
        'built/entity-version.js',
        'built/entitylib-version.js',
        'built/googlefonts.css',
        'built/templates.js'
      ]
    },

    copy: {
      static: {
        expand: true,
        cwd: 'client/static',
        src: ['**/*'],
        dest: 'built'
      },
      libs: {
        files: [{
          expand: true,
          cwd: 'node_modules/bootstrap/dist/fonts',
          src: ['**/*'],
          dest: 'built/fonts'
        }, {
          expand: true,
          cwd: 'node_modules/jquery-ui-bundle/images',
          src: ['**/*'],
          dest: 'built/libs/images'
        }, {
          expand: true,
          cwd: 'node_modules/font-awesome/fonts',
          src: ['**/*'],
          dest: 'built/fonts'
        }]
      }
    },

    cssmin: {
      options: {
        sourceMap: environment === 'dev'
      },
      libs: {
        files: {
          'built/libs/libs.min.css': [
            'node_modules/bootstrap/dist/css/bootstrap.css',
            'node_modules/jquery-ui-bundle/jquery-ui.css',
            'node_modules/font-awesome/css/font-awesome.css',
            'node_modules/LineUpJS/css/style.css',
            'node_modules/LineUpJS/demo/css/style-demo.css',
            'node_modules/bootstrap-table/dist/bootstrap-table.css',
            'built/googlefonts.css'
          ]
        }
      }
    },

    'curl-dir': {
      libs: {
        src: [
          'https://raw.githubusercontent.com/draperlaboratory/user-ale/master/userale.js',
          'https://raw.githubusercontent.com/draperlaboratory/user-ale/master/userale-worker.js'
        ],
        dest: 'built/userale'
      }
    },

    jade: {
      options: {
        client: true,
        compileDebug: false,
        namespace: 'entityApp.templates',
        processName: function (filename) {
          return path.basename(filename, '.jade');
        }
      },
      core: {
        files: {
          'built/templates.js': [
            'client/templates/**/*.jade'
          ]
        }
      }
    },

    shell: {
      getgitversion: {
        command: 'git describe --always --long --dirty --all',
        options: {
          callback: function (ignore_err, stdout, stderr, callback) {
            gitVersionObject = stdout.replace(/^\s+|\s+$/g, '');
            callback();
          }
        }
      },
      googlefonts: {
        command: 'node node_modules/google-fonts-offline/bin/goofoffline outDir=built/libs outCss=../googlefonts.css \'http://fonts.googleapis.com/css?family=Lato:400,700\''
      },
      npmlibs: {
        command: [
          'cd node_modules/Clique',
          'npm install',
          'npm run build',
          'cd ../candela',
          'npm install',
          'npm run dist'
        ].join(' && ')
      }
    },

    symlink: {
      options: {
        overwrite: true
      },
      app: {
        files: [{
          expand: true,
          overwrite: true,
          cwd: 'client',
          src: ['*.js', '*.css', '*.html'],
          dest: 'built'
        }, {
          src: 'service',
          dest: 'built/service'
        }, {
          src: 'defaults.json',
          dest: 'built/defaults.json'
        }, {  /* DWM:: */
          src: 'cache',
          dest: 'built/cache'
        }, {
          src: 'lineup_js',
          dest: 'built/lineup_js'
        }]
      }
    },

    uglify: {
      options: {
        sourceMap: environment === 'dev',
        sourceMapIncludeSources: true,
        report: 'min',
        beautify: {
          ascii_only: true
        }
      },
      app: {
        files: {
          'built/app.min.js': [
            'built/entity-version.js',
            'built/templates.js'
          ]
        }
      },
      libs: {
        files: {
          'built/libs/libs.min.js': [
            'node_modules/jquery/dist/jquery.js',
            'node_modules/jquery-ui-bundle/jquery-ui.js',
            'node_modules/d3/d3.js',
            'node_modules/underscore/underscore.js',
            'node_modules/backbone/backbone.js',
            'node_modules/bootstrap/dist/js/bootstrap.js',
            'node_modules/bootstrap-table/dist/bootstrap-table.js',
            //'node_modules/LineUpJS/libs/d3.js',
            'node_modules/LineUpJS/dist/LineUpJS.js',
            // 'node_modules/jade/runtime.js',
            'built/entitylib-version.js'
          ]
        }
      },
      npmlibs: {
        files: {
          'built/libs/libs-additional.min.js': [
            'node_modules/Clique/dist/clique.js',
            'node_modules/candela/dist/candela.js'
          ]
        }
      }
    },

    'file-creator': {
      app: {
        'built/entity-version.js': function (fs, fd, done) {
          var entityVersion = versionInfoObject();
          fs.writeSync(
            fd,
            [
              '/* global entity: true */',
              '/* jshint ignore: start */',
              '//jscs:disable',
              'window.versionInfo = ',
              entityVersion,
              ';',
              'window.versionInfo.libVersion = libVersionInfo;',
              '/* jshint ignore: end */',
              '//jscs:enable\n'
            ].join('\n')
          );
          done();
        }
      },
      libs: {
        'built/entitylib-version.js': function (fs, fd, done) {
          var entityLibVersion = libVersionInfoObject();
          fs.writeSync(
            fd,
            [
              '/* global entity: true */',
              '/* jshint ignore: start */',
              '//jscs:disable',
              'window.libVersionInfo = ',
              entityLibVersion,
              ';',
              '/* jshint ignore: end */',
              '//jscs:enable\n'
            ].join('\n')
          );
          done();
        }
      }
    }
  });

  if (['dev', 'prod'].indexOf(environment) === -1) {
    grunt.fatal('The "env" argument must be either "dev" or "prod".');
  }

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-compress');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-jade');
  grunt.loadNpmTasks('grunt-contrib-symlink');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-curl');
  grunt.loadNpmTasks('grunt-file-creator');
  grunt.loadNpmTasks('grunt-gitinfo');
  grunt.loadNpmTasks('grunt-shell');
  grunt.loadNpmTasks('grunt-string-replace');

  grunt.registerTask('version-info', [
    'gitinfo',
    'shell:getgitversion',
    'file-creator:app'
  ]);

  grunt.registerTask('libversion-info', [
    'file-creator:libs'
  ]);

  grunt.registerTask('npmlibs', [
    'shell:npmlibs',
    'uglify:npmlibs'
  ]);

  grunt.registerTask('build-default', [
    'jade',
    'version-info',
    'uglify:app',
    'copy:static',
    'symlink:app'
  ]);
  grunt.registerTask('init', [
    'libversion-info',
    'shell:googlefonts',
    'uglify:libs',
    'cssmin:libs',
    'copy:libs',
    'curl-dir:libs',
    'clean:libs'
  ]);
  grunt.registerTask('default', defaultTasks);
};
