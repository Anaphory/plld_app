from clldutils.path import Path
from clld.web.assets import environment

import plld_app


environment.append_path(
    Path(plld_app.__file__).parent.joinpath('static').as_posix(),
    url='/plld_app:static/')
environment.load_path = list(reversed(environment.load_path))
