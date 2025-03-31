import random
import os
import json
from openai import OpenAI
import re
import pandas as pd
import traceback
from vladiate.validators import UniqueValidator, SetValidator, IntValidator, Validator, ValidationException, RegexValidator
import logging
from vladiate import Vlad, logs
import tempfile
from vladiate.inputs import LocalFile
import threading
from measeval_eval import check_reasoning_measeval
from grobid_eval import check_reasoning_grobid
message_template_grobid = '''
Instruction:
You are an expert in extracting structured annotations from text. Your task is to identify and classify measurements, along with relationships. Please follow the step-by-step reasoning process below and provide the output strictly in the Json format.
The basic JSON structure is the following,where measurements represent the list of extracted measurements:
    {
       "measurements": [
          {
              "type": ...
              "quantity*": ...
              "quantified": ...
          }
       ]
    }
constituted by the following components:
quantity represents the raw quantity
type describes the measurement nature, in particular it can be value, interval or list. Depending on it, the property related to the quantity will change according to the table below.
quantified contains the quantified object/substance in both raw and normalised expression,it should contain rawName field and normalizedName field,example of quantified:
"quantified": {
                    "rawName": "antibody",
                    "normalizedName": "antibody",
              }

Measurement has three types:

Measurement type	Quantity property name(s)	Object type
value	quantity	quantity object
interval	quantityLeast, quantityMost	quantity objects (2)
list	quantities	list of quantity objects



The quantity object follow the schema :

    "quantity": {
      "type": "time",
      "rawValue": "two",
      "rawUnit": {...}
      "parsedValue": {...}
      "normalizedQuantity": 120
      "normalizedUnit": {...}
    }
which has three main objects:

rawValue and rawUnit contains information as they appear in input
parsedValue contains parsed information
normalisedQuantity and normalisedUnit contains normalisation information

The list of unit and quantitiy object types (temperature, pressure, length, etc.) is controlled and based on SI definition. The type of unit and quantity object should be in the list below:["unknown","length","time","temperature","mass","luminous intensity","amount of substance","electric current","angle","solid angle","frequency","force","pressure","energy","power","electric charge","voltage","electric capacitance","electric resistance","electric conductance","electric field","magnetic flux","magnetization","mass magnetization","magnetic flux density","magnetic induction","magnetic field strength","magnetic field ratio","inductance","luminous flux","illuminance","luminance","radioactivity","absorbed dose","equivalent dose","attenuation","torque","dynamic viscosity","kinematic viscosity","acoustic pressure","mass flow-rate","volume flow-rate","air flow-rate","spectral responsivity","regular spectral transmittance","diffuse spectral reflectance","spectral flux density","reflectance","detector passband","thermal conductivity","thermal diffusivity","specific heat capacity","volumetric heat capacity","emission rate","catalytic activity","radiance","irradiance","emissivity","humidity","volume","velocity","area","concentration","density","acidity","fraction","VO2 max","count","acceleration","angle","diffusion flux","magnetic moment","atom mass unit","pace","maximum energy product","energy density","atomic ratio","weight ratio","mass accumulation rate","sedimentation rate","rotation"]
In the rawUnit and normalizedUnit, the "system" field is required to display the unit system where the unit is located. Its value must be one of the following: ["unknown", "SI base", "SI derived", "imperial", "us", "centimetre–gram–second", "metre-kilogram-second", "gaussian", "non SI"].
The normalizedUnit and rawUnit should contain a name field, a type field, and a system field. The name field represents the name of the unit. The value of the type field should be selected from the previously defined list of types, and the system field should indicate which unit system the unit belongs to. 

example of rawUnit and normalizedUnit:
"rawUnit": {
          "name": "months",
          "type": "time",
          "system": "non SI"
        }
"normalizedUnit": {
                    "name": "m",
                    "type": "length",
                    "system": "SI base"
                }




The normalizedQuantity represents the value after conversion to the standard unit.


parsedvalue is a structure used to represent the information of a parsed numerical value. It mainly includes the numerical value, name, structure type, and the parsed string representation.
Structure Composition
numeric (Required)
Description: Represents the actual numerical value, which is the core data of parsedvalue.
name (Optional)
Description: The name of the numerical value, which can be used to identify or describe the value. If not provided, it will be None.
structure (Optional)
Description: Represents the structural information of the numerical value, including the structure type and the formatted string. The specific structure is as follows:
type (Required)
Description: The structure type, which can take one of the following values:
NUMBER: Represents a numerical type.
ALPHABETIC: Represents an alphabetic type.
EXPONENT: Represents an exponent type.
TIME: Represents a time type.
UNKNOWN: Represents an unknown type.
formatted (Optional)
Description: The formatted string representation. If type is not UNKNOWN, this field cannot be None; if type is UNKNOWN, this field can be None.
parsed (Optional)
Description: The parsed string representation, which can be used to record the text form of the numerical value. If not provided, it will be None.
Validation Rules
When the type in structure is not UNKNOWN, the formatted field in structure cannot be None. 

normalisedQuantity and normalisedUnit contains normalisation information
example of parsedValue:
"parsedValue": {
                    "name": "0.1",
                    "numeric": 0.1,
                    "structure": {
                        "type": "NUMBER",
                        "formatted": "0.1"
                    },
                    "parsed": "0.1"
                }




please return a JSON response looking like

    {
      "measurements": [
          {
              "type": "value",
              "quantity": {
                  "type": "time",
                  "rawValue": "two",
                  "rawUnit": {
                      "name": "minutes",
                      "type": "time",
                      "system": "non SI",
                  },
                  "parsedValue": {
                      "numeric": 2,
                      "structure": {
                          "type": "ALPHABETIC",
                          "formatted": "two"
                      },
                      "parsed": "two"
                  },
                  "normalizedQuantity": 120,
                  "normalizedUnit": {
                      "name": "s",
                      "type": "time",
                      "system": "SI base"
                  },
              }
          }
      ]
    }
Another example of a quantity of type interval looks as below: :

    {
      "measurements": [
          {
              "type": "interval",
              "quantityLeast": {
                  "type": "time",
                  "rawValue": "1",
                  "rawUnit": {
                      "name": "minutes",
                      "type": "time",
                      "system": "non SI",
                  },
                  "parsedValue": {
                      "numeric": 1,
                      "structure": {
                          "type": "NUMBER",
                          "formatted": "1"
                      },
                      "parsed": "1"
                  },
                  "normalizedQuantity": 60,
                  "normalizedUnit": {
                      "name": "s",
                      "type": "time",
                      "system": "SI base"
                  },
              },
              "quantityMost": {
                  "type": "time",
                  "rawValue": "2",
                  "rawUnit": {
                      "name": "minutes",
                      "type": "time",
                      "system": "non SI",
                  },
                  "parsedValue": {
                      "numeric": 2,
                      "structure": {
                          "type": "NUMBER",
                          "formatted": "2"
                      },
                      "parsed": "2"
                  },
                  "normalizedQuantity": 120,
                  "normalizedUnit": {
                      "name": "s",
                      "type": "time",
                      "system": "SI base"
                  },
              }
          }
      ]
    }

    Input：%s
'''


message_template_measeval="""
Instruction:
You are an expert in extracting structured annotations from text. Your task is to identify and classify Quantities, MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships. Please follow the step-by-step reasoning process below and provide the output strictly in the specified TSV format.

---
Annotation Type Definitions:
1. Quantity: A value that can represent a Count (e.g., "5 apples") or a Measurement (e.g., "355 ml"). It may include optional Modifiers such as tolerances and must ideally relate to a MeasuredEntity or MeasuredProperty using the "HasQuantity" relationship. If no such entity exists, the Quantity can remain standalone. 
  - Example: "355 ml" in "The soda can's volume was 355 ml."
2. MeasuredEntity: The object or entity associated with a Quantity. It must relate to the Quantity via "HasQuantity". If applicable, it can also relate to a MeasuredProperty using "HasProperty". 
  - Example: "soda can" in "The soda can's volume was 355 ml."
3. MeasuredProperty: A descriptive property linked to both a MeasuredEntity (via "HasProperty") and a Quantity (via "HasQuantity"). It is optional. 
  - Example: "volume" in "The soda can's volume was 355 ml."
4. Qualifier: An optional span describing conditions or attributes that affect a Quantity, MeasuredEntity, or MeasuredProperty. It is related using the "Qualifies" relationship. 
  - Example: "after I drank half the can" in "The can contained 175 ml of soda after I drank half the can."
5. Unit: The unit of a Quantity, typically included within the Quantity span (e.g., "ml").

---
Relationships Definitions:
1. HasQuantity: Links a MeasuredEntity or MeasuredProperty to a Quantity.
2. HasProperty: Links a MeasuredEntity to a MeasuredProperty.
3. Qualifies: Links a Qualifier to a Quantity, MeasuredEntity, or MeasuredProperty.

---
Output Format (TSV Fields):
- annotSet: The annotation set ID (starting from 1 for each logical grouping of related annotations).
- annotType: One of the following types: Quantity, MeasuredEntity, MeasuredProperty, or Qualifier.
- annotId: A unique identifier for the annotation (e.g., T1, T2), numbered sequentially within each annotSet.
- text: The exact text of the annotation from the input.
- other: If annotType is Quantities: Extract all phrases involving quantities, specifying their unit and modifiers (if any). Include unit (e.g., "kg", "ppm"), ensure that all modifiers are placed inside "mods" (e.g., "mods": ["IsCount"]), and si (SI equivalent of the unit, if applicable). Optional modifiers include IsApproximate (indicating approximate values, e.g., "around 1300 m/s"), IsCount (indicating a count, e.g., "four samples"), IsRange (indicating a range, e.g., "1.5-2.6m"), IsList (indicating a list of quantities, e.g., "4.5kg, 6kg, 13kg"), IsMedian (indicating a median value, e.g., "10ppq"), IsMean (indicating a mean value, e.g., "9 ± 6"), and IsMeanHasSD (indicating a mean value with standard deviation, e.g., "1.23 ± 0.25").
Example: {"mods": ["IsMean"], "unit": "years"}
else if annotType is Other types (e.g., MeasuredEntities, MeasuredProperties, Qualifier,etc.):You must annotate relationships between entities using the format {relationType: targetAnnotation}.
Examples: if annotType is MeasuredEntities:{"HasProperty": "T21-4"},MeasyredProperties:{"HasQuantity":"T3-2"},Qualifier:{"Qualifies": "T4-5"}
---

Annotation Steps:
Step 1: Extract Quantities
1. Annotation of Quantities: 
  - Identify and annotate all Quantities in the paragraph.
  - Quantities may include values and units (measurements), or just values (counts).
  - If a quantity involves a modifier such as "approximately" or symbols like ">", include it if adjacent to the quantity span.
  - Counts of entities (e.g., "five samples") should also be annotated as Quantities.
2. Example Process: 
  - Read through the paragraph and identify each quantity, whether numeric (e.g., "5", "355") or descriptive (e.g., "room temperature", "sea level").
  - Annotate any numbers or phrases that represent quantities, including both measurements and counts.

---
Step 2: For Each Quanties，Extract Quantity Modifiers, Units, and Additional Spans and Relations
1. Quantity Modifiers and Units:
  - Correct the Quantity if necessary, then annotate any relevant Modifiers and Units for the Quantity.
  - Add a "Unit" span for the relevant unit if applicable.
  - If the Quantity is approximate, include the text indicating this in the span and tick the "IsApproximate" box.
  - If the Quantity represents a count and lacks a corresponding unit, tick the "IsCount" box.
2. Special Quantity Modifiers:
  - IsApproximate: Indicates the Quantity is an approximation (e.g., "around 1300 m/s").
  - IsCount: Indicates a count of entities (e.g., "four transits").
  - IsRange: Denotes a range of values (e.g., "1.5–2.6 m").
  - IsList: Denotes a list of quantities (e.g., "4.5 kg, 6 kg, and 13 kg").
  - IsMean: Indicates an average value (e.g., "490 K").
  - IsMedian: Indicates a median value (e.g., "10 ppq").
  - IsMeanHasSD: Indicates a mean with standard deviation (e.g., "1.23±0.25‰").
  - HasTolerance: Indicates tolerance (e.g., "93.90±0.15 Ma").
3. Additional Spans and Relations:
  - Mark the MeasuredEntity associated with the Quantity.
  - Mark the MeasuredProperty, if present.
  - Mark any necessary Qualifier spans that provide context to interpret the Quantity.
  - Be sure to include modifying adjectives or nouns that describe the MeasuredEntity (e.g., "Venera-I spacecraft" instead of just "spacecraft").
4. Create Relationships:
  - HasQuantity: Connect the MeasuredEntity (or MeasuredProperty) to the Quantity.
  - HasProperty: Connect the MeasuredEntity to the MeasuredProperty if applicable.
  - Qualifies: If a modifier is not adjacent to the Quantity, link it to the relevant span using a "Qualifies" relationship.


Example Paragraph:
"The temperature of the solution was approximately 25°C, and the volume of the solvent was 500 milliliters. We also added 10 grams of salt to the solution."


Step 1: Extract Quantities
- Quantities: 
  - "approximately 25°C" (Temperature)
  - "500 milliliters" (Volume of solvent)
  - "10 grams" (Amount of salt)
Step 2: For Each Quanties，Extract Quantity Modifiers, Units, and Additional Spans and Relations
- Modifiers: 
  - "approximately" is a modifier for "25°C", marking it as IsApproximate.
- Units: 
  - "°C" for the temperature (25°C)
  - "milliliters" for the volume (500 milliliters)
  - "grams" for the amount of salt (10 grams)
- MeasuredEntities: 
  - "solution" (for temperature)
  - "solvent" (for volume)
  - "salt" (for amount)
- MeasuredProperties: 
  - "temperature" (for solution)
  - "volume" (for solvent)
  - "amount" (for salt)
- Relationships: 
  - These spans are related using three types of Relationships:
  - HasQuantity, which relates a MeasuredEntity or MeasuredProperty to a Qauntity;
  - HasProperty, which relates a MeasuredEntity to a MeasuredProperty; and
  - Qualifies, which relates a Qualifier to any MeasuredEntity, MeasuredProperty, or Quantity.

---

Final Output (TSV Format):

annotSet    annotType           annotId    text                other
1           Quantity            T1         approximately 25°C  {"unit": "°C", "mods": ["IsApproximate"]}
1           MeasuredProperty    T2         temperature         {"HasQuantity": "T1"}
1           MeasuredEntity      T3         solution            {"HasQuantity": "T1", "HasProperty":"T2"}
2           Quantity            T4         500 milliliters     {"unit": "milliliters"}
2           MeasuredProperty    T5         volume              {"HasQuantity": "T4"}
2           MeasuredEntity      T6         solvent             {"HasQuantity": "T4", "HasProperty": "T5"}
3           Quantity            T7         10 grams            {"unit": "grams"}
3           MeasuredProperty    T9         amount              {"HasQuantity": "T7"}
3           MeasuredEntity      T8         salt                {"HasQuantity": "T7", "HasProperty": "T8"}



 Input：%s

"""
reasoning_template_grobid = '''
    You are an expert in handling text data, now please help me wrap the JSON data in the following reasoning text with \'\'\' \'\'\', such as: \'\'\'{"quantity":100,"qualified":"name"}\'\'\'.If there are errors in the format of the JSON content, please correct them.Pay special attention to the end of elements within objects or arrays, ensuring there are no extraneous commas. And please keep the rest as it is.
    Please only output the reasoning text and don't add any of your own words. Do not modify any of the original content!
Input:%s
'''


if __name__ == "__main__":
    textpaths = [
        "data/train/text/"]

    client = OpenAI(api_key="sk-danqwpmat42akvfw",
                    base_url="https://cloud.infini-ai.com/maas/v1")

    typemap = {"Quantity": "QUANT",
            "MeasuredEntity": "ME",
            "MeasuredProperty": "MP",
            "Qualifier": "QUAL"}

    docIds = []
    textset = {}

    for fileset in textpaths:
        for fn in os.listdir(fileset):
            with open(fileset + fn) as textfile:
                text = textfile.read()  # .splitlines()
                textset[fn[:-4]] = text
                docIds.append(fn[:-4])
    ents = {}

    for docId in docIds:
        # docId = "S2213671113001306-910"
        print(docId)
        cnt = 3
        while cnt > 0:
            text = textset[docId]
            ents[docId] = {}
            response = client.chat.completions.create(
                model="pro-deepseek-r1",  # 填写需要调用的模型名称
                temperature=0.6,
                messages=[{"role": "user", "content": "You are an expert in quantity relations extraction."},
                        {"role": "user", "content": message_template_measeval % (text)}])
            result_measeval = response.choices[0].message.content
            reasoning_measeval = response.choices[0].message.reasoning_content
            print("finish measeval---------------------------------------------")
            try:
                check_reasoning_measeval(reasoning_measeval)
                break
            except Exception as e:
                cnt -=1
                print(e)
                continue
        if cnt ==0: continue

        cnt = 3
        while cnt>0:
            response = client.chat.completions.create(
                model="pro-deepseek-r1",  # 填写需要调用的模型名称
                temperature=0.6,
                messages=[{"role": "user", "content": "You are an expert in quantity relations extraction."},
                        {"role": "user", "content": message_template_grobid % (text)}])
            result_grobid = response.choices[0].message.content
            reasoning_grobid = response.choices[0].message.reasoning_content        


            processed_reasoning = client.chat.completions.create(
            model="qwen2.5-72b-instruct",  # 填写需要调用的模型名称
            messages=[{"role": "user", "content": "You are a text processing assistant proficient in handling text data"},
                    {"role": "user", "content": reasoning_template_grobid % (reasoning_grobid)}])
            processed_reasoning = processed_reasoning.choices[0].message.content
            print("finish grobid----------------------------------------")
            try:
                check_reasoning_grobid(processed_reasoning)
                break
            except Exception as e:
                cnt -=1
                print(e)
                continue
        if cnt ==0: continue

        reasoning_path = 'First, let me think in the Grobid-quantity way:\n <Grobid-quantity>\n'+processed_reasoning+'\n<\Grobid-quantity>\n\n Then, armed with the information obtained from thinking in the grobid-quantity format, I will continue my thinking from the perspective of MeasEval.\n<MeasEval>\n'+reasoning_measeval+'\n<\MeasEval>'

        file_path = f"reasoning_path/{docId}.txt"
                # 写入文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(reasoning_path)