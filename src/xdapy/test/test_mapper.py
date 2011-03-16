"""Unittest for  proxy

Created on Jun 17, 2009
"""
from sqlalchemy.exceptions import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from xdapy.errors import InsertionError, SelectionError, ContextError
from xdapy import Connection, Mapper
from xdapy.structures import EntityObject
from xdapy.utils.algorithms import listequal
from xdapy.structures import ParameterOption
import unittest
"""
TODO: Real test for create_tables
As of Juli 7, 2010: 4Errors
I ntegrityError: (IntegrityError) duplicate key value violates unique constraint "stringparameters_pkey"
 'INSERT INTO stringparameters (id, name, value) VALUES (%(id)s, %(name)s, %(value)s)' {'id': 4L, 'value': 'John Doe', 'name': 'experimenter'}

"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


class Experiment(EntityObject):
    parameter_types = {
        'project': 'string',
        'experimenter': 'string'
    }
    
class Observer(EntityObject):
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }

class Trial(EntityObject):
    parameter_types = {
        'time': 'string',
        'rt': 'integer',
        'valid': 'boolean',
        'response': 'string'
    }

class TestProxy(unittest.TestCase):

    def setUp(self):
        db = Connection.test()
        self.m = Mapper(db)
        self.m.create_tables(overwrite=True)
        
        self.m.register(Observer, Experiment, Trial)
        
        
    def tearDown(self):
        pass
        
    def testCreateTables(self):
        self.m.create_tables(overwrite=True)

    def testSave(self):
        valid_objects = ("""Observer(name="Max Mustermann", handedness="right", age=26)""",
                       """Experiment(project="MyProject", experimenter="John Doe")""",
                       """Experiment(project="MyProject")""")
  
        invalid_objects = ("""Observer(name=9, handedness="right")""",
                       """Experiment(project=12)""",
                       """Experiment(project=1.2)""")
       
        invalid_types = (None, 1, 1.2, 'string')
        
        for obj in valid_objects:
            eval(obj, globals(), locals())

        for obj in invalid_objects:
            self.assertRaises(TypeError, lambda obj: eval(obj, globals(), locals()), obj)
        
        for obj in invalid_types:
            from sqlalchemy.orm.exc import UnmappedInstanceError
            self.assertRaises(UnmappedInstanceError, self.m.save, obj)
        
        exp = Experiment(project='MyProject', experimenter="John Doe")
        def assignment():
            exp.param['parameter'] = 'new'
        self.assertRaises(KeyError, assignment)
        
        exp = Experiment(project='MyProject', experimenter="John Doe")
        def assignment():
            exp.param['perimenter'] = 'new'
        self.assertRaises(KeyError, assignment)
    
        exp = Experiment(project='MyProject', experimenter="John Doe")
        exp.data['somedata'] = """[0, 1, 2, 3]"""
        
        def assign_list():
            exp.data['somedata'] = [0, 1, 2, 3]

        self.assertRaises(ValueError, assign_list)
        self.m.save(exp)
        
        e = Experiment(project='YourProject', experimenter="Johny Dony")
        o1 = Observer(name="Maxime Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
        self.m.save(e, o1, o2)
        
    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        obs.data['moredata'] = """(0, 3, 6, 8)""" # TODO: Deal with non-string data?
        obs.data['otherredata'] = """(0, 3, 6, 8)"""
        self.m.save(obs)
       
        obs = Observer(name="Max Mustermann")
        obs_by_object = self.m.find_first(obs)
        
        obs_by_object = self.m.find_by_id(Observer, id=1)
         
        #Error if object does not exist
        self.assertIsNone(self.m.find_first(Observer(name='John Doe')))
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 5)
        
        #Error if object exists multiple times # TODO
        self.m.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertTrue(len(self.m.find_all(Observer(name="Max Mustermann"))) > 1)                  
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 3)
 
                    
    def testConnectObjects(self):
        #Test add_child and get_children
        e = Experiment(project='MyProject', experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        t = Trial(rt=125, valid=True, response='left')
        self.m.save(e)
        
        self.m.save(o, t)
        o.children.append(t)
        self.assertEqual(e.children, [])
        self.assertEqual(o.children, [t])
        self.assertEqual(t.children, [])
        
        e.children.append(o)
        self.assertEqual(e.children, [o])
        self.assertEqual(o.children, [t])
        self.assertEqual(t.children, [])
          
        e2 = Experiment(project='yourProject', experimenter="John Doe")
        t2 = Trial(rt=189, valid=False, response='right')
        self.m.save(e2, t2)
        e2.children.append(o) # o gets new parent e2
        o.children.extend([t2, e2])
        
        self.assertEqual(e.children, [])
        self.assertItemsEqual(o.children, [t, t2, e2])
        
#    def testGetDataMatrix(self):
#        e1 = Experiment(project='MyProject', experimenter="John Doe")
#        o1 = Observer(name="Max Mustermann", handedness="right", age=26)
#        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
#       
#        e2 = Experiment(project='YourProject', experimenter="John Doe")
#        o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
#        
#        self.m.save(e1, e2, o1, o2, o3)
#        
#        #all objects are root
#        self.assertEqual(self.m.get_data_matrix([], {'Observer':['age']}), [[26], [38], [40]])
#        self.assertEqual(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}), [])
#        self.assertEqual(self.m.get_data_matrix([Experiment()], {'Observer':['age']}), [])
#        
#        #only e1 and e2 are root
#        self.m.connect_objects(e1, o1)
#        self.m.connect_objects(e1, o2)
#        self.m.connect_objects(e2, o3)
#        self.m.connect_objects(e2, o2)
#        
#        #make sure the correct data is retrieved
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age']}),
#                                                [[26L], [38L]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}),
#                                                [[38L], [40]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age', 'name']}),
#                                                [[38, "Susanne Sorgenfrei"], [40, 'Susi Sorgen']]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age', 'name']}),
#                                                [[26, "Max Mustermann"], [38, "Susanne Sorgenfrei"]]))
#        
#        self.assertTrue(listequal(self.m.get_data_matrix([Observer(handedness='left')],
#                                                 {'Experiment':['project'], 'Observer':['name']}),
#                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
#                                                  ['YourProject', "Susi Sorgen"]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Observer(handedness='left')],
#                                                 {'Observer':['name'], 'Experiment':['project']}),
#                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
#                                                  ['YourProject', "Susi Sorgen"]]))
        
#
#    def testRegisterParameter(self):
#        valid_parameters = (('Observer', 'glasses', 'string'),
#                          ('Experiment', 'reference', 'string'))
#        
#        invalid_parameters = (('Observer', 'name', 25),
#                          ('Observer', 54, 'integer'),
#                          (24, 'project', 'string'))
#        
#        for e, p, pt in valid_parameters:
#            self.m.register_parameter(e, p, pt)
#        
#        for e, p, pt in invalid_parameters:
#            self.assertRaises(TypeError, self.m.register_parameter, e, p, pt)
#        
#        self.assertRaises(IntegrityError, self.m.register_parameter,
#                          'Experiment', 'reference', 'string')

#===============================================================================
#        
# 
# class InvalidObserverClass(ObjectTemplate):
#    """Observer class to store information about an observer"""
#    _parameters_ = {'name':'string', 'handedness':'string','age':'int'}
#    
#    def __init__(self, name=None, handedness=None, age=None):
#        self.name = name
#        self.handedness=handedness
#        self.age=age
#        
# class TestProxyForObjectTemplates(unittest.TestCase):
# 
#    def setUp(self):
#        self.m = ProxyForObjectTemplates()
#        self.m.create_tables()
#        
#    def tearDown(self):
#        pass
# 
#    def testCreateTables(self):
#        self.m.create_tables()
# 
#    def testSaveObject(self):
#        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
#                       Experiment(project='MyProject',experimenter="John Doe"))
#        invalid_objects=(Observer(name="Max Mustermann", handedness="right", age='26'),
#                       Experiment(project='MyProject', experimenter=None),
#                       Observer(name="Max Mustermann", handedness="right"),
#                       Observer(),
#                       Experiment(project='MyProject'))#,
#                       #'justastring')
#        
#        for obj in valid_objects:
#            self.m.save(obj)
#        for obj in invalid_objects:
#            self.assertRaises(TypeError, self.m.save, obj)    
#        self.assertRaises(TypeError,self.m.save,
#                          InvalidObserverClass(name="Max Mustermann", 
#                                               handedness="right", age=26))
#            
#    def testLoadObject(self):
#        #AmbiguousObjects
#        self.m.save(Observer(name="Max Mustermann", handedness="right", age=26))
#        self.m.load(Observer(name="Max Mustermann"))           
#        self.m.save(Observer(name="Max Mustermann", handedness="left", age=29))
#        self.assertRaises(RequestObjectError,self.m.load,Observer(name="Max Mustermann"))                  
#        self.assertRaises(RequestObjectError,self.m.load,3)
#                    
#    def testConnectObjects(self):
#        #Test add_child and get_children
#        e = Experiment(project='MyProject',experimenter="John Doe")
#        o = Observer(name="Max Mustermann", handedness="right", age=26)
#        self.m.save(e)
#        self.m.save(o)
#        self.m.add_child(e,o)
#        
#        s = self.m.Session()
#        exp_reloaded = self.m.viewhandler.get_entity(s,1)
#        obs_reloaded = self.m.viewhandler.get_entity(s,2)
#        
#        self.assertEqual(exp_reloaded.children, [obs_reloaded])
#        self.assertEqual(exp_reloaded.parents,[])
#        self.assertEqual(obs_reloaded.children, [])
#        self.assertEqual(obs_reloaded.parents,[exp_reloaded])
#        
#        exp_children = self.m.get_children(e)
#        self.assertEqual(exp_children,[o])
#===============================================================================

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()