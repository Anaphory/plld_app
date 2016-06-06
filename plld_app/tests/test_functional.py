from clldutils.path import Path
from clld.tests.util import TestWithApp

import plld_app


class Tests(TestWithApp):
    __cfg__ = Path(plld_app.__file__).parent.joinpath('..', 'development.ini').resolve()
    __setup_db__ = False

    def test_home(self):
        res = self.app.get('/', status=200)
