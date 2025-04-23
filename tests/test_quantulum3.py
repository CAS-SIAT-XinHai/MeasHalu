import json
import unittest

from quantulum3 import parser

from meashalu.schemas.quantulum import QuantulumAnnotationEntityType, QuantulumAnnotationQuantity
from meashalu.schemas.quantulum3 import Quantulum3AnnotationInstance


class TestQuantulum3AnnotationInstance(unittest.TestCase):
    def setUp(self):
        pass

    def test_quantulum3(self):
        quants = parser.parse('I want 2 liters of wine')
        print(quants)

        print(quants[0].unit)

        print(quants[0].unit.entity)

        print(QuantulumAnnotationEntityType.ACCELERATION.value)

    def test_get_quantity(self):
        with open('quantulum_tests.json') as f:
            tests = json.load(f)

        for test in tests:
            for quantity in parser.parse(test['req']):
                try:
                    instance = QuantulumAnnotationQuantity.from_quantulum(quantity)
                    # print(instance.model_dump_json(indent=2))
                except Exception as e:
                    print(e)
                    print(test)
                    print(quantity)
                    print(quantity.unit)
                    print(quantity.unit.entity)

    def test_get_quantity_3(self):
        with open('quantulum_tests.json') as f:
            tests = json.load(f)

        for test in tests:
            instance = Quantulum3AnnotationInstance.from_quantulum(parser.parse(test['req']))
            print(instance)
