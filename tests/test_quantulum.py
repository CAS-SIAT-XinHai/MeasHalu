import json
import re
import unittest

from quantulum import parser
from quantulum.classes import Entity, Unit, Quantity
from quantulum.load import NAMES, ENTITIES, UNITS

from meashalu.schemas.quantulum import QuantulumAnnotationEntityType, QuantulumAnnotationQuantity, \
    QuantulumAnnotationInstance


def get_quantity(test, item):
    """Build a single quantity for the test."""
    try:
        unit = NAMES[item['unit']]
    except KeyError:
        try:
            entity = item['entity']
        except KeyError:
            print(('Could not find %s, provide "dimensions" and'
                   ' "entity"' % item['unit']))
            return
        if entity == 'unknown':
            dimensions = [{'base': NAMES[i['base']].entity.name,
                           'power': i['power']} for i in
                          item['dimensions']]
            entity = Entity(name='unknown', dimensions=dimensions)
        elif entity in ENTITIES:
            entity = ENTITIES[entity]
        else:
            print(('Could not find %s, provide "dimensions" and'
                   ' "entity"' % item['unit']))
            return
        unit = Unit(name=item['unit'],
                    dimensions=item['dimensions'],
                    entity=entity)
    try:
        span = next(re.finditer(re.escape(item['surface']),
                                test['req'])).span()
    except StopIteration:
        print('Surface mismatch for "%s"' % test['req'])
        return

    uncert = None
    if 'uncertainty' in item:
        uncert = item['uncertainty']

    quantity = Quantity(value=item['value'],
                        unit=unit,
                        surface=item['surface'],
                        span=span,
                        uncertainty=uncert)

    return quantity


class TestQuantulumAnnotationInstance(unittest.TestCase):
    def setUp(self):
        pass

    def test_quantulum_entities(self):
        base = set()
        name = set()
        with open('quantulum_entities.json') as f:
            for item in json.load(f):
                if item['dimensions']:
                    for dimension in item['dimensions']:
                        base.add(dimension['base'])
                name.add(item['name'])
        print(base)
        for item in base:
            print("_".join(item.upper().split()), "=", f'"{item}"')

        with open('quantulum_entities.json') as f:
            for item in json.load(f):
                print("_".join(item['name'].upper().split()), "=", f'"{item['name']}"', end=",")
                print(f'"{item['uri']}"', end=",")
                print("[", end="")
                if item['dimensions']:
                    for dimension in item['dimensions']:
                        print(
                            f"QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.{dimension['base'].upper()}, power={dimension['power']})",
                            end=",")
                print("]")

    def test_quantulum_units(self):
        base = set()
        name = set()
        with open('quantulum_units.json') as f:
            for item in json.load(f):
                if item['dimensions']:
                    for dimension in item['dimensions']:
                        base.add(dimension['base'])
                name.add(item['name'])
        print(base)
        for item in base:
            print("_".join(item.upper().split()), "=", f'"{item}"')

        symbols = []
        with open('quantulum_units.json') as f:
            for item in json.load(f):
                print("_".join(item['name'].upper().split()).replace('-', '_'), "=", f'"{item['name']}"', end=",")
                print(json.dumps(item['surfaces']), end=",")
                print(f'QuantulumAnnotationEntityType.{"_".join(item['entity'].upper().split())}', end=",")
                print(f'"{item['URI']}"', end=",")
                print("[", end="")
                if item['dimensions']:
                    for dimension in item['dimensions']:
                        print(
                            f"QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.{dimension['base'].upper()}, power={dimension['power']})",
                            end=",")
                print("]", end=",")
                print(json.dumps(item['symbols']))
                # print("[", end="")
                # if item['symbols']:
                #     for symbol in item['symbols']:
                #         print(
                #             f"QuantulumAnnotationUnitSymbolType.{"_".join(symbol.upper().split())}",
                #             end=",")
                # print("]")

                for i, symbol in enumerate(item['symbols']):
                    if len(item['symbols']) > 1:
                        symbols.append(["_".join(item['name'].upper().split()) + f"_{i}", symbol])
                    else:
                        symbols.append(["_".join(item['name'].upper().split()), symbol])

        for name, item in symbols:
            print(name, "=", f'"{item}"')

    def test_quantulum(self):
        quants = parser.parse('I want 2 liters of wine')
        print(quants)

        print(quants[0].unit)

        print(quants[0].unit.entity)

        print(UNITS.keys())
        print(QuantulumAnnotationEntityType.ACCELERATION.value)

    def test_get_quantity(self):
        with open('quantulum_tests.json') as f:
            tests = json.load(f)

        for test in tests:
            print(test)
            res = []
            for item in test['res']:
                quantity = get_quantity(test, item)
                if quantity is None:
                    return
                print(QuantulumAnnotationQuantity.from_quantulum(quantity))
                res.append(quantity)
            test['res'] = [i for i in res]
            print(test)
            # self.assertEqual(parser.parse(test['req']), test['res'])

    def test_get_quantity_2(self):
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
            instance = QuantulumAnnotationInstance.from_quantulum(parser.parse(test['req']))
            print(instance)