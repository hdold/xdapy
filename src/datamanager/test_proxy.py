"""Unittest for the proxy

Created on Jun 17, 2009
    TestProxy:    Testcase for Proxy class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.proxy import Proxy
from datamanager.objects import ObjectDict, Observer, Experiment
from datamanager.errors import RequestObjectError
from datamanager.views import ParameterOption
from sqlalchemy.exceptions import IntegrityError

class TestProxy(unittest.TestCase):

    def setUp(self):
        self.p = Proxy('localhost','root','unittestDB','tin4u')
        self.p.create_tables(overwrite=True)
        self.session = self.p.Session()
        self.session.add(ParameterOption('Observer','name','string'))
        self.session.add(ParameterOption('Observer','age','integer'))
        self.session.add(ParameterOption('Observer','handedness','string'))
        self.session.add(ParameterOption('Experiment','project','string'))
        self.session.add(ParameterOption('Experiment','experimenter','string'))
        self.session.commit()
        
    def tearDown(self):
        pass

    def testCreateTables(self):
        self.p.create_tables()
#
    def testSave(self):
        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
                       Experiment(project='MyProject',experimenter="John Doe"))
        invalid_objects=(Experiment(project='MyProject', experimenter=None),
                       Observer(name="Max Mustermann", handedness="right"),
                       Observer(),
                       Experiment(project='MyProject'),
                       Experiment(project=1.2))
        
        invalid_types = (None,1,1.2,'string')
        
        for obj in valid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.p.save(obj)
            self.assertEqual(obj.get_concurrent(), True)

        for obj in invalid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.assertRaises(TypeError, self.p.save, obj)    
            self.assertEqual(obj.get_concurrent(), False)
        
        for obj in invalid_types:
            self.assertRaises(TypeError, self.p.save, obj)
        
        exp = Experiment(project='MyProject',experimenter="John Doe")
        exp['parameter']='new'
        self.assertRaises(RequestObjectError, self.p.save, exp)
        
        exp = Experiment(project='MyProject',experimenter="John Doe")
        exp['perimenter']='new'
        #self.p.save(exp)
        self.assertRaises(RequestObjectError, self.p.save, exp)
        
        exp = Experiment(project='MyProject',experimenter="John Doe")
        exp.data['somedata']=[0,1,2,3]
        self.p.save(exp)
        
        e = Experiment(project='YourProject',experimenter="Johny Dony")
        o1 = Observer(name="Maxime Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left',age=38)
        self.p.save(e,o1,o2)
        
    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        obs.data['moredata']=(0,3,6,8)
        obs.data['otherredata']=(0,3,6,8)
        self.p.save(obs)
        
        #Test the settings of _cuncurrent
        obs = Observer(name="Max Mustermann")
        obs_by_object = self.p.load(obs)
        self.assertEqual(obs_by_object.get_concurrent(),True)
        #important obs_by_object and obs are not equal, only their dictionary parts are. 
        
        #Test the settings of _cuncurrent
        #important obs_by_id and obs are not equal, only their dictionary parts are. 
        obs_by_object = self.p.load(1)
        self.assertEqual(obs_by_object.get_concurrent(),True)
         
        #Error if object does not exist
        self.assertRaises(RequestObjectError,self.p.load,Observer(name='John Doe'))
        self.assertRaises(RequestObjectError,self.p.load,5)
        
        #Error if object exists multiple times
        self.p.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertRaises(RequestObjectError,self.p.load,Observer(name="Max Mustermann"))                  
        self.assertRaises(RequestObjectError,self.p.load,3)
        
        #No Error for load_all
        for obs_by_obj in self.p.load_all(Observer(name='Max Mustermann')):
            self.assertEqual(obs_by_obj.get_concurrent(),True) 
#                    
    def testConnectObjects(self):
        #Test add_child and get_children
        e = Experiment(project='MyProject',experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        self.p.save(e)
        
        self.assertRaises(RequestObjectError,self.p.connect_objects,e,o)
        self.p.save(o)
        self.p.connect_objects(e,o)
        
        #Assure that the .children and .parent are correctly populated
    
        
    def testGetChildren(self):
        e = Experiment(project='MyProject',experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        self.p.save(e)
        self.p.save(o)
        self.p.connect_objects(e,o)
        
        #Assert that children are correctly returned
        self.assertEqual(self.p.get_children(e), [o])
        self.assertEqual(self.p.get_children(o), [])
        
    
    def testGetDataMatrix(self):
        e = Experiment(project='MyProject',experimenter="John Doe")
        o1 = Observer(name="Max Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left',age=38)
       
        o3 = Observer(name="Susi Sorgen", handedness='left',age=38)
        #all observers are root
        self.p.save(e, o1, o2, o3)
     #   self.p.get_data_matrix([Observer(name="Susanne Sorgenfrei")], [Observer()])
        
        
        #only e is root
        self.p.connect_objects(e, o1)
        self.p.connect_objects(e, o2)
       # self.p.connect_objects(e, o3)
        self.p.connect_objects(o2, o3)
        print self.p.get_data_matrix([Observer(name="Susanne Sorgenfrei")], [Observer()])
        
        
    def testRegisterParameter(self):
        valid_parameters=(('Observer', 'glasses', 'string'),
                          ('Experiment','reference','string'))
        
        invalid_parameters=(('Observer', 'name', 25),
                          ('Observer', 54, 'integer'),
                          (24,'project','string'))
        
        for e,p,pt in valid_parameters:
            self.p.register_parameter(e,p,pt)
        
        for e,p,pt in invalid_parameters:
            self.assertRaises(TypeError, self.p.register_parameter,e,p,pt)
        
        self.assertRaises(IntegrityError, self.p.register_parameter, 
                          'Experiment', 'reference', 'string')
        
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
#        self.p = ProxyForObjectTemplates()
#        self.p.create_tables()
#        
#    def tearDown(self):
#        pass
# 
#    def testCreateTables(self):
#        self.p.create_tables()
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
#            self.p.save(obj)
#        for obj in invalid_objects:
#            self.assertRaises(TypeError, self.p.save, obj)    
#        self.assertRaises(TypeError,self.p.save,
#                          InvalidObserverClass(name="Max Mustermann", 
#                                               handedness="right", age=26))
#            
#    def testLoadObject(self):
#        #AmbiguousObjects
#        self.p.save(Observer(name="Max Mustermann", handedness="right", age=26))
#        self.p.load(Observer(name="Max Mustermann"))           
#        self.p.save(Observer(name="Max Mustermann", handedness="left", age=29))
#        self.assertRaises(RequestObjectError,self.p.load,Observer(name="Max Mustermann"))                  
#        self.assertRaises(RequestObjectError,self.p.load,3)
#                    
#    def testConnectObjects(self):
#        #Test add_child and get_children
#        e = Experiment(project='MyProject',experimenter="John Doe")
#        o = Observer(name="Max Mustermann", handedness="right", age=26)
#        self.p.save(e)
#        self.p.save(o)
#        self.p.add_child(e,o)
#        
#        s = self.p.Session()
#        exp_reloaded = self.p.viewhandler.get_entity(s,1)
#        obs_reloaded = self.p.viewhandler.get_entity(s,2)
#        
#        self.assertEqual(exp_reloaded.children, [obs_reloaded])
#        self.assertEqual(exp_reloaded.parents,[])
#        self.assertEqual(obs_reloaded.children, [])
#        self.assertEqual(obs_reloaded.parents,[exp_reloaded])
#        
#        exp_children = self.p.get_children(e)
#        self.assertEqual(exp_children,[o])
#===============================================================================

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()