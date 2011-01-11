# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper

connection = Connection(profile="test") # use standard profile
print connection.configuration
m = Mapper(connection)
m.create_tables(overwrite=True)

from xdapy.objects import Experiment, Observer, Trial, Session
from xdapy.structures import Context

f = open("xml.xml")
xml = f.read()
m.typesFromXML(xml)

m.session.add_all(m.fromXML(xml))
m.session.commit()
xml = m.toXMl()
print xml


m.register(Observer)
m.register(Experiment)
m.register(Trial)
m.register(Session)

e1 = Experiment(project='MyProject', experimenter="John Do")
e1.param['project'] = "NoProject"
m.save(e1)
m.save(e1)
m.save(e1)
m.save(e1)

e2 = Experiment(project='YourProject', experimenter="John Doe")
o1 = Observer(name="Max Mustermann", handedness="right", age=26)
o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)   
o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
print o3.param["name"]

import datetime
s1 = Session(date=datetime.date.today())

s2 = Session(date=datetime.date.today())
#    e1.context.append(Context(context=s2))
s2.context.append(Context(context=e1, note="Some Context"))

#all objects are root
#m.save(e1)
#m.save(e2, o1, o2, o3)
#m.save(s1, s2)

m.session.add_all([e1, e2, o1, o2, o3, s1, s2])

m.session.commit()

#    m.connect_objects(e1, o1)
#    m.connect_objects(o1, o2)

o1.parent = e1

#    print m.get_children(e1)
#    print m.get_children(o1, 1)   

# print m.get_data_matrix([], {'Observer':['age','name']})

#only e1 and e2 are root
#    m.connect_objects(e1, o1)
#    m.connect_objects(e1, o2, True)
#    m.connect_objects(e2, o3)
#    m.connect_objects(e1, o3)
print "---"
experiments = m.find_all(Experiment)

for num, experiment in enumerate(experiments):
    print experiment._parameterdict
#        experiment.param["countme"] = num
    experiment.param["project"] = "PPP" + str(num)

experiments = m.find_all(Experiment(project="PPP1"))
for num, experiment in enumerate(experiments):
    print experiment._parameterdict
    
e1.data = {"hlkk": "lkjlkjkl#√§jkljysdsa"}

m.save(e1)


o = {}

from xdapy.objects import EntityObject
print EntityObject.__subclasses__()

o["otherObj"] = type("otherObj", (EntityObject,), {'parameterDefaults': {'myParam': 'string'}})

print [s.__name__ for s in EntityObject.__subclasses__()]
oo = o["otherObj"](myParam="Hey")
m.save(oo)

m.session.commit()

#    m.session.delete(e1)
m.session.commit()

def gte(v):
    return lambda type: type >= v

def gt(v):
    return lambda type: type > v

def lte(v):
    return lambda type: type <= v

def lt(v):
    return lambda type: type < v

def between(v1, v2):
    return lambda type: and_(gte(v1)(type), lte(v2)(type))

xml = m.toXMl()
print ""
print xml
m.session.add_all(m.fromXML(xml))
m.session.commit()

print m.find_all(Observer, filter={"name": "%Sor%"})
print m.find_all(Observer, filter={"name": ["%Sor%"]})
print m.find_all(Observer, filter={"age": range(30, 50), "name": ["%Sor%"]})
print m.find_all(Observer, filter={"age": between(30, 50)})
print m.find_all(Observer, filter={"age": 40})
print m.find_all(Observer, filter={"age": gt(10)})
print m.find_all(Session, filter={"date": gte(datetime.date.today())})

print m.get_data_matrix([Observer(name="Max Mustermann")], {Experiment:['project'], Observer:['age','name']})

