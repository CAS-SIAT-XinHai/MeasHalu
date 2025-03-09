import copy
import json
import unittest

from meashalu.schemas.grobid_quantities import GrobidQuantitiesAnnotationInstance


class TestGrobidQuantitiesAnnotationInstance(unittest.TestCase):
    def setUp(self):
        with open("grobid_quantities_pdf_1.json") as f:
            self.data = json.load(f)

    def test_read(self):
        for i in range(len(self.data['measurements'])):
            data = copy.deepcopy(self.data)
            data['measurements'] = data['measurements'][:i + 1]
            print(data['measurements'][-1])
            instance = GrobidQuantitiesAnnotationInstance.model_validate(data)
            print(instance)


class TestGrobidQuantitiesAnnotationInstance2(unittest.TestCase):
    def setUp(self):
        with open("grobid_quantities_pdf_2.json") as f:
            self.data = json.load(f)

    def test_read(self):
        for i in range(len(self.data['measurements'])):
            data = copy.deepcopy(self.data)
            data['measurements'] = data['measurements'][:i + 1]
            print(data['measurements'][-1])
            instance = GrobidQuantitiesAnnotationInstance.model_validate(data)
            print(instance)


class TestGrobidQuantitiesAnnotationInstance3(unittest.TestCase):
    def setUp(self):
        with open("grobid_quantities_pdf_3.json") as f:
            self.data = json.load(f)

    def test_read(self):
        for i in range(len(self.data['measurements'])):
            data = copy.deepcopy(self.data)
            data['measurements'] = data['measurements'][:i + 1]
            print(data['measurements'][-1])
            instance = GrobidQuantitiesAnnotationInstance.model_validate(data)
            print(instance)


if __name__ == '__main__':
    unittest.main()
