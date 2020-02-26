# pre-commit.sh
git stash -q --keep-index
if [ -d env/ ]; then
	. env/bin/activate
fi
./runtests pep8
RESULT=$?
git stash pop -q
[ $RESULT -ne 0 ] && exit 1
exit 0
