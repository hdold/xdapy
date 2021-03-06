# -*- coding: utf-8 -*-

"""Unittest for  proxy

Created on Jun 17, 2009
"""
import operator
from sqlalchemy.exc import CircularDependencyError, InvalidRequestError
from sqlalchemy.orm.exc import NoResultFound, DetachedInstanceError
from xdapy import Connection, Mapper, Entity
from xdapy.structures import Context, create_entity
from xdapy.errors import InsertionError
from xdapy.operators import gt, lt, eq, between, ge

import unittest
import datetime
from xdapy.utils.algorithms import listequal

"""
TODO: Real test for create_tables
As of Juli 7, 2010: 4Errors
IntegrityError: (IntegrityError) duplicate key value violates unique constraint "stringparameters_pkey"
 'INSERT INTO stringparameters (id, name, value) VALUES (%(id)s, %(name)s, %(value)s)' {'id': 4L, 'value': 'John Doe', 'name': 'experimenter'}

"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


class Experiment(Entity):
    declared_params = {
        'project': 'string',
        'experimenter': 'string'
    }

class Observer(Entity):
    declared_params = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }

class Trial(Entity):
    declared_params = {
        'time': 'string',
        'rt': 'integer',
        'valid': 'boolean',
        'response': 'string'
    }

class Session(Entity):
    declared_params = {
        'count': 'integer',
        'date': 'date',
        'category1': 'integer',
        'category2': 'integer'
    }


class Setup(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)

        self.m.register(Observer, Experiment, Trial, Session)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

class TestMapper(Setup):
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
            exp.params['parameter'] = 'new'
        self.assertRaises(KeyError, assignment)

        exp = Experiment(project='MyProject', experimenter="John Doe")
        def assignment2():
            exp.params['perimenter'] = 'new'
        self.assertRaises(KeyError, assignment2)

        exp = Experiment(project='MyProject', experimenter="John Doe")
        self.m.save(exp)
        exp.data['somedata'].put("""[0, 1, 2, 3]""")

        def assign_list():
            exp.data['somedata'].put([0, 1, 2, 3])

        self.assertRaises(ValueError, assign_list)
        self.m.save(exp)

        e = Experiment(project='YourProject', experimenter="Johny Dony")
        o1 = Observer(name="Maxime Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
        self.m.save(e, o1, o2)

        self.assertEqual(len(self.m.find_all(Experiment)), 2)
        self.assertEqual(len(self.m.find_all(Observer)), 2)
        self.assertEqual(len(self.m.find_all(Entity)), 4)
        self.assertEqual(len(self.m.find_all(Trial)), 0)

        obs = self.m.find_all(Observer)
        self.m.delete(*obs)
        self.m.delete(e)
        self.assertEqual(len(self.m.find_all(Entity)), 1)

    def test_find_registered_entities(self):
        entity_classes = [Experiment, Observer, Trial, Session]
        entities_in_db = self.m.entities_from_db()
        self.assertEqual(len(entities_in_db), len(entity_classes))
        self.assertTrue(listequal(
            [(e.__name__, e.declared_params) for e in entity_classes],
            entities_in_db
        ))


    def test_save_and_delete(self):
        e = Experiment(project='YourProject', experimenter="Johny Dony")
        t1 = Trial(rt=189, valid=True, response='right')
        t2 = Trial(rt=189, valid=False, response='right')
        s1 = Session(count=1)
        s2 = Session(count=2)

        self.assertEqual(len(self.m.find_all(Entity)), 0)
        self.assertEqual(len(self.m.find_all(Trial)), 0)
        self.assertEqual(len(self.m.find_all(Session)), 0)

        t1.parent = e
        t2.parent = e

        t1.children.append(s1)
        t2.children.append(s2)

        self.assertTrue(s1.parent is not None)
        self.assertEqual(s1.parent, t1)

        # this saves the whole tree
        self.m.save(s1)

        self.assertEqual(len(self.m.find_all(Experiment)), 1)
        self.assertEqual(len(self.m.find_all(Trial)), 2)
        self.assertEqual(len(self.m.find_all(Session)), 2)

        # t1 is being removed from the tree as well as
        # all its connections
        self.m.delete(t1)

        self.assertEqual(len(self.m.find_all(Experiment)), 1)
        self.assertEqual(len(self.m.find_all(Trial)), 1)
        self.assertEqual(len(self.m.find_all(Session)), 2)

        self.assertFalse(t1 in e.children)
        self.assertTrue(t2 in e.children)

        self.assertTrue(s1.parent is None)

        # however, s1 is still a child of t1
        self.assertTrue(s1 in t1.children)
        # but we cannot save t1 again
        self.assertRaises(InvalidRequestError, self.m.save, t1)

    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        self.m.save(obs)
        obs.data['moredata'].put("""(0, 3, 6, 8)""") # TODO: Deal with non-string data?
        obs.data['otherredata'].put("""(0, 3, 6, 8)""")
        self.m.save(obs)

        new_obs = Observer(name="Max Mustermann")
        obs_by_object = self.m.find_first(new_obs)

        obs_by_object = self.m.find_by_id(Observer, id=1)

        #Error if object does not exist
        self.assertTrue(self.m.find_first(Observer(name='John Doe')) is None) # assertIsNone
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 5)

        #Error if object exists multiple times # TODO
        self.m.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertTrue(len(self.m.find_all(Observer(name="Max Mustermann"))) > 1)
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 3)

        unique_id = obs.unique_id
        self.assertEqual(self.m.find_by_unique_id(unique_id), obs)
        self.assertRaises(NoResultFound, self.m.find_by_unique_id, "lkjlkjlkjl")


    def testEntityByName(self):
        self.assertEqual(Observer, self.m.entity_by_name(Observer))
        self.assertEqual(Observer, self.m.entity_by_name("Observer"))
        self.assertEqual(Observer, self.m.entity_by_name("Observer_e1c05e3bba82a039dd8d410aaf50f815"))

        self.assertNotEqual(Observer, self.m.entity_by_name(Experiment))

        self.assertRaises(ValueError, self.m.entity_by_name, "Observer_")
        self.assertRaises(ValueError, self.m.entity_by_name, "Obs")
        self.assertRaises(ValueError, self.m.entity_by_name, "")
        self.assertRaises(TypeError, self.m.entity_by_name, str)

        # defining a new Observer type
        Observer_new = create_entity("Observer", {})

        # approx. equivalent to but does not shadow the original Observer
        #    class Observer(Entity):
        #        declared_params = {}
        #    Observer_new = Observer
        #    del Observer

        self.m.register(Observer_new)

        # now more than one Observer has been defined
        # first check that the hashes are in order
        self.assertEqual(Observer.__name__, "Observer_e1c05e3bba82a039dd8d410aaf50f815")
        self.assertEqual(Observer_new.__name__, "Observer_99914b932bd37a50b983c5e7c90ae93b")

        # check, that "Observer" is not sufficient any more
        self.assertRaises(ValueError, self.m.entity_by_name, "Observer")

        # with the complete hash, it still works
        self.assertEqual(Observer, self.m.entity_by_name("Observer_e1c05e3bba82a039dd8d410aaf50f815"))
        self.assertEqual(Observer_new, self.m.entity_by_name("Observer_99914b932bd37a50b983c5e7c90ae93b"))

        self.assertEqual(Observer, self.m.entity_by_name(Observer))
        self.assertEqual(Observer_new, self.m.entity_by_name(Observer_new))


    def testCreate(self):
        obs = self.m.create("Observer")
        self.assertTrue(obs.id is None)
        obs = self.m.create("Observer", name="Noname")
        self.assertTrue(obs.id is None)
        self.assertEqual(obs.params["name"], "Noname")
        obs = self.m.create_and_save("Observer")
        self.assertEqual(obs.id, 1)


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
        self.assertEqual(sorted(o.children), sorted([t, t2, e2])) # assertItemsEqual

        def add_circular_1():
            e1 = Experiment()
            e2 = Experiment()
            e3 = Experiment()
            e3.parent = e2
            e2.parent = e1
            e1.parent = e3
            self.m.save(e1, e2, e3)

        self.assertRaises(CircularDependencyError, add_circular_1)

        def add_circular_2():
            e1 = Experiment()
            e2 = Experiment()
            e3 = Experiment()
            e3.parent = e2
            e2.parent = e1
            e1.parent = e3
            self.m.save(e1)

        self.assertRaises(CircularDependencyError, add_circular_2)

    def test_failing_auto_session_reverts_transaction(self):
        class DummyException(Exception):
            pass

        e1 = Experiment()
        self.m.save(e1)
        e1.params["experimenter"] = "Some experimenter"

        try:
            with self.m.auto_session as sess:
                e1.params["project"] = "e1"
                self.m.save(e1)
                raise DummyException
        except DummyException:
            pass

        self.assertEqual("Some experimenter", e1.params["experimenter"])
        self.assertRaises(KeyError, lambda: e1.params["project"])

class TestContext(Setup):
    def setUp(self):
        super(TestContext, self).setUp()

        self.e1 = Experiment(project="e1")
        self.e2 = Experiment(project="e2")

        self.o1 = Observer(name="o1", age=20)
        self.o2 = Observer(name="o2", age=25)
        self.o3 = Observer(name="o3", age=30)

        self.e1.attach("Observer", self.o1)
        self.e1.attach("Observer", self.o2)
        self.e2.attach("Observer", self.o2)
        self.e2.attach("Observer", self.o3)

        self.m.save(self.e1, self.e2, self.o1, self.o2, self.o3)

    def test_connections_automatically_set_ids(self):
        # need to check that connections have correct id and entity_id,
        # although the Experiment and Observer did not have an id
        # when the connection was established
        connections = self.m.find_all(Context)

        self.assertTrue(len(connections), 4)

        experiment_ids = [self.e1.id, self.e2.id]
        observer_ids = [self.o1.id, self.o2.id, self.o3.id]

        # check that neither list has a 0 or None entry
        self.assertTrue(all(experiment_ids))
        self.assertTrue(all(observer_ids))

        for conn in connections:
            self.assertTrue(conn.holder_id in experiment_ids)
            self.assertTrue(conn.attachment_id in observer_ids)

    def test_context(self):
        self.assertTrue(self.o1 in self.e1.context["Observer"])
        self.assertTrue(self.o2 in self.e1.context["Observer"])
        self.assertTrue(self.o3 not in self.e1.context["Observer"])

        self.assertTrue(self.o1 not in self.e2.context["Observer"])
        self.assertTrue(self.o2 in self.e2.context["Observer"])
        self.assertTrue(self.o3 in self.e2.context["Observer"])

        # check that the Context is correctly stored
        context = self.m.find_all(Context)
        self.assertTrue(any(c.holder==self.e1 and c.attachment==self.o1 and c.connection_type=="Observer" for c in context))
        self.assertTrue(any(c.holder==self.e1 and c.attachment==self.o2 and c.connection_type=="Observer" for c in context))
        self.assertFalse(any(c.holder==self.e1 and c.attachment==self.o3 and c.connection_type=="Observer" for c in context))
        self.assertFalse(any(c.holder==self.e2 and c.attachment==self.o1 and c.connection_type=="Observer" for c in context))
        self.assertTrue(any(c.holder==self.e2 and c.attachment==self.o2 and c.connection_type=="Observer" for c in context))
        self.assertTrue(any(c.holder==self.e2 and c.attachment==self.o3 and c.connection_type=="Observer" for c in context))

        self.assertTrue(len(context), 4)

    def test_context_contains(self):
        with self.m.auto_session:
            self.e1.attach("Additional Observer", self.o3)

        self.assertTrue("Observer" in self.e1.context)
        self.assertTrue("Additional Observer" in self.e1.context)
        self.assertFalse("XXX Additional Observer XXX" in self.e1.context)

        self.assertTrue("Observer" in self.e2.context)
        self.assertFalse("Additional Observer" in self.e2.context)

    def test_context_getitem(self):
        with self.m.auto_session:
            self.e1.attach("Additional Observer", self.o3)

        self.assertEqual(self.e1.context["Observer"], set([self.o1, self.o2]))
        self.assertEqual(self.e1.context["Additional Observer"], set([self.o3]))
        self.assertEqual(self.e1.context["XXX Additional Observer XXX"], set())

        self.assertEqual(self.e2.context["Observer"], set([self.o2, self.o3]))
        self.assertEqual(self.e2.context["Additional Observer"], set())

    def test_context_delete(self):
        with self.m.auto_session:
            del self.e1.context["Observer"]
        context = self.m.find_all(Context)
        self.assertTrue(len(context), 0)

    def test_context_partial_delete(self):
        with self.m.auto_session:
            self.e1.attach("Additional Observer", self.o3)

        context = self.m.find_all(Context)
        self.assertTrue(len(context), 5)

        with self.m.auto_session:
            del self.e1.context["Observer"]

        context = self.m.find_all(Context)
        self.assertTrue(len(context), 1)
        self.assertTrue(self.o3 in self.e1.context["Additional Observer"])

    def test_context_delete_does_not_delete_entities(self):
        self.assertEqual(len(self.m.find_all(Observer)), 3)
        with self.m.auto_session:
            del self.e1.context["Observer"]
        self.assertEqual(len(self.m.find_all(Observer)), 3)

    def test_context_updates(self):
        with self.m.auto_session:
            self.e1.context["Additional Observer"] = [self.o3]
        self.assertTrue(self.o3 in self.e1.context["Additional Observer"])

        self.assertEqual(self.e2.context, {
            "Observer": set([self.o2, self.o3])
        })

        with self.m.auto_session:
            self.e2.context = {
                "O even": [self.o2],
                "O odd": [self.o1, self.o3]
            }
        self.assertEqual(self.e2.context, {
            "O even": set([self.o2]),
            "O odd": set([self.o1, self.o3])
        })

        with self.m.auto_session:
            self.e2.context["O odd"].add(self.o3)
        self.assertEqual(self.e2.context, {
            "O even": set([self.o2]),
            "O odd": set([self.o1, self.o3])
        })

        with self.m.auto_session:
            self.e2.context = {}
        with self.m.auto_session:
            self.e2.context["O even"].update([self.o2])
            self.e2.context["O odd"].update([self.o1])
            self.e2.context["O odd"].update([self.o1, self.o3])
        self.assertEqual(self.e2.context, {
            "O even": set([self.o2]),
            "O odd": set([self.o1, self.o3])
        })

    def test_context_len(self):
        with self.m.auto_session:
            self.e2.context = {
                "O even": [self.o2],
                "O odd": [self.o1, self.o3]
            }

        self.assertEqual(len(self.e2.context), 2)
        self.assertEqual(len(self.e2.context["O even"]), 1)
        self.assertEqual(len(self.e2.context["O odd"]), 2)
        self.assertEqual(len(self.e2.context["O other"]), 0)
        self.assertEqual(len(self.o1.context), 0)

    def test_context_deletes_key_on_remove(self):
        with self.m.auto_session:
            self.e2.context = {
                "O even": [self.o2],
                "O odd": [self.o1, self.o3]
            }

        with self.m.auto_session:
            self.e2.context["O odd"].remove(self.o3)

        self.assertTrue("O odd" in self.e2.context)

        with self.m.auto_session:
            self.e2.context["O odd"].remove(self.o1)

        self.assertFalse("O odd" in self.e2.context)
        self.assertEqual(self.e2.context, {
            "O even": set([self.o2])
        })

    def test_context_errors(self):
        # cannot set non-iterable
        self.assertRaises(TypeError, operator.setitem, self.e1.context, "A", self.o3)
        # cannot delete unknown key
        self.assertRaises(KeyError, operator.delitem, self.e1.context, "A")
        # cannot remove non-existent item
        self.assertRaises(KeyError, lambda: self.e1.context["Observer"].remove(self.o3))

    def test_context_reprs(self):
        # should not fail
        str(self.e1.context)
        repr(self.e1.context)

        str(self.e1.context["Observer"])
        repr(self.e1.context["Observer"])

        context = self.m.find_all(Context)
        for ctx in context:
            str(ctx)
            repr(ctx)

    def test_number_of_connections(self):
        self.assertEqual(self.m.find(Context).count(), 4)

    def test_that_context_delete_does_not_delete_entity_1(self):
        for i in range(1, 4):
            ctx = self.m.find_first(Context)
            self.m.delete(ctx)
            self.assertEqual(self.m.find(Experiment).count(), 2)
            self.assertEqual(self.m.find(Observer).count(), 3)
            self.assertEqual(self.m.find(Context).count(), 4 - i)

    def test_that_entity_delete_deletes_context_1(self):
        self.m.delete(self.e1)
        self.assertEqual(self.m.find(Context).count(), 2)
        self.assertEqual(self.m.find(Observer).count(), 3)
        self.assertEqual(self.m.find(Experiment).count(), 1)

    def test_that_entity_delete_deletes_context_2(self):
        self.m.delete(self.o2)
        self.assertEqual(self.m.find(Context).count(), 2)
        self.assertEqual(self.m.find(Observer).count(), 2)
        self.assertEqual(self.m.find(Experiment).count(), 2)

    def test_that_connection_returns_correctly(self):
        eee1 = Experiment()
        eee2 = Experiment()
        ooo1 = Observer()
        ooo2 = Observer()
        self.m.save(eee1, eee2, ooo1, ooo2)

        eee1.attach("CCC", ooo1)
        eee1.attach("CCC", ooo2)
        eee2.attach("CCC", ooo1)

        self.assertEqual(len(eee2.holds_context), 1, "eee2.holds_context has not been updated.")
        # check that connections have been added to session
        self.assertEqual(self.m.find(Context).filter(Context.connection_type=="CCC").count(), 3)

    def test_connections_must_be_unique(self):
        e1 = Experiment()
        o1 = Observer()
        o2 = Observer()

        self.m.save(e1)
        self.m.save(o1)

        e1.attach("CCC", o1)
        self.assertRaises(InsertionError, e1.attach, "CCC", o1)

        e1.attach("DDD", o1)
        e1.attach("CCC", o2)

        self.assertTrue(o1 in e1.attachments())
        self.assertTrue(o2 in e1.attachments())

        self.assertTrue(o1 in e1.attachments("CCC"))
        self.assertTrue(o2 in e1.attachments("CCC"))
        self.assertTrue(o1 in e1.attachments("DDD"))
        self.assertTrue(o2 not in e1.attachments("DDD"))

        self.assertTrue(e1 in o1.holders("CCC"))
        self.assertTrue(e1 in o2.holders("CCC"))
        self.assertTrue(e1 in o1.holders("DDD"))
        self.assertTrue(e1 not in o2.holders("DDD"))

        self.assertTrue(e1 in o1.holders())
        self.assertTrue(e1 in o2.holders())

        self.assertEquals(len(e1.attachments()), 2)

        self.assertTrue(e1.id is not None)
        self.assertTrue(o1.id is not None)
        self.assertTrue(o2.id is not None)
        self.assertTrue(e1.unique_id is not None)
        self.assertTrue(o1.unique_id is not None)
        self.assertTrue(o2.unique_id is not None)

    def test_connections_must_be_unique_without_session(self):
        e1 = Experiment()
        o1 = Observer()
        o2 = Observer()

        e1.attach("CCC", o1)
        self.assertRaises(InsertionError, e1.attach, "CCC", o1)

        e1.attach("DDD", o1)
        e1.attach("CCC", o2)

        self.assertTrue(o1 in e1.attachments())
        self.assertTrue(o2 in e1.attachments())

        self.assertTrue(o1 in e1.attachments("CCC"))
        self.assertTrue(o2 in e1.attachments("CCC"))
        self.assertTrue(o1 in e1.attachments("DDD"))
        self.assertTrue(o2 not in e1.attachments("DDD"))

        self.assertTrue(e1 in o1.holders("CCC"))
        self.assertTrue(e1 in o2.holders("CCC"))
        self.assertTrue(e1 in o1.holders("DDD"))
        self.assertTrue(e1 not in o2.holders("DDD"))

        self.assertTrue(e1 in o1.holders())
        self.assertTrue(e1 in o2.holders())

        self.assertEquals(len(e1.attachments()), 2)

        self.assertTrue(e1.id is None)
        self.assertTrue(o1.id is None)
        self.assertTrue(o2.id is None)
        self.assertTrue(e1.unique_id is None)
        self.assertTrue(o1.unique_id is None)
        self.assertTrue(o2.unique_id is None)

    def test_special_context_method(self):
        t1 = Trial()
        self.m.save(t1)

        self.e1.attach("Trial", t1)

        self.assertEqual(self.e1.context, {"Observer": set([self.o1, self.o2]), "Trial": set([t1])})

    def test_find_related(self):
        res = self.m.find_related("Experiment", ("Observer", {"age": between(20, 30)}))
        self.assertEqual(set(res), set([self.e1, self.e2]))
        res = self.m.find_related("Experiment", ("Observer", {"age": between(22, 30)}))
        self.assertEqual(set(res), set([self.e1, self.e2]))
        res = self.m.find_related("Experiment", ("Observer", {"age": between(26, 30)}))
        self.assertEqual(set(res), set([self.e2]))
        res = self.m.find_related("Experiment", ("Observer", {"age": ge(30)}))
        self.assertEqual(set(res), set([self.e2]))
        res = self.m.find_related("Experiment", ("Observer", {"age": lt(15)}))
        self.assertEqual(set(res), set())


class TestGetDataMatrix(Setup):
    def setUp(self):
        super(TestGetDataMatrix, self).setUp()

    def assertUnorderedEqual(self, list1, list2):
        try:
            return self.assertTrue(listequal(list1, list2))
        except AssertionError:
            print list1, list2
            raise


    def testGetDataMatrix(self):
        e1 = Experiment(project='MyProject', experimenter="John Doe")
        o1 = Observer(name="Max Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)

        e2 = Experiment(project='YourProject', experimenter="John Doe")
        o3 = Observer(name="Susi Sorgen", handedness='left', age=40)

        e1.attach("Observer", o1)
        e1.attach("Observer", o2)
        e2.attach("Observer", o3)

        self.m.save(e1, e2, o1, o2, o3)

        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment, {'Observer': ['age']}),
                                  [{"age": 26}, {"age": 38}, {"age": 40}])
        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment(project='YourProject'), {'Observer':['age']}),
                                  [{"age": 40}])
        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment(), {'Observer':['age']}),
                                  [{"age": 26}, {"age": 38}, {"age": 40}])
        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment(project='MyProject'), {'Observer':['age']}),
                                  [{"age": 26}, {"age":38}])
        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment(project='YourProject'), {'Observer':['age', 'name']}),
                                  [{"age":40, "name":'Susi Sorgen'}])
        self.assertUnorderedEqual(self.m.get_data_matrix(Experiment(project='MyProject'), {'Observer':['age', 'name']}),
                                  [{"age": 26, "name":"Max Mustermann"}, {"age":38, "name": "Susanne Sorgenfrei"}])

        self.assertUnorderedEqual(self.m.get_data_matrix(Observer(handedness='left'),
                                                         {'Experiment':['project'], 'Observer':['name']}),
                                  [{'name': 'Susanne Sorgenfrei'}, {'project': 'YourProject'},
                                   {'name': 'Susi Sorgen'}, {'project': 'MyProject'}])

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
#            self.m._register_parameter(e, p, pt)
#
#        for e, p, pt in invalid_parameters:
#            self.assertRaises(TypeError, self.m._register_parameter, e, p, pt)
#
#        self.assertRaises(IntegrityError, self.m._register_parameter,
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
#        self.connection.create_tables()
#        self.m = ProxyForObjectTemplates()
#
#    def tearDown(self):
#        self.connection.drop_tables()
#
#    def testCreateTables(self):
#        self.connection.create_tables()
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

class TestComplicatedQuery(Setup):
    def setUp(self):
        super(TestComplicatedQuery, self).setUp()

        self.o1 = Observer(name="A")
        self.o2 = Observer(name="B")
        self.o3 = Observer(name="C")

        e1 = Experiment(project="E1", experimenter="X1")
        self.e1 = e1
        e2 = Experiment(project="E2", experimenter="X1")
        self.e2 = e2
        e3 = Experiment(project="E3")
        self.e3 = e3

        t1 = Trial(rt=1, response="resp_0")
        self.t1 = t1
        t2 = Trial(rt=2, response="resp_1")
        t3 = Trial(rt=3, response="noresp")
        t4 = Trial(rt=4, response="resp_1")

        s1_1 = Session(count=1, category1=0)
        self.s1_1 = s1_1
        s1_2 = Session(count=2, category1=1)
        s2_1 = Session(count=3, category1=0)
        s2_2 = Session(count=4, category1=1)
        s3_1 = Session(count=5, category1=0)
        s4_1 = Session(count=6, category1=1)

        e1.attach("Observed by", self.o1)
        e1.attach("Observed by", self.o2)
        e2.attach("Observed by", self.o1)
        e2.attach("Observed by", self.o3)
        e3.attach("Observed by", self.o3)

        self.m.save(self.o1, self.o2, self.o3, e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

        t1.parent = e1
        t2.parent = e1
        t3.parent = e2
        t4.parent = e3

        s1_1.parent = t1
        s1_2.parent = t1
        s2_1.parent = t2
        s2_2.parent = t2
        s3_1.parent = t3
        s4_1.parent = t4

        self.m.save(e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

    def test_simple(self):
        sessions = self.m.find_complex("Session", {"_parent": ("Trial", {"rt": gt(2)})})
        # there should be two sessions with Trial parent and Trial.rt > 2: s3_1 and s4_1
        self.assertEqual(len(sessions), 2)
        counts = set([s.params["count"] for s in sessions])
        self.assertEqual(set([5, 6]), counts)

        # find the experiment with the child trial(rt=3)
        experiment = self.m.find_complex("Experiment", {"_child": ("Trial", {"rt": eq(3)})})[0]
        self.assertEqual(experiment, self.e2)
        
        # find the trial with child session(count=1)
        trial = self.m.find_complex("Trial", {"_child": ("Session", {"count": eq(1)})})[0]
        self.assertEqual(trial, self.t1)

        # find the experiments with observer Observer(name="A")
        experiments = self.m.find_complex("Experiment", {("_context", "Observed by"): ("Observer", {"name": "A"})})
        self.assertEqual(set(experiments), set([self.e1, self.e2]))

        # find the experiments with observer Observer(name="A") or Observer(name="B")
        experiments = self.m.find_complex("Experiment", {("_context", "Observed by"): {"_any": [("Observer", {"name": "A"}),
                                                                                              ("Observer", {"name": "C"})]}})
        self.assertEqual(set(experiments), set([self.e1, self.e2, self.e3]))

    def test_find_with(self):
        # we can also do parent relations with find_with
        sessions = self.m.find_with("Session", {"_parent": ("Trial", {"rt": gt(2)})})
        # there should be two sessions with Trial parent and Trial.rt > 2: s3_1 and s4_1
        self.assertEqual(len(sessions), 2)
        counts = set([s.params["count"] for s in sessions])
        self.assertEqual(set([5, 6]), counts)

        # retrieve all Sessions with parent Trial and response=resp%
        sessions = self.m.find_with("Session", {"_parent": ("Trial", {"response": "resp%"})})
        self.assertEqual(len(sessions), 5)

        # retrieve all Sessions with parent Trial and response=resp% and rt!=2
        sessions = self.m.find_with("Session", {"_parent": ("Trial", {"response": "resp%",
                                                                      "_with": lambda e: e.params["rt"] != 2})})
        self.assertEqual(len(sessions), 3)

    def test_find_by_object(self):
        # find the experiments with observer o1
        experiments = self.m.find_complex("Experiment", {("_context", "Observed by"): self.o1})
        self.assertEqual(set(experiments), set([self.e1, self.e2]))

    def test_complicated(self):

        # Session.params['count'] should be even
        param_check = {"count": lambda count: count % 2 == 0}

        sessions = self.m.find_complex("Session", param_check)
        self.assertEqual(len(sessions), 3)

        # Two sessions should have a count <= 3 and category1 == 0
        with_check = {"_with": lambda entity: entity.params['count'] <= 3 and entity.params['category1'] == 0}
        sessions = self.m.find_complex("Session", with_check)
        self.assertEqual(len(sessions), 2)
        counts = set([s.params["count"] for s in sessions])
        self.assertEqual(set([1, 3]), counts)

        parent_check = {
            "_parent": {"_any":
                [
                    ("Trial", {
                        "_parent": ("Experiment", {"project": "E1"})
                    }),
                    ("Trial", {
                          "_parent": ("Experiment", {"project": "E2", "experimenter": "X1"})}),
                    self.t1
                ]
            }
        }

        sessions = self.m.find_complex("Session", parent_check)
        self.assertEqual(len(sessions), 5)

        sessions = self.m.find_complex("Session", dict(
            param_check.items() + with_check.items() + parent_check.items()))
        self.assertEqual(len(sessions), 0) # TODO Prepare a better test and example


class TestTypeMagic(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_rebrand(self):
        class E0(Entity):
            declared_params = {
                "q": "integer"
            }

        class E1(Entity):
            declared_params = {
                "q": "integer",
                "q1": "integer"
            }

        e0 = E0(q=100)
        self.m.save(e0)

        self.m.rebrand(E0, E1)

        # trying to load something from e0 now raises
        self.assertRaises(DetachedInstanceError, lambda: e0.type)
        self.assertRaises(DetachedInstanceError, lambda: dict(e0.params)) # lazy, so we call dict

        e1 = self.m.find_roots()[0]

        #self.m.session.expunge(e1)

        import pdb
        #pdb.set_trace()

        self.assertEqual(e1._type, E1.__name__)
        self.assertEqual(e1.params["q"], 100)

        e1.params["q"] = 0
        e1.params["q1"] = 0

    def test_multi_step_rebrand(self):
        class MyEntity1(Entity):
            declared_params = {
                "name": "string",
                "version": "integer"
            }

        class MyEntity2a(Entity):
            declared_params = {
                "name": "string",
                "version": "integer",
                "version_string": "string",
                "release_date": "date"
            }

        class MyEntity2b(Entity):
            declared_params = {
                "name": "string",
                "version_string": "string",
                "release_date": "date"
            }

        class MyEntity3(Entity):
            declared_params = {
                "name": "string",
                "version": "string",
                "release_date": "date"
            }

        orig_entities = [
            MyEntity1(name="abc", version=1),
            MyEntity1(name="def", version=2),
            MyEntity1(name="ghi", version=3),
            MyEntity1(name="jkl", version=4),
            MyEntity1(name="mno", version=5),
            MyEntity1(name="pqr", version=6),
            MyEntity1(name="stu", version=7)
        ]

        self.m.save(*orig_entities)

        def change_version_string_add_date(e, params):
            params["version_string"] = str(params["version"])
            del params["version"]
            params["release_date"] = datetime.date.today()
            return params

        def change_version_string(e, params):
            params["version"] = params["version_string"]
            del params["version_string"]
            return params

        self.assertEqual(len(self.m.find(MyEntity1).all()), 7)
        self.assertEqual(len(self.m.find(MyEntity3).all()), 0)

        version_1 = [e.params["version"] for e in self.m.find(MyEntity1)]
        self.assertEqual(len(version_1), 7)
        self.assertTrue(all(type(v)==int for v in version_1))

        # we cannot rebrand directly:
        self.assertRaises(ValueError, self.m.rebrand, MyEntity1, MyEntity3)

        # do the rebranding
        self.m.rebrand(MyEntity1, MyEntity2a, after=change_version_string_add_date)

        # still won’t work to do this directly
        self.assertRaises(ValueError, self.m.rebrand, MyEntity2a, MyEntity3)
        self.m.rebrand(MyEntity2a, MyEntity2b)

        self.m.rebrand(MyEntity2b, MyEntity3, after=change_version_string)

        self.assertEqual(len(self.m.find(MyEntity1).all()), 0)
        self.assertEqual(len(self.m.find(MyEntity3).all()), 7)

        version_3 = [e.params["version"] for e in self.m.find(MyEntity3)]
        self.assertEqual(len(version_3), 7)
        self.assertTrue(all(isinstance(v, basestring) for v in version_3))



if __name__ == "__main__":
    unittest.main()
