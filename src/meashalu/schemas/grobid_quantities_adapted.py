# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan

from enum import Enum
from typing import List, Optional, Union, Annotated
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# measurement systems
class GrobidQuantitiesAnnotationSystemType(str, Enum):
    UNKNOWN = "unknown"
    SI_BASE = "SI base"
    SI_DERIVED = "SI derived"
    IMPERIAL = "imperial"
    US = "us"
    CGS = "centimetre–gram–second"
    MKS = "metre-kilogram-second"
    GAUSSIAN = "gaussian"  # We add as it seems that the CGS is not the proper term
    NON_SI = "non SI"


# measurement types
class GrobidQuantitiesAnnotationUnitType(str, Enum):
    UNKNOWN = "unknown"
    LENGTH = "length"
    TIME = "time"
    TEMPERATURE = "temperature"
    MASS = "mass"
    LUMINOUS_INTENSITY = "luminous intensity"
    AMOUNT_OF_SUBSTANCE = "amount of substance"
    ELECTRIC_CURRENT = "electric current"
    ANGLE = "angle"
    SOLID_ANGLE = "solid angle"
    FREQUENCY = "frequency"
    FORCE = "force"
    PRESSURE = "pressure"
    ENERGY = "energy"
    POWER = "power"
    ELECTRIC_CHARGE = "electric charge"
    VOLTAGE = "voltage"
    ELECTRIC_CAPACITANCE = "electric capacitance"
    ELECTRIC_RESISTANCE = "electric resistance"
    ELECTRIC_CONDUCTANCE = "electric conductance"
    ELECTRIC_FIELD = "electric field"
    MAGNETIC_FLUX = "magnetic flux"
    MAGNETIZATION = "magnetization"
    MASS_MAGNETIZATION = "mass magnetization"
    MAGNETIC_FLUX_DENSITY = "magnetic flux density"
    MAGNETIC_INDUCTION = "magnetic induction"
    MAGNETIC_FIELD_STRENGTH = "magnetic field strength"
    MAGNETIC_FIELD_RATIO = "magnetic field ratio"
    INDUCTANCE = "inductance"
    LUMINOUS_FLUX = "luminous flux"
    ILLUMINANCE = "illuminance"
    LUMINANCE = "luminance"
    RADIOACTIVITY = "radioactivity"
    ABSORBED_DOSE = "absorbed dose"
    EQUIVALENT_DOSE = "equivalent dose"
    ATTENUATION = "attenuation"
    TORQUE = "torque"
    DYNAMIC_VISCOSITY = "dynamic viscosity"
    KINEMATIC_VISCOSITY = "kinematic viscosity"
    ACOUSTIC_PRESSURE = "acoustic pressure"
    MASS_FLOW_RATE = "mass flow-rate"
    VOLUME_FLOW_RATE = "volume flow-rate"
    AIR_FLOW_RATE = "air flow-rate"
    SPECTRAL_RESPONSITIVY = "spectral responsivity"
    SPECTRAL_TRANSMITTANCE = "regular spectral transmittance"
    SPECTRAL_REFLECTANCE = "diffuse spectral reflectance"
    SPECTRAL_FLUX_DENSITY = "spectral flux density"
    REFLECTANCE = "reflectance"
    DETECTOR_PASSBAND = "detector passband"
    THERMAL_CONDUCTIVITY = "thermal conductivity"
    THERMAL_DIFFUSIVITY = "thermal diffusivity"
    HEAT_CAPACITY = "specific heat capacity"
    VOLUMETRIC_HEAT_CAPACITY = "volumetric heat capacity"
    EMISSION_RATE = "emission rate"
    CATALYTIC_ACTIVITY = "catalytic activity"
    RADIANCE = "radiance"
    IRRADIANCE = "irradiance"
    EMISSIVITY = "emissivity"
    HUMIDITY = "humidity"
    VOLUME = "volume"
    VELOCITY = "velocity"
    AREA = "area"
    CONCENTRATION = "concentration"
    DENSITY = "density"
    ACIDITY = "acidity"
    FRACTION = "fraction"
    VO2_MAX = "VO2 max"
    COUNT = "count"
    ACCELERATION = "acceleration"
    DEGREE = "angle"
    DIFFUSION_FLUX = "diffusion flux"
    MAGNETIC_MOMENT = "magnetic moment"
    ATOM_MASS_UNIT = "atom mass unit"
    PACE = "pace"
    MAXIMUM_ENERGY_PRODUCT = "maximum energy product"
    ENERGY_DENSITY = "energy density"
    ATOMIC_RATIO = "atomic ratio"
    WEIGHT_RATIO = "weight ratio"
    MASS_ACCUMULATION_RATE = "mass accumulation rate"
    SEDIMENTATION_RATE = "sedimentation rate"
    ROTATION = "rotation"


class GrobidQuantitiesAnnotationQuantityRawUnit(BaseModel):
    name: str
    type: Optional[GrobidQuantitiesAnnotationUnitType] = None
    system: Optional[GrobidQuantitiesAnnotationSystemType] = None


class GrobidQuantitiesAnnotationQuantityParsedValueStructureType(str, Enum):
    NUMBER = "NUMBER"
    ALPHABETIC = "ALPHABETIC"
    EXPONENT = "EXPONENT"
    TIME = "TIME"
    UNKNOWN = "UNKNOWN"


class GrobidQuantitiesAnnotationQuantityParsedValueStructure(BaseModel):
    type: GrobidQuantitiesAnnotationQuantityParsedValueStructureType
    formatted: Optional[str] = None

    @model_validator(mode='after')
    def check_formatted(self) -> 'GrobidQuantitiesAnnotationQuantityParsedValueStructure':
        if self.formatted is None and self.type != GrobidQuantitiesAnnotationUnitType.UNKNOWN:
            raise ValueError(
                "'formatted' field should not be None"
            )
        return self


class GrobidQuantitiesAnnotationQuantityParsedValue(BaseModel):
    numeric: float
    name: Optional[str] = None
    structure: Optional[GrobidQuantitiesAnnotationQuantityParsedValueStructure] = None
    parsed: Optional[str] = None


class GrobidQuantitiesAnnotationQuantityNormalizedUnit(BaseModel):
    name: str
    type: Optional[GrobidQuantitiesAnnotationUnitType] = None
    system: Optional[GrobidQuantitiesAnnotationSystemType] = None


class GrobidQuantitiesAnnotationQuantity(BaseModel):
    rawValue: str  # "two",
    parsedValue: GrobidQuantitiesAnnotationQuantityParsedValue
    rawUnit: Optional[GrobidQuantitiesAnnotationQuantityRawUnit] = None
    type: Optional[str] = None
    normalizedQuantity: Optional[float] = None
    normalizedUnit: Optional[GrobidQuantitiesAnnotationQuantityNormalizedUnit] = None


class GrobidQuantitiesAnnotationMeasurementType(str, Enum):
    """"""

    """
    (a) atomic, in case of a single measurement (e.g., 10 grams).
    # ATOMIC = "atomic"  # 
    """
    VALUE = "value"

    """
    (b) interval (from 3 to 5 km)
    # INTERVAL_MIN_MAX = "interval min max"
    # INTERVAL_BASE_RANGE = "interval base range"
    """
    INTERVAL = "interval"

    """
    (c) range (100 ± 4 mm) for continuous values
    """
    LIST = 'list'
    RANGE = "range"  #
    # DISCRETE_VALUES = "listc"  # (d) a list of discrete values.
    CONJUNCTION = "listc"
    DISJUNCTION = "listd"


class GrobidQuantitiesAnnotationMeasurementBoundingBoxes(BaseModel):
    p: int
    x: float
    y: float
    w: float
    h: float


class GrobidQuantitiesAnnotationMeasurementOffsets(BaseModel):
    start: int
    end: int


# class GrobidQuantitiesAnnotationMeasurementInterval(BaseModel):
#     type: Literal[GrobidQuantitiesAnnotationMeasurementType.INTERVAL]
#     quantityBase: Optional[GrobidQuantitiesAnnotationQuantity] = None
#     quantityRange: Optional[GrobidQuantitiesAnnotationQuantity] = None
#     quantityMost: Optional[GrobidQuantitiesAnnotationQuantity] = None
#     quantityLeast: Optional[GrobidQuantitiesAnnotationQuantity] = None
#     boundingBoxes: Optional[List[GrobidQuantitiesAnnotationMeasurementBoundingBoxes]] = None
#     measurementRaw: str
#     measurementOffsets: GrobidQuantitiesAnnotationMeasurementOffsets


# class GrobidQuantitiesAnnotationMeasurementValue(BaseModel):
#     type: Literal[GrobidQuantitiesAnnotationMeasurementType.VALUE]
#     quantity: GrobidQuantitiesAnnotationQuantity
#     boundingBoxes: Optional[List[GrobidQuantitiesAnnotationMeasurementBoundingBoxes]] = None
#     measurementRaw: str
#     measurementOffsets: GrobidQuantitiesAnnotationMeasurementOffsets

class GrobidQuantitiesAnnotationQualified(BaseModel):
    rawName:str
    normalizedName:str


class GrobidQuantitiesAnnotationMeasurementValue(BaseModel):
    type:Literal[GrobidQuantitiesAnnotationMeasurementType.VALUE]
    quantity: GrobidQuantitiesAnnotationQuantity
    quantified: Optional[GrobidQuantitiesAnnotationQualified] = None
    

class GrobidQuantitiesAnnotationMeasurementInterval(BaseModel):
    type:Literal[GrobidQuantitiesAnnotationMeasurementType.INTERVAL]
    quantityMost: GrobidQuantitiesAnnotationQuantity
    quantityLeast: GrobidQuantitiesAnnotationQuantity
    quantified: Optional[GrobidQuantitiesAnnotationQualified] = None

class GrobidQuantitiesAnnotationMeasurementList(BaseModel):
    type: Literal[GrobidQuantitiesAnnotationMeasurementType.LIST]
    quantities: Optional[List[GrobidQuantitiesAnnotationQuantity]] = None
    quantified: Optional[GrobidQuantitiesAnnotationQualified] = None



class GrobidQuantitiesAnnotationPages(BaseModel):
    page_height: float
    page_width: float


GrobidQuantitiesAnnotationMeasurement = Annotated[Union[
    GrobidQuantitiesAnnotationMeasurementValue,
    GrobidQuantitiesAnnotationMeasurementList,
    GrobidQuantitiesAnnotationMeasurementInterval], Field(discriminator='type')]


class GrobidQuantitiesAnnotationInstance(BaseModel):
    measurements: List[GrobidQuantitiesAnnotationMeasurement]
