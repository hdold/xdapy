from xdapy import Mapper, Connection
from xdapy.structures import EntityObject

class E(EntityObject):
    parameter_types = {}

connection = Connection.profile("test")#, echo=True) # use standard profile
m = Mapper(connection)
m.create_tables(overwrite=True)

m.register(E)

f = open("10M.dat")
#f = open("100M.dat")
#f = open("1G.dat")
e = E()
m.save(e)

import pdb
#pdb.set_trace()

e.data["100M"].mimetype = "a"

e.data["100M"].put("f")
print e.data["100M"].get_string()

e.data["100M"].put(f)

print e.data["100M"].mimetype
print "CHUNKS"
print e.data["100M"].chunks()
print e.data["100M"].chunk_ids()

m.save(e)
f.close()


ee = m.find_all(E)

for e in ee:

    out = open("out.dat", "w")
    e.data["100M"].get(out)
    print e.data["100M"].size()
    print e.data["100M"].is_consistent()
    print ""
    print "CHUNKS"
    print e.data["100M"].chunks()
    print e.data["100M"].chunk_ids()
    print ""
    print "KEYS"
    print e.data.keys()
    e.data["100M"].delete()
    out.close()
    
    m.delete(e)


