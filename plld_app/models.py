from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin

from clld.db.models.common import Language
from clld import interfaces

#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------
#@implementer(interfaces.ILanguage)
#class plld_appLanguage(CustomModelMixin, Language):
#    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)

@implementer(interfaces.ILanguage)
class Lect(CustomModelMixin, Language):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    region = Column(Unicode)
    family = Column(Unicode)
    language_pk = Column(Integer, ForeignKey('lect.pk'))
    lects = relationship(
        'Lect', foreign_keys=[language_pk], backref=backref('language', remote_side=[pk]))
