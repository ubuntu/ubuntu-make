# Ubuntu Make
Ubuntu Make is a project designed to enable quick and easy setup of common needs for developers on Ubuntu.

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/ubuntu-make)

## Current project health

[![Build Status](https://github.com/ubuntu/ubuntu-make/workflows/style_test/badge.svg?branch=master)](https://github.com/ubuntu/ubuntu-make/actions?workflow=style_test) (pep8 and small tests)

[![Snap Status](https://build.snapcraft.io/badge/ubuntu/ubuntu-make.svg)](https://build.snapcraft.io/user/ubuntu/ubuntu-make)

[![Translation status](https://hosted.weblate.org/widgets/ubuntu-make/-/svg-badge.svg)](https://hosted.weblate.org/engage/ubuntu-make/?utm_source=widget)

## Installing
### SNAP
We recommend to use the Ubuntu Make snap to ensure you always have the latest and greatest version, even on older supported releases.

```sh
$ snap install ubuntu-make --classic
```

If installed via the snap it can be run as `ubuntu-make.umake`, or via the alias `umake`

Ubuntu Make interacts heavily with the system, in particular with the apt database. Confined or devmode snaps aren’t able to do that. 

Transitioning to a classic snap gives us the same power than a debian package on this regard, while still enabling for a smoother transition.

More information on this confined snap is available at https://didrocks.fr/2017/07/05/ubuntu-make-as-a-classic-snap-intro/

### PPA
There is also a daily built ppa:

```
sudo add-apt-repository ppa:lyzardking/ubuntu-make
sudo apt-get update
sudo apt-get install ubuntu-make
```

## Listing

Umake has three listing options:
- `--list` to show all the frameworks
- `--list-available` to show the available frameworks
- `--list-installed` to show the installed frameworks

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

You can also run the pycodestyle or pep8 tool directly from the project directory:

```sh
$ pycodestyle/pep8 .
```

### Tests
#### Types of tests
There are four types of tests that can be combined in runtests:

* **pep8**: Run the pep8 tests on all the umake and test code.
* **small**: Tests modules and components with mock content around them. Note that this uses a local webserver (http and https) to serve mock content.
* **medium**: Tests the whole workflow. It directly calls end user tools from the command line, but without affecting the local system. Requirements like installing packages are mocked, as well as the usage of a local webserver serving (smaller) content similar to what will be fetched in a real use case. The assets have the same formats and layout.
* **large**: Runs the same tests as the medium test, but with real server downloads and installation of dpkg packages. Most of these tests need root privileges. Be aware that these tests only run on a graphical environment. It will interfere with it and it is likely to install or remove packages on your system.

To run all the tests, with coverage report:

```sh
$ ./runtests
```

#### Running some tests with all debug info
By default, **runtests** will not display any debug output if the tests are successful, similar to pytest. However, if only  tests are selected, runtests will a display full debug log,

```sh
$  ./runtests tests/small/test_tools.py::TestConfigHandler
```

#### More information on runtests
**runtests** is a small pytest wrapper used to simplify the testing process. By default, if no arguments are supplied, runtests will run all available tests on the project using the production nose configuration.
It is possible to run only some types of tests:

```sh
$ ./runtests small medium
```

This will only run small and medium tests, with all pytest defaults (no profile is selected).

Finally, you can run a selection of one or more tests:

```sh
$ ./runtests tests/small/test_tools.py::TestConfigHandler
```

You can activate/disable/change any of those default selected configurations with **--config/--coverage/--debug/** (see `runtests --help` for more information)

#### Check for Python warnings:

**runtests** is compatible with showing the Python warnings:

```sh
$ PYTHONWARNINGS=d ./runtests
```

### Create your own environment and run from it
For an easier development workflow, we encourage the use of virtualenv to test and iterate on the project rather than installing all the requirements on your machine. In the project root directory run (env/ is already in .gitignore and excluded from pep8 checking):

```sh
$ virtualenv --python=python3 --system-site-packages env
$ sudo apt-get install -qq python3-apt # use the system version of python apt
$ sudo apt-get install -qq python3-gi # not installable with pypi
$ sudo apt-get install -qq bzr python3-dev # requires for pip install -r
$ env/bin/pip install -r requirements.txt
$ source env/bin/activate
$ bin/umake
```

### Developing using system package

Instead of using a virtual environment, you can install system packages to be able to run the Ubuntu Make tests. The build dependencies are listed in *debian/control* and should be available in recent Ubuntu versions.

## Release management
Refresh .pot files:

```sh
$ ./setup.py update_pot
```
