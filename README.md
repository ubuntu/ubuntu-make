# Ubuntu Developer Tools Center
Ubuntu Developer Tools Center is a project to enable quick and easy setup of common developers needs on Ubuntu.

<!---[![Build Status](https://api.travis-ci.org/didrocks/ubuntu-developer-tools-center.svg?branch=master)](https://travis-ci.org/didrocks/ubuntu-developer-tools-center) TRAVIS disabled until they support 14.04 (need python 3.4 with platform gi.repository)-->

As a first step, it's focusing on installing a full fledge android developer environment on latest Ubuntu LTS (14.04).

**/!\ WIP, not ready for consumption yet**

## Running command line tool
To run the tool:

    $ ./developer-tools-center

You can of course use --help to get more information and change the verbosity of the output with -v, -vv.

## Requirements

> Note that this project is using python3 and requires at least python 3.3. All commands are using the python 3 version. See later on how installing the corresponding virtualenv.


## Shell completion

To enable shell completion on bash or zsh, just run:

    $ . enable_completion

## Different level of logging

Multiple logging profiles are available in *confs/* to be able to have different traces of your execution (useful when debugging in particular). For instance, you will find:

* **debug.logcfg**: Similar than using -vv, but will put logs to a *debug.log*.
* **debug_network.logcfg**: The root logging level is INFO (-v), the network activities are in DEBUG mode and will be logged in *debug_network.log*.
* **testing.logcfg**: Mostly for tests, similar than using -vv, but:
 * DEBUG logs and above are available in *debug.log*.
 * INFO logs and above are available in *info.log*.
 * WARNING and ERROR logs are available in *error.log*.

On normal circumstances, we expect *error.log* to remain empty.

To load one of those logging profile:

    $ LOG_CFG=confs/testing.logcfg ./developer-tools-center

## Development
### Style guide and checking
We are running pep8 relaxing in .pep8 the max line length to 120. env/ is excluded as well from the pep8 check.

Running this tests, in particular:

    $ ./runtests pep8

is running those pep8 checks on the code.

You can run as well the pep8 tool directly from the project directory:

    $ pep8 .

### Tests
#### Types of tests
There are four kinds of tests that can be combined in runtests:

* **pep8**: Run the pep8 tests on all the udtc and tests code.
* **small**: mostly testing modules and component with mocks around it. Note that it's using as well a local webserver (http and https) to serve mock content
* **medium**: testing the whole workflow, directly calling end user tool from the command line, but without any effect on the system. Requirements like installing packages are mocked, as well as the usage of a local webserver serving (smaller) content similar that what will be fetched in a real use case. The assets have the same formats and layout.
* **large**: same tests are run than for the medium tests, but with real server download and installation of dpkg packages. Most of those tests needs root rights. However, be aware than those tests only run on a graphical environment, will interfere with it and will install/remove packages on your system.

To run all those tests, with coverage report (like in Travis CI):

    $ ./runtests
    
You can use --no-config to disable the coverage report selection.

#### Running some tests with all debug infos
By default, **runtests** will not display any debug output of the passing tests like in nose. However, if you select only some tests to run manually, runtests will then switch
to display full debug log,

    $  ./runtests tests/small/test_tools.py:TestConfigHandler

You can use --no-config to disable the debug output selection.

#### More information on runtests
**runtests** is a small nose wrapper used to ease the run of tests. By default runtests withtout any argument or with "all" will run all available tests on the projects, using the production nose config.
You can run as well only some test types if wanted:

    $ ./runtests small medium
    
This will only run small and medium tests, with all nose defaults (no profile is selected).

Finally, you can run, as seen in the previous paragraph, a selection of one or more tests:

    $ ./runtests tests/small/test_tools.py:TestConfigHandler
    
This enables by default the debug profile to display all outputs and logging information (in debug level).

You can active/disable/change any of those default selected configuration with **--config/--coverage/--debug/--no-config** (see runtests --help for more information)

#### Nose configurations

Some nose configurations are available in **confs/**. You will find:

* **debug.nose**: this profile shows all outputs and logging information while turning debug logging.
* **prod.nose**: this profile keep all outputs captured, but display tests coverage results.

#### Check for python warnings:

**runtests** is compatible with showing the python warnings:

     $ PYTHONWARNINGS=d ./runtests

### Create your own environment and run from it
For an easier development workflow, we encourage the use of virtualenv to test and iterate on the project in contrast of installing all requirements on your machine. In the project root directory (env/ is already in .gitignore and excluded for pep8 checking):

    $ virtualenv --python=python3 --system-site-packages env
    $ sudo apt-get install -qq apt apt-utils libapt-pkg-dev # those are the requirements to compile python-apt
    $ sudo apt-get install -qq python3-progressbar python3-gi
    $ env/bin/pip install -r requirements.txt
    $ source env/bin/activate
    $ ./developer-tools-center

## Release management
Refresh .pot files:

   $ ./setup.py extract_messages --output po/ubuntu-developer-tools-center.pot

