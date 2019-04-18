.PHONY: pypi, tag, test

pypi:
	rm -f dist/*
	python setup.py sdist
	twine upload --config-file=.pypirc dist/*
	make tag

tag:
	git tag $$(python django_concurrent_tests/__about__.py)
	git push --tags

test:
	# assumes Python 2.7 virtualenv with some version of Django installed
	PYTHONPATH=.:testing:testing/tests:testing/tests/py2-dj$$(django-admin --version | tr -d .)_testproject \
	DJANGO_SETTINGS_MODULE=py2-dj$$(django-admin --version | tr -d .)_testproject.settings \
	DJANGO_CONCURRENT_TESTS_TIMEOUT=10 \
	py.test -v -s --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb testing/tests
