# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan
import re
from enum import Enum
from typing import List, Optional, Set, Union
from typing import NewType

import spacy
from pydantic import BaseModel, model_validator

nlp = spacy.load("en_core_web_sm")

MeasEvalAnnotationIdType = NewType("MeasEvalAnnotationIdType", str)


class MeasEvalAnnotationSpanType(str, Enum):
    """
    The basic annotation set defined here consists of 4 types of spans, with 3 types of relationship between them.
    """

    """
    The starting point for annotations, a Quantity is either a Count, consisting of a value, or a Measurement, consisting of a value and usually a unit. A Quantity can additionally include optional Modifiers like tolerances. A Quantity can have a relationship from either a MeasuredProperty or MeasuredEntity span via a HasQuantity relationship. If no MeasuredEntity can be identified, the Quantity must be standalone, with no relationships. See MeasuredEntity below for more information.

    The soda can's volume was *355 ml*.
    """
    Quantity = "Quantity"

    """
    A required (if possible) span that has a given Quantity either as its direct value or indirectly via a MeasuredProperty. Every Quantity should ideally be associated with a MeasuredEntity. If no relevant information appears in the text, the Quantity can be standalone, but can have no other relationships. A MeasuredEntity can be related to either a MeasuredProperty by a HasProperty relationship, or to a Quantity by a HasQuantity relationship.

    The *soda can*'s volume was 355 ml.
    """
    MeasuredEntity = "MeasuredEntity"

    """
    An optional span associated with both a MeasuredEntity and a Quantity. Not every Quantity will be associated with a MeasuredProperty. A MeasuredProperty must be related from a MeasuredEntity by a HasProperty relationship, and must be related to a Quantity through the HasQuantity relationship.

    The soda can's *volume* was 355 ml.
    """
    MeasuredProperty = "MeasuredProperty"

    """ 
    An optional Qualifier span describing special circumstances which affect a particular measurement. Qualifiers can be related to any MeasuredEntity, MeasuredProperty, or Quantity by a Qualifies relationship.

    The can contained 175 ml of soda *after I drank half the can*.
    """
    Qualifier = "Qualifier"

    """
    A required (if possible) span, usually contained within the Quantity span, denoting the Unit of measurement used in the Quantity.

    The soda can's volume was 355 *ml*.
    """
    Unit = "Unit"


class MeasEvalAnnotationRelationshipType(str, Enum):
    """"""
    """
    HasQuantity, which relates a MeasuredEntity or MeasuredProperty to a Qauntity;
    """
    HasQuantity = "HasQuantity"

    """
    HasProperty, which relates a MeasuredEntity to a MeasuredProperty;
    """
    HasProperty = "HasProperty"

    """
    Qualifies, which relates a Qualifier to any MeasuredEntity, MeasuredProperty, or Quantity.
    """
    Qualifies = "Qualifies"


class MeasEvalAnnotationQuantityModifierType(str, Enum):
    """"""

    """
    "Around" is included as part of the quantity, as it is the term that indicates the approximate nature of the value.

    If this flag is not adjacent to the Quantity, it can also be included in the MeasuredProperty, or as a separate Qualifier qualifying the Quantity. See Appendix for further examples.

    Note that the ME is not just "winds", as we try to include adjectives and important identifying information in spans.
    
    Example:
    The polar forcing via ion drag generates strong westward (sub-corotating) winds at a peak velocity of around 1300 m s−1 near 82° latitude.

    Quant: around 1300 m s−1
    MP: peak velocity
    ME: strong westward (sub-corotating) winds
    Qual: near 82° latitude
    """
    IsApproximate = "IsApproximate"

    """
    Counts should not have MeasuredProperties, only MeasuredEntities. Counts must not be associated with Unit information.
    
    Example:
    This detection was based on four transits observed with the Space Telescope Imaging Spectrograph (STIS) onboard the Hubble Space Telescope (HST) (Brown et al., 2001).

    Quant: four
    ME: transits
    """
    IsCount = "IsCount"

    """
    1.5-2.6 m is a simple range. Not shown here are open ended ranges where the text says something like "greater than" or "less than". Treat those ranges without an upper or lower bound. Include that text in the span of the quantity and modifier.
    
    Example:
    Concentrations of salts in Mars soil assuming deposition during the Amazonian, a soil density of 1 g cm−3, and mixing in a range of 1.5–2.6 m depth.

    Quant: range of 1.5–2.6 m
    MP: depth
    ME: Mars soil
    """
    IsRange = "IsRange"

    """
    Lists of quantities should usually be annotated as one annotation with the "isList" attribute. The exception to this is when lists clearly differentiate between separate MeasuredEntities, MeasureProperties, or Qualifiers, such as "The apple had a diameter, circumference, and weight of 2.5 inches, 6 inches, and 9 oz respectively."

    For lists that repeat the Unit, only add one Unit span once using the last instance included in the span.
    
    Example:
    Effect of bed inventory on increase of solid minor element concentrations for bed inventories of 4.5 kg, 6 kg and 13 kg CaCO3.

    Quant: 4.5 kg, 6 kg and 13 kg
    MP: CaCO3
    ME: bed inventories
    """
    IsList = "IsList"

    """
    Note that in this example, there is another Quantity, this time a range, contained within the Qualifier. This will be managed as a separate Quantity annotation, with it's own MeasuredEntity, Unit, etc.
    
    Example:
    Despite direct solar EUV heating of Saturn’s upper atmosphere representing a minor energy source only, it is however important to note that solar EUV and shorter wavelength radiation is responsible for the majority of ionisation, and thus conductivity, outside of the narrow band of high latitude electron precipitation. In our solstice simulation (R19) we find exospheric temperatures averaged from 74°S to 90°S (the summer polar region) of 490 K.
    
    Quant: 490 K
    MP: exospheric temperatures
    ME: solstice simulation (R19)
    Qual: averaged, from 74°S to 90°S (the summer polar region)
    """
    IsMean = "IsMean"

    """
    Note the mention of median, which has been underlined for clarity.
    
    Example:        
    If we use a median Os abundance in seawater of 10 ppq we can evaluate the approximate Os contribution from the Caribbean LIP to the global ocean using a progressive mixing model.
    
    Quant: 10 ppq
    MP: Os abundance
    ME: seawater
    Qual: median
    """
    IsMedian = "IsMedian"

    """
    Note the mention of mean and SD, which has been underlined.
    
    Example:
    Samples were measured relative to the NIST RM 8546 standard. The external diatomite standard (1.26±0.2‰, Reynolds et al., 2007) yielded a mean and 2SD of 1.23±0.25‰ (n=104).

    Quant: 1.23±0.25‰
    ME: Samples
    Qual: mean and 2SD, external diatomite standard
    """
    IsMeanHasSD = "IsMeanHasSD"

    """
    Note the mention of average, which has been underlined, and which in this case is not adjacent to the Quantity and is marked as part of the MeasuredProperty.

    Also note that here, the ± represents a tolerance rather than an Standard Deviation, as there is no Mean.

    Example:
    Woods et al. (2000) studied the variability of solar Lyman α emissions based on satellite observations spanning four and a half solar cycles between 1947 and 1999. They found that the average variability during one solar rotation was found to be 9 ± 6%.

    Quant: 9 ± 6%
    MP: average variability
    ME: solar Lyman α emissions
    Qual: during one solar rotation
    """
    IsMeanHasTolerance = "IsMeanHasTolerance"

    """
    Example:
    Even higher temperatures in Saturn’s auroral oval of (563–624) ± 30 K were derived from Cassini VIMS observations by Stallard et al.

    Quant: (563–624) ± 30 K
    MP: temperatures
    ME: Saturn’s auroral oval
    """
    IsRangeHasTolerance = "IsRangeHasTolerance"

    """
    Recent sanidine 40Ar/39Ar and zircon 206Pb/238U geochronology integrated with astrochronology constrain the CTB at 93.90±0.15 Ma.

    Quant: 93.90±0.15 Ma.
    ME: CTB
    """
    HasTolerance = "HasTolerance"


class MeasEvalAnnotationQuantityModifiersAndUnits(BaseModel):
    mods: Optional[List[MeasEvalAnnotationQuantityModifierType]] = None
    unit: Optional[str] = None
    si: Optional[str] = None


class MeasEvalAnnotationQuantityQualifiers(BaseModel):
    Qualifies: MeasEvalAnnotationIdType


class MeasEvalAnnotationMeasuredEntityProperty(BaseModel):
    """
    Create a "HasProperty" relationship from the MeasuredEntity to the MeasuredProperty where there is a MeasuredProperty, connecting to the Quantity.
    """
    HasProperty: MeasEvalAnnotationIdType


class MeasEvalAnnotationMeasuredPropertyQuantity(BaseModel):
    """
    Create a "HasQuantity" relationship from the MeasuredProperty, if there is one, to the Quantity.

    If there is no MeasuredProperty, created a "HasQuantity" relationship directly from the MeasuredEntity to the Quantity.
    """
    HasQuantity: MeasEvalAnnotationIdType


class MeasEvalAnnotationMeasurement(BaseModel):
    """
    For the TSV format, the following fields are used:

    docId: points to the document ID of the example.
    annotSet: refers to the logical grouping of annotations, one per annotated quantity, in the order that they appear in the text document.
    annotType, one of Quantity, MeasuredEntity, MeasuredProperty, or Qualifier.
    startOffset: character offset of the start of the annotation in the text.
    endOffset: character offset pointing to the character after the last character in the annotation.
    annotId: an identifier for the row in the file, unique per annotSet.
    text: the text of the annotation.
    other: additional properties used in the task, including:
        For Quantities: other holds the unit: the unit in the text; si: the SI equivalant of this unit, if applicable, and mods: a set of modifiers that further describe the Quantity.
        For MeasuredEntity, MeasuredProperty, and Qualifier, other holds the relationship type and target of the related span, in the form {relationType: targetAnnotation}
    """
    docId: str
    annotSet: int
    annotType: MeasEvalAnnotationSpanType
    startOffset: int
    endOffset: int
    annotId: MeasEvalAnnotationIdType
    text: str
    other: Optional[Union[
        MeasEvalAnnotationQuantityModifiersAndUnits,
        MeasEvalAnnotationQuantityQualifiers,
        MeasEvalAnnotationMeasuredEntityProperty,
        MeasEvalAnnotationMeasuredPropertyQuantity
    ]]

    @model_validator(mode='after')
    def check_annotation_id(self) -> 'MeasEvalAnnotationMeasurement':
        if not re.match(r"T\d+\-\d+", self.annotId):
            raise ValueError(
                "'annotId' does not match extpected format"
            )
        return self

    @model_validator(mode='after')
    def check_span_length(self) -> 'MeasEvalAnnotationMeasurement':
        expected_len = self.endOffset - self.startOffset
        text_len = len(self.text)
        if expected_len != text_len:
            raise ValueError(
                "'{}' length {} does not match extpected length /{}/".format(self.text, text_len, expected_len)
            )
        return self

    @model_validator(mode='after')
    def check_other_type(self) -> 'MeasEvalAnnotationMeasurement':
        if self.annotType == MeasEvalAnnotationSpanType.Quantity:
            if not isinstance(self.other, MeasEvalAnnotationQuantityModifiersAndUnits):
                raise ValueError(f"Annotation type is {self.annotType}, but other type is {type(self.other)}!")
        elif self.annotType == MeasEvalAnnotationSpanType.MeasuredEntity:
            if not isinstance(self.other,
                              Union[
                                  MeasEvalAnnotationMeasuredEntityProperty, MeasEvalAnnotationMeasuredPropertyQuantity]):
                raise ValueError(f"Annotation type is {self.annotType}, but other type is {type(self.other)}!")
        elif self.annotType == MeasEvalAnnotationSpanType.MeasuredProperty:
            if not isinstance(self.other, MeasEvalAnnotationMeasuredPropertyQuantity):
                raise ValueError(f"Annotation type is {self.annotType}, but other type is {type(self.other)}!")
        elif self.annotType == MeasEvalAnnotationSpanType.Qualifier:
            if not isinstance(self.other, MeasEvalAnnotationQuantityQualifiers):
                raise ValueError(f"Annotation type is {self.annotType}, but other type is {type(self.other)}!")
        return self


class MeasEvalAnnotationInstance(BaseModel):
    docId: str
    text: str
    entries: List[MeasEvalAnnotationMeasurement]
    annotSet: Set[int]

    @model_validator(mode='after')
    def check_unique_id(self):
        doc_ids = set([e.docId for e in self.entries])
        if len(doc_ids) != 1:
            raise ValueError(f"docId {doc_ids} is not unique!")

    @classmethod
    def from_entries(cls, entries: List[MeasEvalAnnotationMeasurement], text: str) -> 'MeasEvalAnnotationInstance':
        docId = entries[0].docId
        annotSet = set([e.annotSet for e in entries])
        return cls(docId=docId, text=text, entries=entries, annotSet=annotSet)

    def to_instruction_per_set(self, entries: List[MeasEvalAnnotationMeasurement], sentences: List[str]) -> str:
        
        # 

        # 1. (Necessary minimal change) Create a map for quick lookup of annotation targets
        entry_map = {e.annotId: e for e in entries}

        quantities = [e for e in entries if e.annotType == MeasEvalAnnotationSpanType.Quantity]
        entities = [e for e in entries if e.annotType == MeasEvalAnnotationSpanType.MeasuredEntity]

        assert len(quantities) == 1
        assert len(entities) == 1

        # print(quantities[0].other)
        # print(entities[0].other)

        quantity = quantities[0]
        if isinstance(quantity.other, MeasEvalAnnotationQuantityModifiersAndUnits):
            quantity_instruction = "[{text}], it has unit [{unit}].".format(text=quantity.text, unit=quantity.other.unit)
            if quantity.other.mods is not None:
                quantity_instruction += " The modifier for the quantity are [{mods}].".format(
                    mods=", ".join([m.value for m in quantity.other.mods]))
        else:
            quantity_instruction = quantity.text

        # -----------------------------------------------------------------------------------------
        # Modified Qualifier Logic Starts Here
        # -----------------------------------------------------------------------------------------
        qualifiers = [e for e in entries if e.annotType == MeasEvalAnnotationSpanType.Qualifier]
        
        qualifier_instruction = ""
        if qualifiers:
            for qualifier in qualifiers:
                # Assuming qualifier.other is MeasEvalAnnotationQuantityQualifiers based on BaseModel validator
                if qualifier.other and hasattr(qualifier.other, 'Qualifies'):
                    target_id = qualifier.other.Qualifies
                    target_entry = entry_map.get(target_id)
                    
                    if target_entry:
                        target_type = target_entry.annotType.value
                        target_text = target_entry.text
                        
                        qualifier_instruction += """ And there is a qualifier [{qualifier}] qualifies the [{target_type}].""".format(
                                qualifier=qualifier.text,
                                target_type=target_type,
                                target_text=target_text
                            )

            # Combine all qualifier descriptions
        else:
            qualifier_instruction = ""
        # -----------------------------------------------------------------------------------------
        # Modified Qualifier Logic Ends Here
        # -----------------------------------------------------------------------------------------

        entity = entities[0]
        entity_instruction = entity.text
        # print(entity.other)

        properties = [e.text for e in entries if e.annotType == MeasEvalAnnotationSpanType.MeasuredProperty]

        property_instruction = """The entity has the following property [{property}].""".format(property="\n".join(properties)) if len(properties) == 1 else ""


        return """From the target sentences: 
{sentences}

We can find the quantity with surface form {quantity}  This quantity is used to describe the entity [{entity}]. {property}{qualifier}""".format(
            sentences="\n".join(sentences),
            quantity=quantity_instruction,
            entity=entity_instruction,
            property=property_instruction,
            qualifier=qualifier_instruction # This will now inject the detailed Qualifier information
        )

    def to_instruction(self) -> str:
        doc = nlp(self.text)
        doc.set_extension("annotSet", default={}, force=True)
        for sent in doc.sents:
            for entry in self.entries:
                if entry.startOffset >= sent.start_char and entry.endOffset <= sent.end_char:
                    doc._.annotSet.setdefault(entry.annotSet, set())
                    doc._.annotSet[entry.annotSet].add(sent)

        instructions = []
        for aset in self.annotSet:
            entries = [e for e in self.entries if e.annotSet == aset]
            sents = doc._.annotSet[aset]
            instructions.append(self.to_instruction_per_set(entries, [s.text for s in sents]).strip())

        return """From the given text: 
{text}

There are quantities and associated descriptions found:

### {instruction}
""".format(text=self.text, instruction="\n\n### ".join(instructions))