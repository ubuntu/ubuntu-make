# Ubuntu Make
Ubuntu Make is a project to enable quick and easy setup of common developers needs on Ubuntu.

<!---[![Build Status](https://api.travis-ci.org/didrocks/ubuntu-make.svg?branch=master)](https://travis-ci.org/didrocks/ubuntu-make) TRAVIS disabled until they support 14.04 (need python 3.4 with platform gi.repository)-->

As a first step, it's focusing on installing a full-fledged android developer environment on latest Ubuntu LTS (14.04).

**/!\ WIP, not ready for consumption yet**

## Running command line tool
To run the tool:

```sh
$ ./umake
```

You can of course use `--help` to get more information and change the verbosity of the output with `-v`, `-vv`.

## Requirements

> Note that this project is using python3 and requires at least python 3.3. All commands are using the python 3 version. See later on how to install the corresponding virtualenv.


## Shell completion

To enable shell completion on bash or zsh, just run:

```sh
$ . enable_completion
```

## Different level of logging

Multiple logging profiles are available in *confs/* to be able to have different traces of your execution (useful when debugging in particular). For instance, you will find:

* **debug.logcfg**: Similar than using -vv, but will also put logs to a *debug.log*.
* **debug_network.logcfg**: The root logging level is INFO (-v), the network activities are in DEBUG mode and will be logged in *debug_network.log*.
* **testing.logcfg**: Mostly for coverage tests, do not set any logging config on stdout, but:
 * DEBUG logs and above are available in *debug.log*.
 * INFO logs and above are available in *info.log*.
 * WARNING and ERROR logs are available in *error.log*.

Under normal circumstances, we expect *error.log* to remain empty../

To load one of those logging profiles:

```sh
$ LOG_CFG=confs/debug.logcfg bin/umake
```

## Development
### Providing user's framework

It's possible for anyone to have local frameworks for either development purpose or for special local or team use-case.
* Any files in a directory set with the "UMAKE_FRAMEWORKS" environment variable will be loaded first.
* Any files inside ~/.umake/frameworks will be loaded next.

Any file should eventually contain a category or frameworks like the ones in umake/frameworks/*.

If categories name are duplicated only one will be loaded. Ubuntu Make will first load the one controlled by the environment variable, then in home based directory, and finally, the system one.
Note that duplicate filenames aren't encouraged, but supported.


### Style guide and checking
We are running pep8 relaxing in .pep8 the max line length to 120. env/ is excluded from the pep8 check as well.

Running this test, in particular:

```sh
$ ./runtests pep8
```

will run those pep8 checks on the code.

You can also run the pep8 tool directly from the project directory:

```sh
$ pep8 .
```

### Tests
#### Types of tests
There are four kinds of tests that can be combined in runtests:

* **pep8**: Run the pep8 tests on all the umake and tests code.
* **small**: mostly testing modules and component with mocks around it. Note that it's using a local webserver (http and https) to serve mock content
* **medium**: testing the whole workflow, directly calling end user tool from the command line, but without any effect on the system. Requirements like installing packages are mocked, as well as the usage of a local webserver serving (smaller) content similar that what will be fetched in a real use case. The assets have the same formats and layout.
* **large**: same tests are run as for the medium tests, but with real server download and installation of dpkg packages. Most of those tests need root rights. However, be aware that those tests only run on a graphical environment, will interfere with it and will install/remove packages on your system.

To run all those tests, with coverage report (like in Travis CI):

```sh
$ ./runtests
```

You can use `--no-config` to disable the coverage report selection.

#### Running some tests with all debug infos
By default, **runtests** will not display any debug output of the passing tests like in nose. However, if you select only some tests to run manually, runtests will then switch to display full debug log,

```sh
$  ./runtests tests/small/test_tools.py:TestConfigHandler
```

You can use `--no-config` to disable the debug output selection.

#### More information on runtests
**runtests** is a small nose wrapper used to ease the run of tests. By default runtests without any argument or with "all" will run all available tests on the projects, using the production nose config.
You can also run only some test types if wanted:

```sh
$ ./runtests small medium
```

This will only run small and medium tests, with all nose defaults (no profile is selected).

Finally, you can run, as seen in the previous paragraph, a selection of one or more tests:

```sh
$ ./runtests tests/small/test_tools.py:TestConfigHandler
```

This enables the debug profile by default, to display all outputs and logging information (in debug level).

You can activate/disable/change any of those default selected configurations with **--config/--coverage/--debug/--no-config** (see `runtests --help` for more information)

#### Nose configurations

Some nose configurations are available in **confs/**. You will find:

* **debug.nose**: this profile shows all outputs and logging information while turning debug logging.
* **prod.nose**: this profile keep all outputs captured, but display tests coverage results.

#### Check for python warnings:

**runtests** is compatible with showing the python warnings:

```sh
$ PYTHONWARNINGS=d ./runtests
```

### Create your own environment and run from it
For an easier development workflow, we encourage the use of virtualenv to test and iterate on the project in contrast to installing all requirements on your machine. In the project root directory (env/ is already in .gitignore and excluded from pep8 checking):

```sh
$ virtualenv --python=python3 --system-site-packages env
$ sudo apt-get install -qq apt apt-utils libapt-pkg-dev # those are the requirements to compile python-apt
$ sudo apt-get install -qq python3-progressbar python3-gi python3-argcomplete
$ env/bin/pip install -r requirements.txt
$ source env/bin/activate
$ bin/umake
```

## Release management
Refresh .pot files:

```sh
$ ./setup.py update_pot
```

