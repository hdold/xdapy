# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper

from xdapy.parameters import ParameterMap

import unittest

class TestParameter(unittest.TestCase):
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        mapper = Mapper(self.connection)
        mapper.create_tables(overwrite=True)

    def tearDown(self):         
        pass
    
    def test_parameters(self):
        from datetime import datetime, date, time
        values = {
            "datetime": [datetime(2011, 1, 1, 12, 32, 11)],
            "time": [time(12, 32, 11)],
            "date": [date(2011, 1, 1)],
            "integer": [112, 20010213322],
            "float": [11.2, 200.10213322],
            "boolean": [True, False],
            "string": [u"Kleiner Text", u"äöü", u"Юникод"]}

        for type, vals in values.iteritems():
            for val in vals:
                param_class = ParameterMap[type]
                param_val = param_class("test", val)
                assert val == param_class.from_string(param_val.value_string)

if __name__ == '__main__':
    unittest.main()


