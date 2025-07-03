import json
import unittest
from io import StringIO
from typing import List

import pandas as pd

from meashalu.schemas.measeval import MeasEvalAnnotationInstance, MeasEvalAnnotationMeasurement


class TestMeasEvalAnnotationInstance(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(StringIO("""docId	annotSet	annotType	startOffset	endOffset	annotId	text	other
S0019103512003533-5300	1	Quantity	135	144	T1-1	80 mV m−1	{"unit": "mV m−1"}
S0019103512003533-5300	1	MeasuredEntity	117	131	T2-1	field strength	{"HasQuantity": "T1-1"}
S0019103512003533-5300	2	Quantity	220	237	T1-2	0.2 to 1.2 mW m−2	{"mods": ["IsRange"], "unit": "mW m−2"}
S0019103512003533-5300	2	MeasuredProperty	203	214	T3-2	energy flux	{"HasQuantity": "T1-2"}
S0019103512003533-5300	2	MeasuredEntity	29	37	T4-2	electron	{"HasProperty": "T3-2"}
S0019103512003533-5300	2	Qualifier	188	198	T5-2	increasing	{"Qualifies": "T3-2"}
S0019103512003533-5300	3	Quantity	252	262	T1-3	100 mV m−1	{"unit": "mV m−1"}
S0019103512003533-5300	3	MeasuredEntity	117	131	T2-3	field strength	{"HasQuantity": "T1-3"}
S0019103512003533-5300	4	Quantity	266	297	T1-4	increases from ∼550 K to 850 K.	{"mods": ["IsRange", "IsApproximate"], "unit": "K"}
S0019103512003533-5300	4	MeasuredProperty	149	160	T2-4	temperature	{"HasQuantity": "T1-4"}
S0019103512003533-5300	4	MeasuredEntity	391	413	T3-4	Saturn’s thermospheric	{"HasProperty": "T2-4"}
S0019103512003533-5300	4	Qualifier	239	262	T4-4	while at E = 100 mV m−1	{"Qualifies": "T2-4"}
S0019103512003533-5300	5	Quantity	526	532	T1-5	10 keV	{"unit": "keV"}
S0019103512003533-5300	5	MeasuredEntity	533	542	T2-5	particles	{"HasQuantity": "T1-5"}
S0019103512003533-5300	6	Quantity	613	619	T1-6	500 eV	{"unit": "eV"}
S0019103512003533-5300	6	MeasuredEntity	621	630	T2-6	electrons	{"HasQuantity": "T1-6"}
S0019103512003533-5300	6	Qualifier	607	611	T4-6	soft	{"Qualifies": "T2-6"}
"""), sep="\t")
        self.text = """The temperature changes with electron energy flux depend on the electric field strength that was set. For a moderate field strength of 80 mV m−1 the temperature is virtually constant when increasing the energy flux from 0.2 to 1.2 mW m−2, while at E = 100 mV m−1 it increases from ∼550 K to 850 K. Thus we can make the more general statement that for low to moderate electric field strength Saturn’s thermospheric temperatures are more responsive to changes in electric field strength than incident energetic electron flux of 10 keV particles. Temperatures are less responsive to changes in energy flux for soft (500 eV) electrons (not shown) as these do not penetrate deep enough into the atmosphere to significantly affect Pedersen and Hall conductances (Galand et al., 2011)."""

    def test_read(self):
        validated_data: List[MeasEvalAnnotationMeasurement] = []
        for item in self.df.to_dict(orient='records'):
            item['other'] = json.loads(item['other'])
            print(item)
            validated_data.append(MeasEvalAnnotationMeasurement(**item))
        instance = MeasEvalAnnotationInstance.from_entries(validated_data, self.text)
        instruction = instance.to_instruction()
        print(instruction)

class TestMeasEvalAnnotationInstanceError(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(StringIO("""docId	annotSet	annotType	startOffset	endOffset	annotId	text	other
S0019103512003533-5300	1	Quantity	135	144	T1-1	80 mV m−1	{"unit": "mV m−1"}
S0019103512003533-5300	1	MeasuredEntity	117	131	T2-1	field strength	{"HasQuantity": "T1-1"}
S0019103512003533-5300	2	Quantity	220	237	T1-2	0.2 to 1.2 mW m−2	{"mods": ["IsRange"], "unit": "mW m−2"}
S0019103512003533-5300	2	MeasuredProperty	203	214	T3-2	energy flux	{"HasQuantity": "T1-2"}
S0019103512003533-5300	2	MeasuredEntity	29	37	T4-2	electron	{"HasProperty": "T3-2"}
S0019103512003533-5300	2	Qualifier	188	198	T5-2	increasing	{"Qualifies": "T3-2"}
S0019103512003533-5300	3	Quantity	252	262	T1-3	100 mV m−1	{"unit": "mV m−1"}
S0019103512003533-5300	3	MeasuredEntity	117	131	T2-3	field strength	{"HasQuantity": "T1-3"}
S0019103512003533-5300	4	Quantity	266	297	T1-4	increases from ∼550 K to 850 K.	{"mods": ["IsRange", "IsApproximate"], "unit": "K"}
S0019103512003533-5300	4	MeasuredProperty	149	160	T2-4	temperature	{"HasQuantity": "T1-4"}
S0019103512003533-5301	4	MeasuredEntity	391	413	T3-4	Saturn’s thermospheric	{"HasProperty": "T2-4"}
S0019103512003533-5300	4	Qualifier	239	262	T4-4	while at E = 100 mV m−1	{"Qualifies": "T2-4"}
S0019103512003533-5300	5	Quantity	526	532	T1-5	10 keV	{"unit": "keV"}
S0019103512003533-5300	5	MeasuredEntity	533	542	T2-5	particles	{"HasQuantity": "T1-5"}
S0019103512003533-5300	6	Quantity	613	619	T1-6	500 eV	{"unit": "eV"}
S0019103512003533-5300	6	MeasuredEntity	621	630	T2-6	electrons	{"HasQuantity": "T1-6"}
S0019103512003533-5300	6	Qualifier	607	611	T4-6	soft	{"Qualifies": "T2-6"}
"""), sep="\t")
        self.text = """The temperature changes with electron energy flux depend on the electric field strength that was set. For a moderate field strength of 80 mV m−1 the temperature is virtually constant when increasing the energy flux from 0.2 to 1.2 mW m−2, while at E = 100 mV m−1 it increases from ∼550 K to 850 K. Thus we can make the more general statement that for low to moderate electric field strength Saturn’s thermospheric temperatures are more responsive to changes in electric field strength than incident energetic electron flux of 10 keV particles. Temperatures are less responsive to changes in energy flux for soft (500 eV) electrons (not shown) as these do not penetrate deep enough into the atmosphere to significantly affect Pedersen and Hall conductances (Galand et al., 2011)."""

    def test_read(self):
        validated_data: List[MeasEvalAnnotationMeasurement] = []
        for item in self.df.to_dict(orient='records'):
            item['other'] = json.loads(item['other'])
            validated_data.append(MeasEvalAnnotationMeasurement(**item))
        instance = MeasEvalAnnotationInstance.from_entries(validated_data, self.text)


if __name__ == '__main__':
    unittest.main()
