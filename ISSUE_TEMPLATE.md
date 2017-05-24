Make sure you try the following before submitting the issue, thank you!

- Check that umake is the latest version (https://github.com/ubuntu/ubuntu-make/releases)
- If you're not running the latest development version of Ubuntu, or a flavor based on it, add the ppa as described in the README.

Maybe the bug is fixed in the master branch? If you have all dependencies installed, you can run `umake` easily from it:

```
$ git clone https://github.com/ubuntu/ubuntu-make
$ cd ubuntu-make
$ bin/umake <your-command>
```

If all this doesn't solve the problem you're having, please submit the issue including the version of ubuntu and umake itself.
