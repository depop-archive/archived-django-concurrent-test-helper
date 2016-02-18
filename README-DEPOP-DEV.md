## info for Depop devs

To release a new version of this to PyPI you should use the `depop` PyPI user account.

If you already have your own personal PyPI account you probably have that saved in your `/.pypirc` file.

In order to release to PyPI under a different user you need to:

1. `pip install twine`
2. create a `.pypirc` file in the project root containing the `depop` username and password
3. `rm dist/*` (remove old versions to simplify step 5)
4. `python setup.py sdist`
5. `twine upload --config-file=.pypirc dist/*`
