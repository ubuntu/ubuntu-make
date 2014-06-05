# Ubuntu Developer Tools Center

Ubuntu Developer Tools Center is a project to enable quick and easy setup of common developers needs on Ubuntu.

[![Build Status](https://api.travis-ci.org/didrocks/ubuntu-developer-tools-center.svg?branch=master)](https://travis-ci.org/didrocks/ubuntu-developer-tools-center)

As a first step, it's focusing on installing a full fledge android developer environment on latest Ubuntu LTS (14.04).

**/!\ WIP, not ready for consumption yet**

## Running command line tool
To run the tool:

    $ ./developer-tools-center

You can of course use --help to get more information and change the verbosity of the output with -v, -vv.

## Requirements

> Note that this project is using python3 and requires at least python 3.3. All commands (including nosetests) are using the python 3 version. See later on how installing the corresponding virtualenv.

## Different level of logging
Multiple logging profiles are available in *log-confs/* to be able to have different traces of your execution (useful when debugging in particular). For instance, you will find:

* **debug.yaml**: Similar than using -vv, but will put logs to a *debug.log* file.
* **debug_network.yaml**: The root logging level is INFO (-v), the network activities are in DEBUG mode and will be logged in *debug_network.log*.
* **testing.yaml**: Mostly for tests, similar than using -vv, but:
 * DEBUG logs and above are available in *debug.log*.
 * INFO logs and above are available in *info.log*.
 * WARNING and ERROR logs are available in *error.log*.

On normal circumstances, we expect *error.log* to remain empty.

To load one of those logging profile:

    $ LOG_CFG=log-confs/testing.yaml ./developer-tools-center

### Types of tests
There are three kinds of tests:

* small tests: mostly testing modules and component with mocks around it. Note that it's using as well a local webserver (http and https) to serve mock content
* medium tests: testing the whole workflow, directly calling end user tool from the command line, but without any effect on the system. Requirements like installing packages are mocked, as well as the usage of a local webserver serving (smaller) content similar that what will be fetched in a real use case. The assets have the same formats and layout.
* large tests: same tests are run than for the medium tests, but with real server download and installation of dpkg packages. Most of those tests needs root rights. However, be aware than those tests only run on a graphical environment, will interfere with it and will install/remove packages on your system.

To run all those tests:

    $ nosetests

### Running some tests with all debug infos
By default, nose won't display debug output of the passing tests. When you want or work on some tests and want to see full debug log, you can use this existing node profile:

    $ nosetests -c log-confs/debug_test.cfg tests.small.test_download_center:TestDownloadCenter.test_multiple_with_one_404_url

## Create your own environment and run from it
In the project root directory (env/ is already in .gitignore):

    $ virtualenv --python=python3 env
    $ env/bin/pip install -r requirements.txt
    $ source env/bin/activate
    $ ./developer-tools-center

## Development

### Style guide and checking

We are running pep8 relaxing in .pep8 the max line length to 120. env/ is excluded as well from the pep8 check.

Running the tests, in particular:

    $ nosetests test/__init__.py

is running those pep8 checks on the code.

You can run as well the pep8 tool directly from the project directory:

    $ pep8 .

