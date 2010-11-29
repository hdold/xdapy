"""Contains all classes that possess equivalents as tables in the database. 

Created on Jun 17, 2009
This module contains so called views - classes that are directly mapped onto the 
database through a object-relational-mapper (ORM).
"""
"""
TODO: Figure out what to do with global variable base
TODO: Make Data truncation an error
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


from datetime import date, time, datetime
from pickle import dumps, loads
from sqlalchemy import Sequence, MetaData, Table, Column, ForeignKey, \
    ForeignKeyConstraint, Binary, String, Integer, Float, Date, Time, DateTime, \
    Boolean
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref, validates
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.interfaces import AttributeExtension, MapperExtension, \
    MapperExtension
from sqlalchemy.sql import select, and_
        
base = declarative_base()
        
        
class Data(base):
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
  #  id = Column('id',Integer, Sequence('data_id_seq',1,1), nullable=False,primary_key=True)
    name = Column('name', String(40), primary_key=True)
    data = Column('data', Binary, nullable=False)
    entity_id = Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
    
    __tablename__ = 'data'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    @validates('name')
    def validate_name(self, key, parameter):
        if not isinstance(parameter, str):
            raise TypeError("Argument must be a string")
        return parameter 
    
    def __init__(self, name, data):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of data
        data -- The data to be saved
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        self.name = name
        self.data = data
        
    def __repr__(self):
        return "<%s('%s','%s',%s)>" % (self.__class__.__name__, self.name, self.data, self.entity_id)


class Parameter(base):
    '''
    The class 'Parameter' is mapped on the table 'parameters' and forms the 
    superclass of all possible parameter types (e.g. for string, integer...). 
    The name assigned to a Parameter must be a string.
    Each Parameter is connected to at least one entity through the 
    adjacency list 'parameterlist'. The corresponding entities can be accessed via
    the entities attribute of the Parameter class.
    '''
    id = Column('id', Integer, Sequence('parameter_id_seq'), autoincrement=True, unique=True, primary_key=True)
    name = Column('name', String(40), primary_key=True)
    type = Column('type', String(20), nullable=False)
    
    __tablename__ = 'parameters'
    __table_args__ = {'mysql_engine':'InnoDB'}
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}
    
    @validates('name')
    def validate_name(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise TypeError("Argument must be unicode or string")
            
        return parameter 
    
    def __init__(self, name):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of the parameter
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        self.name = name
    
    def __repr__(self):
        return "<%s(%s,'%s')>" % (self.__class__.__name__, self.id, self.name)


class StringParameter(Parameter):
    '''
    The class 'StringParameter' is mapped on the table 'stringparameters' and 
    is derived from 'Parameter'. The value assigned to a StringParameter must be 
    a string. 
    '''
   
    id = Column('id', Integer, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', String(40), primary_key=True)
    
    __tablename__ = 'stringparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']
                                           , onupdate="CASCADE", ondelete="CASCADE"),
                      {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'inherit_condition': and_(Parameter.id == id, Parameter.name == name),
                       'polymorphic_identity':'string'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise TypeError("Argument must be unicode or string")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and string value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The string associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no a string.
        '''
        self.name = name
        self.value = value

    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)
        

class IntegerParameter(Parameter):
    '''
    The class 'IntegerParameter' is mapped on the table 'integerparameters' and 
    is derived from Parameter. The value assigned to an IntegerParameter must be
    an integer. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', Integer, autoincrement=False, primary_key=True)

    __tablename__ = 'integerparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name'],
                                           onupdate="CASCADE", ondelete="CASCADE"),
                                           {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'inherit_condition': and_(Parameter.id == id, Parameter.name == name),
                       'polymorphic_identity':'integer'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not (isinstance(parameter, int) or isinstance(parameter, long)):
            raise TypeError("Argument must be an integer")
        return parameter 
    
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and integer value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The integer associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no an integer.
        '''
        self.name = name
        self.value = value
    
    def __repr__(self):
        return "<%s(%s,'%s',%s)>" % (self.__class__.__name__, self.id, self.name, self.value)


class FloatParameter(Parameter):
    '''
    The class 'FloatParameter' is mapped on the table 'floatparameters' and 
    is derived from 'Parameter'. The value assigned to a FloatParameter must be 
    a float. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', Float, primary_key=True)

    __tablename__ = 'floatparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']), {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'polymorphic_identity':'float'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, float):
            raise TypeError("Argument must be a float")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and string value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The float associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no float.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class DateParameter(Parameter):
    '''
    The class 'FloatParameter' is mapped on the table 'dateparameters' and 
    is derived from 'Parameter'. The value assigned to a DateParameter must be 
    a datetime.date. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', Date, primary_key=True)

    __tablename__ = 'dateparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']), {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'polymorphic_identity':'date'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, date) or parameter is None:
            raise TypeError("Argument must be a datetime.date")
        elif isinstance(parameter, date) and parameter.timetuple()[3:6] != (0, 0, 0):
            raise TypeError("Argument must be a datetime.date")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and datetime.date.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.date associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no a datetime.date.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class TimeParameter(Parameter):
    '''
    The class 'TimeParameter' is mapped on the table 'timeparameters' and 
    is derived from 'Parameter'. The value assigned to a TimeParameter must be 
    a datetime.time. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', Time, primary_key=True)

    __tablename__ = 'timeparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']), {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'polymorphic_identity':'time'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, time) or parameter is None:
            raise TypeError("Argument must be a datetime.time")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and datetime.time value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.time object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is not datetime.time.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class DateTimeParameter(Parameter):
    '''
    The class 'DateTimeParameter' is mapped on the table 'datetimeparameters' and 
    is derived from 'Parameter'. The value assigned to a DateTimeParameter must be 
    a datetime.datetime. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', DateTime, primary_key=True)

    __tablename__ = 'datetimeparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']), {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'polymorphic_identity':'datetime'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, datetime):
            raise TypeError("Argument must be a datetime.datetime")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and datetime.datetime value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.datetime object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no datetime.datetime.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class BooleanParameter(Parameter):
    '''
    The class 'BooleanParameter' is mapped on the table 'booleanparameters' and 
    is derived from 'Parameter'. The value assigned to a BooleanParameter must be 
    a boolean. 
    '''
    id = Column('id', Integer, autoincrement=True, unique=True)
    name = Column('name', String(40), primary_key=True)
    value = Column('value', Boolean, primary_key=True)

    __tablename__ = 'booleanparameters'
    __table_args__ = (ForeignKeyConstraint(['id', 'name'], ['parameters.id', 'parameters.name']), {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Parameter, 'polymorphic_identity':'boolean'}
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, Boolean):
            raise TypeError("Argument must be a boolean")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and boolean value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The boolean object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no boolean.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


'''
The parameterlist is an association table. It relates an Entity and a Parameter 
using their ids as foreign keys.
'''
parameterlist = Table('parameterlist', base.metadata,
     Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True), #
   #  Column('name',String(40), primary_key=True),
     Column('parameter_id', Integer, ForeignKey('parameters.id'), primary_key=True), # ForeignKey('parameters.id'), 
  #   ForeignKeyConstraint(['parameter_id', 'name'],['parameters.id','parameters.name'])
   #   ForeignKeyConstraint(['parameter_id'],['parameters.id'])
     mysql_engine='InnoDB'
     )


'''
relations is an association table. It relates an Entity and another Entity 
using their ids as foreign keys.
'''
#relations = Table('relations', base.metadata,     
#     Column('id', Integer, ForeignKey('entities.id'), primary_key=True),
#     Column('child_id', Integer, ForeignKey('entities.id'), primary_key=True),
#     Column('type',String(40)))
def _create_relation(child, label):
    """A creator function, constructs Holdings from Stock and share quantity."""
    return Relation(child=child, label=label)

class Relation(base):
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'), primary_key=True)
    child_id = Column('child_id', Integer, ForeignKey('entities.id'), primary_key=True)
    label = Column('label', String(500), primary_key=True)
    
    __tablename__ = 'relations'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    parent = relation('Entity',
                       primaryjoin='Relation.parent_id==Entity.id')
    child = relation('Entity',
                      primaryjoin='Relation.child_id==Entity.id')
    
    def __init__(self, parent=None, child=None, label=0):
        self.parent = parent
        self.child = child
        self.label = label


class Context(base):
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    id = Column('id', Integer, primary_key=True)
    entity_id = Column('entity_id', Integer, ForeignKey('entities.id'))
    path = Column('path', String(500))
    
    __tablename__ = 'contexts'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    @validates('path')
    def validate_path(self, key, parameter):
        if not isinstance(parameter, str):
            raise TypeError("Argument must be a string")
        return parameter 
    
    def __init__(self, path):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of data
        data -- The data to be saved
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        self.path = path

    
class Entity(base):
    '''
    The class 'Entity' is mapped on the table 'entities'. The name column 
    contains unique information about the object type (e.g. 'Observer', 
    'Experiment'). Each Entity is connected to a set of parameters through the 
    adjacency list parameterlist. Those parameters can be accessed via the 
    parameters attribute of the Entity class. Additionally entities can build a 
    hierarchical structure (represented in a flat table!) via the children and 
    parents attributes.
    '''
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(40)) 
   
    __tablename__ = 'entities'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    #relations = association_proxy('children', 'label', creator=_create_relation)
    
#    children = relation('Relation',
#        collection_class=attribute_mapped_collection('child'),
#        primaryjoin='Relation.parent_id==Entity.id')
#   
    # one to many Entity->Context
    context = relation('Context', backref=backref('entities', order_by=id))
    # many to many Entity<->Parameter,deletion cascade is handled in session.flush()
    parameters = relation('Parameter', secondary=parameterlist,
                        #primaryjoin = id == parameterlist.c.entity_id,
                        #secondaryjoin = parameterlist.c.parameter_id == Parameter.id,
                        backref=backref('entities', order_by=id))
    # one to many Entity->Data
    data = relation('Data', backref=backref('entities', order_by=id),
                    cascade='all,delete-orphan', single_parent=True)
    
    
    @validates('name')
    def validate_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument must be a string")
        return e_name 
    
    def __init__(self, name):
        '''Initialize an entity corresponding to an experimental object.
        
        Argument:
        name -- A one-word-description of the experimental object
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no an integer.
        '''
        self.name = name
                
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id, self.name)


class ParameterOption(base):
    '''
    The class 'ParameterOption' is mapped on the table 'parameteroptions'. This 
    table provides a lookup table for entity/parameter pairs and the type the 
    parameter is required to have. Ideally this table is filled once after table 
    creation. And only if at a later moment the need for a new parameter emerges, 
    then this parameter can be added to the list of allowed parameters.
    '''
    parameter_name = Column('parameter_name', String(40), primary_key=True)
    entity_name = Column('entity_name', String(40), primary_key=True)
    parameter_type = Column('parameter_type', String(40), primary_key=True)
  
    __tablename__ = 'parameteroptions'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    @validates('parameter_name')
    def validate_parameter_name(self, key, p_name):
        if not isinstance(p_name, str):
            raise TypeError("Argument 'parameter_name' must be a string")
        return p_name 
    
    @validates('entity_name')
    def validate_entity_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument 'entity_name' must be a string")
        return e_name 
    
    @validates('parameter_type')
    def validate_parameter_type(self, key, p_type):
        if not isinstance(p_type, str) or p_type not in ('integer', 'string'):
            raise TypeError(("Argument 'parameter_type' must one of the ",
                             "following strings: ",
                             "'string' or 'integer'"))
        return p_type 
    
    def __init__(self, entity_name, parameter_name, parameter_type):
        '''Initialize an entity - parameter pair 
        
        Argument:
        entity_name -- A one-word-description of the experimental object
        parameter_name -- A one-word-description of the parameter 
        parameter_value -- The polimorphic type of the parameter 
            (e.g. 'integer', 'string')
        
        Raises:
        TypeError -- Occurs if arguments aren't strings or type not in list.
        '''
        self.entity_name = entity_name
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
                
    def __repr__(self):
        return "<ParameterOption('%s','%s', '%s')>" % (self.entity_name,
                                                       self.parameter_name,
                                                       self.parameter_type)


if __name__ == "__main__":
    pass