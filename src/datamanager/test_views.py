"""Unittest for views

Created on Jun 17, 2009
    TestStringParameter:    Testcase for StringParameter class
    TestIntegerParameter:   Testcase for IntegerParameter class
    TestEntity:             Testcase for Entity class
    TestParameterOption:    Testcase for ParameterOption class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.views import Data, Parameter, StringParameter, IntegerParameter, Entity, ParameterOption, Relation
from datamanager.views import base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, join
from sqlalchemy.sql import and_
from sqlalchemy.exceptions import IntegrityError                 
from pickle import dumps, loads
import numpy as np
from sqlalchemy.orm import exc as orm_exc

db = 'mysql'

def return_engine():
    if db is 'mysql':
        engine = create_engine('mysql://root@localhost/unittestDB',connect_args={'passwd':'tin4u'})
        base.metadata.drop_all(engine)
    elif db is 'sqlite':
        engine = create_engine('sqlite:///:memory:', echo=False)
    else:
        raise AttributeError('db type "%s" not defined'%db)
    return engine
        
class TestClass(object):
    def __init__(self):
        self.test = 'test'
    def returntest(self):
        return self.test

class TestData(unittest.TestCase):

    # images, class, 
    valid_input = (('somestring','SomeString'),
                   ('someint',1),
                   ('somefloat',1.2),
                   ('somelist',[0, 2, 3, 5]),
                   ('sometuple',(0, 2, 3, 5)),
                   ('somearray1',np.array([2,3,1,0])),
                   ('somearray2', np.array([[ 1.+0.j, 2.+0.j], [ 0.+0.j, 0.+0.j], [ 1.+1.j, 3.+0.j]])),
                   ('somearray3', np.array([[1,2,3],(4,5,6)])),
                   ('somedict',{'jack': 4098, 'sape': 4139}),
                   ('someclass',TestClass()))
    
    invalid_input = (('name',None))
    
    def setUp(self):
        """Create test database in memory"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name, data in self.valid_input:
            d = Data(name=name,data=dumps(data))
            self.assertEqual(d.name,name)
            self.assertEqual(d.data,dumps(data))
            self.session.add(d)
            self.session.commit()
            d_reloaded =  self.session.query(Data).filter(Data.name==name).one()
            try:
                self.assertEqual(data,loads(d_reloaded.data))
            except ValueError:
                #arrays
                self.assertEqual(data.all(),loads(d_reloaded.data).all())
            except AssertionError:
                #testclass
                self.assertEqual(data.test,loads(d_reloaded.data).test)

class TestParameter(unittest.TestCase):
    string_exceeding_length = '*****************************************'
    
    def setUp(self):
        """Create test database"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def testInvalidInputLength(self):
        parameter = Parameter(self.string_exceeding_length)
        self.session.add(parameter)
        self.session.commit()
        self.assertEqual([], self.session.query(Parameter).filter(Parameter.name==self.string_exceeding_length).all())
       
class TestStringParameter(unittest.TestCase):
    valid_input = (('name','Value'),
                  ('name','value'),
                  ('****************************************','Value'),
                  ('name','****************************************'))
    invalid_input_types = (('name',0),
                    ('name',0.0),
                    ('name',None),
                    (0,None))
                    #,('Name','value'))
    
    invalid_input_length = ('name','******************************************************************************************************')
    
    def setUp(self):
        """Create test database in memory"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name,value in self.valid_input:
            par = StringParameter(name,value)
            self.session.add(par)
            self.session.commit()
            self.assertEqual(par.name, name)
            self.assertEqual(par.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, StringParameter, name, value)
        
    def testInvalidInputLength(self):
        name = self.invalid_input_length[0]
        value = self.invalid_input_length[1]
        parameter = StringParameter(name,value)
        self.session.add(parameter)
        self.session.commit()
        self.assertEqual([], self.session.query(StringParameter).filter(and_(StringParameter.name==name,StringParameter.value==value)).all())
        
        

class TestIntegerParameter(unittest.TestCase):
    valid_input = (('name',26),
                  ('name',-1),
                  ('****************************************',0))
    invalid_input_types = (('name','0'),
                    ('name',0.0),
                    ('name',None))

    def setUp(self):
        """Create test database in memory"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter_reloaded = IntegerParameter(name,value)
            self.assertEqual(parameter_reloaded.name, name)
            self.assertEqual(parameter_reloaded.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, IntegerParameter, name, value)
    
          
class TestEntity(unittest.TestCase):
    """Testcase for Entity class

    Longer class information....
    Longer class information....
    
    Attributes:
        something -- A boolean indicating if we like something.
        somethingelse -- An integer count of the something else.
    """
    
    valid_input=('observer','experiment', 'observer')
    invalid_input_types=(0,0.0,None)

    def setUp(self):
        """Create test database in memory"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def testValidInput(self):
        for name in self.valid_input:
            entity = Entity(name)
            self.assertEqual(entity.name, name)
            self.session.add(entity)
            self.session.commit()
            entity_reloaded =  self.session.query(Entity).filter(and_(Entity.name==name,Entity.id==entity.id)).one()
            self.assertEqual(entity,entity_reloaded)
            
    def testInvalidInputType(self):
        for name in self.invalid_input_types:
            self.assertRaises(TypeError, Entity, name)
    
    def testParametersAttribute(self):
        intparam = IntegerParameter('intname',1)
        strparam = StringParameter('strname', 'string')
        exp = Entity('experiment')
        
        self.session.add(exp)
        self.session.add(intparam)
        self.session.add(strparam)
        exp.parameters.append(intparam)
        self.session.commit()
        
        exp_reloaded =  self.session.query(Entity).filter(Entity.name=='experiment').one()
        ip_reloaded = self.session.query(Parameter).filter(Parameter.name=='intname').one()
        sp_reloaded = self.session.query(Parameter).filter(Parameter.name=='strname').one()
        
        self.assertEqual(exp_reloaded.parameters, [intparam])
        self.assertEqual(ip_reloaded.entities,[exp])
        self.assertEqual(sp_reloaded.entities,[])
        
    def testRelationsAttribute(self):
        exp = Entity('experiment')
        obs1 = Entity('observer1')
        obs2 = Entity('observer2')
        exp.relations[obs1]=1
        
        self.session.add(exp)
        self.session.add(obs2)
        self.session.commit()
        
      #  parents = self.session.query(Entity.name,Relation.label).select_from(join(Entity,Relation,Relation.parent)).filter(Relation.child_id==childid).all()
       # children = self.session.query(Entity.name).select_from(join(Entity,Relation,Relation.child)).filter(Relation.parent_id==parentid).all()
   
        #exp_reloaded = self.session.query(Entity).select_from(join(Entity,Relation,Relation.parent)).filter(Entity.name=='experiment').all()
        #print exp_reloaded
        exp_reloaded =  self.session.query(Entity).filter(Entity.name=='experiment').one()
        self.assertTrue(obs1 in exp_reloaded.relations)
       # self.assertEqual(exp_reloaded.parents,[])
        
        obs1_reloaded =  self.session.query(Entity).filter(Entity.name=='observer1').one()
        
        obs2_reloaded =  self.session.query(Entity).filter(Entity.name=='observer2').one()
        self.assertFalse(obs1_reloaded.relations)
        

          
class TestParameterOption(unittest.TestCase):
    """Testcase for ParameterOption class"""
    
    valid_input=(('observer', 'name', 'string'),
                 ('experiment', 'project', 'string'),
                 ('observer', 'age', 'integer'))
    
    invalid_input=((26, 'name', 'string'),
                   ('experiment', 2.3, 'string'),
                   ('observer', 'age', 90),
                   ('observer', 'age', 'int'))
    

    def setUp(self):
        """Create test database in memory"""
        engine = return_engine()
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def testValidInput(self):
        for e_name, p_name, p_type in self.valid_input:
            parameter_option = ParameterOption(e_name, p_name, p_type)
            self.assertEqual(parameter_option.parameter_name, p_name)
            self.session.add(parameter_option)
            self.session.commit()
            parameter_option_reloaded =  self.session.query(ParameterOption).filter(
                and_(ParameterOption.entity_name==e_name,
                     ParameterOption.parameter_name==p_name,
                     ParameterOption.parameter_type==p_type)).one()
            self.assertEqual(parameter_option,parameter_option_reloaded)
            
    def testInvalidInput(self):
        for e_name, p_name, p_type in self.invalid_input:
            self.assertRaises(TypeError, ParameterOption, e_name, p_name, p_type)

    def testPrimaryKeyConstrain(self):
        parameter_option1 = ParameterOption('observer', 'parameter', 'integer')
        parameter_option2 = ParameterOption('observer', 'parameter', 'integer')
        self.session.add(parameter_option1)
        self.session.add(parameter_option2)
        self.assertRaises(IntegrityError, self.session.commit)
        
     
        
if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test.testName']
    unittest.main()