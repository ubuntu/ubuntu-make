# Ubuntu Make
Ubuntu Make is a project designed to enable quick and easy setup of common needs for developers on Ubuntu.

## Current project health
[![Build Status](https://api.travis-ci.org/ubuntu/ubuntu-make.svg?branch=master)](https://travis-ci.org/ubuntu/ubuntu-make) (pep8 and small tests)

[All test results](https://jenkins.qa.ubuntu.com/job/udtc-trusty-tests/) and [Coverage report](https://jenkins.qa.ubuntu.com/job/udtc-trusty-tests-collect/label=ps-trusty-desktop-amd64-1/lastSuccessfulBuild/artifact/html-coverage/index.html)

## Installing
We recommend to use the Ubuntu Make ppa to ensure you always have the latest and greatest version, even on older supported released. We are available on the currenctly supported Ubuntu version.

```sh
$ sudo add-apt-repository ppa:ubuntu-desktop/ubuntu-make
$ sudo apt update
$ sudo apt install ubuntu-make
```

## Running the command line tool
To run the tool:

```sh
$ ./umake
```

You can use `--help` to get more information and change the verbosity of the output with `-v`, `-vv`.

## Requirements

> Note that this project uses python3 and requires at least python 3.3. All commands use the python 3 version. There are directions later on explaining how to install the corresponding virtualenv.


## Shell completion

To enable shell completion on bash or zsh, just run:

```sh
$ . enable_completion
```

## Different level of logging

Multiple logging profiles are available in *confs/* to be able to have different traces of your execution (particularly useful for debugging). For instance, you will find:

* **debug.logcfg**: Similar to using -vv, but also puts logs in a *debug.log*.
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

It's possible for anyone to have local frameworks for either development purposes or for special local or team use-cases.
* Any files in a directory set with the "UMAKE_FRAMEWORKS" environment variable will be loaded first.
* Any files inside ~/.umake/frameworks will be loaded next.

Any file should eventually contain a category or frameworks like the ones in umake/frameworks/*.

If category names are duplicated only one will be loaded. Ubuntu Make will first load the one controlled by the environment variable, then the one located in the home based directory, and finally, the system one.
Note that duplicate filenames are supported but not encouraged.


### Style guide and checking
We are running pep8, but the max line length has been relaxed to 120. env/ is excluded from the pep8 check as well.

Running this test, in particular:

```sh
$ ./runtests pep8
```

This will run those pep8 checks on the code.

You can also run the pep8 tool directly from the project directory:

```sh
$ pep8 .
```

### Tests
#### Types of tests
There are four types of tests that can be combined in runtests:

* **pep8**: Run the pep8 tests on all the umake and test code.
* **small**: Tests modules and components with mock content around them. Note that this uses a local webserver (http and https) to serve mock content.
* **medium**: Tests the whole workflow. It directly calls end user tools from the command line, but without effecting the local system. Requirements like installing packages are mocked, as well as the usage of a local webserver serving (smaller) content similar to what will be fetched in a real use case. The assets have the same formats and layout.
* **large**: Runs the same tests as the medium test, but with real server downloads and installation of dpkg packages. Most of these tests need root privileges. Be aware that these tests only run on a graphical environment. It will interfere with it and it is likely to install or remove packages on your system.

To run all the tests, with coverage report, like in our jenkins infra:

```sh
$ ./runtests
```

Use `--no-config` to disable the coverage report selection.

#### Running some tests with all debug infos
By default, **runtests** will not display any debug output if the tests are successful, similar to Nose. However, if only some tests are selected, runtests will a display full debug log,

```sh
$  ./runtests tests/small/test_tools.py:TestConfigHandler
```

Use `--no-config` to disable the debug output selection.

#### More information on runtests
**runtests** is a small nose wrapper used to simplify the testing process. By default, if no arguments are supplied or if "all" is supplied, runtests will run all available tests on the project using the production nose configuration.
It is possible to run only some types of tests:

```sh
$ ./runtests small medium
```

This will only run small and medium tests, with all nose defaults (no profile is selected).

Finally, you can run a selection of one or more tests:

```sh
$ ./runtests tests/small/test_tools.py:TestConfigHandler
```

This enables the debug profile by default, to display all outputs and logging information (in debug level).

You can activate/disable/change any of those default selected configurations with **--config/--coverage/--debug/--no-config** (see `runtests --help` for more information)

#### Nose configurations

Some nose configurations are available in **confs/**. You will find:

* **debug.nose**: this profile shows all outputs and logging information while turning debug logging on.
* **prod.nose**: this profile keep all outputs captured, but display tests coverage results.

#### Check for python warnings:

**runtests** is compatible with showing the python warnings:

```sh
$ PYTHONWARNINGS=d ./runtests
```

### Create your own environment and run from it
For an easier development workflow, we encourage the use of virtualenv to test and iterate on the project rather than installing all the requirements on your machine. In the project root directory run (env/ is already in .gitignore and excluded from pep8 checking):

```sh
$ virtualenv --python=python3 --system-site-packages env
$ sudo apt-get install -qq apt apt-utils libapt-pkg-dev # those are the requirements to compile python-apt
$ sudo apt-get install -qq python3-gi # not installable with pypi
$ sudo apt-get install -qq bzr python3-dev # requires for pip install -r
$ env/bin/pip install -r requirements.txt
$ source env/bin/activate
$ bin/umake
```

### Developing using system package

Instead of using a virtual environment, you can install system packages to be able to run the Ubuntu Make tests. The build dependencies are listed in *debian/control* and should be available in latest development ubuntu version. If you are using the latest LTS, you should find them in a dedicated [Ubuntu Make Build-dep ppa](https://launchpad.net/~ubuntu-desktop/+archive/ubuntu/ubuntu-make-builddeps).

## Release management
Refresh .pot files:

```sh
$ ./setup.py update_pot
```
