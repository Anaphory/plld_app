from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common

import plld_app
from plld_app import models


def main(args):
    data = Data()

    dataset = common.Dataset(
        id=plld_app.__name__,
        domain='plld.clld.org',
        description="Database of Papuan Language and Culture",
        )
    DBSession.add(dataset)

    # All ValueSets must be related to a contribution:
    contrib = common.Contribution(id='contrib', name='the contribution')

    # All ValueSets must be related to a Language:
    lang = common.Language(
        id='lang',
        name='A Language',
        latitude=20,
        longitude=20)

    param = common.Parameter(id='param', name='Feature 1')

    # ValueSets group Values related to the same Language, Contribution and 
    # Parameter
    vs = common.ValueSet(id='vs', language=lang, parameter=param, contribution=contrib)

    # Values store the actual "measurements":
    DBSession.add(common.Value(id='v1', name='value 1', valueset=vs))
    DBSession.add(common.Value(id='v2', name='value 2', valueset=vs))

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
