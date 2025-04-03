# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Self, Optional

from pydantic import BaseModel
from quantulum.classes import Quantity, Unit


class QuantulumAnnotationUnitDimensionBaseType(str, Enum):
    KILOWATT = "kilowatt"
    MINUTE = "minute"
    TURN = "turn"
    FOOT = "foot"
    LITRE = "litre"
    VOLT = "volt"
    MEGABIT = "megabit"
    KILOGRAM = "kilogram"
    HECTOMETRE = "hectometre"
    POUND_MASS = "pound-mass"
    HOUR = "hour"
    CENTIMETRE = "centimetre"
    CANDELA = "candela"
    KILOMETRE = "kilometre"
    GRAM = "gram"
    KILOBIT = "kilobit"
    DECIMETRE = "decimetre"
    BIT = "bit"
    HORSEPOWER = "horsepower"
    SECOND = "second"
    INCH = "inch"
    GIGABIT = "gigabit"
    YARD = "yard"
    METRE = "metre"
    WATT = "watt"
    MILLIMETRE = "millimetre"
    AMPERE = "ampere"
    MILE = "mile"
    NEWTON = "newton"


class QuantulumAnnotationUnitDimensionType(BaseModel):
    base: QuantulumAnnotationUnitDimensionBaseType
    power: int


class QuantulumAnnotationEntityDimensionBaseType(str, Enum):
    SPEED = "speed"
    TIME = "time"
    LENGTH = "length"
    DIMENSIONLESS = "dimensionless"
    FORCE = "force"
    FREQUENCY = "frequency"
    MAGNETIC_FLUX = "magnetic flux"
    RADIATION_ABSORBED_DOSE = "radiation absorbed dose"
    AMOUNT_OF_SUBSTANCE = "amount of substance"
    DATA_STORAGE = "data storage"
    CHARGE = "charge"
    ENERGY = "energy"
    CURRENT = "current"
    POWER = "power"
    VOLUME = "volume"
    ANGULAR_SPEED = "angular speed"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    ELECTRICAL_RESISTANCE = "electrical resistance"
    TYPOGRAPHICAL_ELEMENT = "typographical element"
    LUMINOUS_INTENSITY = "luminous intensity"
    MASS = "mass"
    RELUCTANCE = "reluctance"
    ANGLE = "angle"
    ELECTRIC_POTENTIAL = "electric potential"
    AREA = "area"
    ACCELERATION = "acceleration"
    ELECTRICAL_RESISTIVITY = "electrical resistivity"


class QuantulumAnnotationEntityDimensionType(BaseModel):
    base: QuantulumAnnotationEntityDimensionBaseType
    power: int


@dataclass
class QuantulumAnnotationEntityTypeMixin:
    name_: str
    uri: str
    dimensions: List[QuantulumAnnotationEntityDimensionType] = field(default_factory=list)


class QuantulumAnnotationEntityType(QuantulumAnnotationEntityTypeMixin, Enum):
    DIMENSIONLESS = "dimensionless", "https://en.wikipedia.org/wiki/dimensionless_quantity", []
    LENGTH = "length", "https://en.wikipedia.org/wiki/length", []
    MASS = "mass", "https://en.wikipedia.org/wiki/mass", []
    CURRENCY = "currency", "https://en.wikipedia.org/wiki/currency", []
    TIME = "time", "https://en.wikipedia.org/wiki/time", []
    TEMPERATURE = "temperature", "https://en.wikipedia.org/wiki/temperature", []
    CHARGE = "charge", "https://en.wikipedia.org/wiki/charge_(physics)", []
    ANGLE = "angle", "https://en.wikipedia.org/wiki/angle", []
    DATA_STORAGE = "data storage", "https://en.wikipedia.org/wiki/computer_data_storage", []
    AMOUNT_OF_SUBSTANCE = "amount of substance", "https://en.wikipedia.org/wiki/amount_of_substance", []
    CATALYTIC_ACTIVITY = "catalytic activity", "https://en.wikipedia.org/wiki/catalysis", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AMOUNT_OF_SUBSTANCE,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME,
                                               power=-1), ]
    AREA = "area", "https://en.wikipedia.org/wiki/area", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=2), ]
    VOLUME = "volume", "https://en.wikipedia.org/wiki/volume", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=3), ]
    VOLUME_LUMBER = "volume (lumber)", "https://en.wikipedia.org/wiki/lumber", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=3), ]
    FORCE = "force", "https://en.wikipedia.org/wiki/force", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ACCELERATION, power=1), ]
    PRESSURE = "pressure", "https://en.wikipedia.org/wiki/pressure", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.FORCE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=-1), ]
    ENERGY = "energy", "https://en.wikipedia.org/wiki/energy", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.FORCE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=1), ]
    POWER = "power", "https://en.wikipedia.org/wiki/power_(physics)", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    SPEED = "speed", "https://en.wikipedia.org/wiki/speed", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    ACCELERATION = "acceleration", "https://en.wikipedia.org/wiki/acceleration", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.SPEED, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    FUEL_ECONOMY = "fuel economy", "https://en.wikipedia.org/wiki/fuel_efficiency", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=-1), ]
    FUEL_CONSUMPTION = "fuel consumption", "https://en.wikipedia.org/wiki/fuel_efficiency", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    ANGULAR_SPEED = "angular speed", "https://en.wikipedia.org/wiki/angular_velocity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ANGLE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    ANGULAR_ACCELERATION = "angular acceleration", "https://en.wikipedia.org/wiki/angular_acceleration", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ANGULAR_SPEED,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME,
                                               power=-1), ]
    DENSITY = "density", "https://en.wikipedia.org/wiki/density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=-1), ]
    SPECIFIC_VOLUME = "specific volume", "https://en.wikipedia.org/wiki/specific_volume", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=-1), ]
    MOMENT_OF_INERTIA = "moment of inertia", "https://en.wikipedia.org/wiki/moment_of_inertia", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=2), ]
    TORQUE = "torque", "https://en.wikipedia.org/wiki/torque", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.FORCE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=1), ]
    THERMAL_RESISTANCE = "thermal resistance", "https://en.wikipedia.org/wiki/thermal_resistance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TEMPERATURE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.POWER, power=-1), ]
    THERMAL_CONDUCTIVITY = "thermal conductivity", "https://en.wikipedia.org/wiki/thermal_conductivity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.POWER, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TEMPERATURE, power=-1), ]
    SPECIFIC_HEAT_CAPACITY = "specific heat capacity", "https://en.wikipedia.org/wiki/heat_capacity#specific_heat_capacity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=-1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TEMPERATURE, power=-1), ]
    VOLUMETRIC_FLOW = "volumetric flow", "https://en.wikipedia.org/wiki/volumetric_flow_rate", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    MASS_FLOW = "mass flow", "https://en.wikipedia.org/wiki/mass_flow_rate", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    CONCENTRATION = "concentration", "https://en.wikipedia.org/wiki/concentration", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=-1), ]
    DYNAMIC_VISCOSITY = "dynamic viscosity", "https://en.wikipedia.org/wiki/viscosity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.PRESSURE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=1), ]
    KINEMATIC_VISCOSITY = "kinematic viscosity", "https://en.wikipedia.org/wiki/viscosity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    FLUIDITY = "fluidity", "https://en.wikipedia.org/wiki/viscosity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=1), ]
    SURFACE_TENSION = "surface tension", "https://en.wikipedia.org/wiki/surface_tension", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.FORCE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    PERMEABILITY = "permeability", "https://en.wikipedia.org/wiki/permeation", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.PRESSURE, power=-1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=-1), ]
    SOUND_LEVEL = "sound level", "https://en.wikipedia.org/wiki/sound_level", []
    LUMINOUS_INTENSITY = "luminous intensity", "https://en.wikipedia.org/wiki/luminous_intensity", []
    LUMINOUS_FLUX = "luminous flux", "https://en.wikipedia.org/wiki/luminous_flux", []
    ILLUMINANCE = "illuminance", "https://en.wikipedia.org/wiki/illuminance", []
    LUMINANCE = "luminance", "https://en.wikipedia.org/wiki/luminance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LUMINOUS_INTENSITY,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA,
                                               power=-1), ]
    TYPOGRAPHICAL_ELEMENT = "typographical element", "https://en.wikipedia.org/wiki/typography", []
    IMAGE_RESOLUTION = "image resolution", "https://en.wikipedia.org/wiki/image_resolution", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TYPOGRAPHICAL_ELEMENT,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH,
                                               power=-1), ]
    FREQUENCY = "frequency", "https://en.wikipedia.org/wiki/frequency", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    INSTANCE_FREQUENCY = "instance frequency", "https://en.wikipedia.org/wiki/frequency", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.DIMENSIONLESS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    FLUX_DENSITY = "flux density", "https://en.wikipedia.org/wiki/flux", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.POWER, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-2),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.FREQUENCY, power=-1), ]
    LINEAR_MASS_DENSITY = "linear mass density", "https://en.wikipedia.org/wiki/linear_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    LINEAR_CHARGE_DENSITY = "linear charge density", "https://en.wikipedia.org/wiki/linear_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    SURFACE_CHARGE_DENSITY = "surface charge density", "https://en.wikipedia.org/wiki/area_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=-1), ]
    CHARGE_DENSITY = "charge density", "https://en.wikipedia.org/wiki/charge_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.VOLUME, power=-1), ]
    CURRENT = "current", "https://en.wikipedia.org/wiki/electric_current", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    LINEAR_CURRENT_DENSITY = "linear current density", "https://en.wikipedia.org/wiki/linear_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CURRENT, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    SURFACE_CURRENT_DENSITY = "surface current density", "https://en.wikipedia.org/wiki/area_density", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CURRENT, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.AREA, power=-1), ]
    ELECTRIC_POTENTIAL = "electric potential", "https://en.wikipedia.org/wiki/electric_potential", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=-1), ]
    ELECTRIC_FIELD = "electric field", "https://en.wikipedia.org/wiki/electric_field", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRIC_POTENTIAL,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH,
                                               power=-1), ]
    ELECTRICAL_RESISTANCE = "electrical resistance", "https://en.wikipedia.org/wiki/electrical_resistance_and_conductance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRIC_POTENTIAL,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CURRENT,
                                               power=-1), ]
    ELECTRICAL_RESISTIVITY = "electrical resistivity", "https://en.wikipedia.org/wiki/electrical_resistivity_and_conductivity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRICAL_RESISTANCE,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH,
                                               power=1), ]
    ELECTRICAL_CONDUCTANCE = "electrical conductance", "https://en.wikipedia.org/wiki/electrical_resistance_and_conductance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRICAL_RESISTANCE,
                                               power=-1), ]
    ELECTRICAL_CONDUCTIVITY = "electrical conductivity", "https://en.wikipedia.org/wiki/electrical_resistivity_and_conductivity", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRICAL_RESISTIVITY,
                                               power=-1), ]
    CAPACITANCE = "capacitance", "https://en.wikipedia.org/wiki/capacitance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRIC_POTENTIAL,
                                               power=-2), ]
    INDUCTANCE = "inductance", "https://en.wikipedia.org/wiki/inductance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CURRENT, power=-2), ]
    MAGNETIC_FLUX = "magnetic flux", "https://en.wikipedia.org/wiki/magnetic_flux", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ELECTRIC_POTENTIAL,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME,
                                               power=1), ]
    RELUCTANCE = "reluctance", "https://en.wikipedia.org/wiki/magnetic_reluctance", []
    MAGNETOMOTIVE_FORCE = "magnetomotive force", "https://en.wikipedia.org/wiki/magnetomotive_force", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.RELUCTANCE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MAGNETIC_FLUX,
                                               power=-2), ]
    MAGNETIC_FIELD = "magnetic field", "https://en.wikipedia.org/wiki/magnetic_field", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CURRENT, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-1), ]
    IRRADIANCE = "irradiance", "https://en.wikipedia.org/wiki/irradiance", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.POWER, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.LENGTH, power=-2), ]
    RADIATION_ABSORBED_DOSE = "radiation absorbed dose", "https://en.wikipedia.org/wiki/absorbed_dose", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.ENERGY, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=-1), ]
    RADIOACTIVITY = "radioactivity", "https://en.wikipedia.org/wiki/radioactive_decay", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME, power=-1), ]
    RADIATION_EXPOSURE = "radiation exposure", "https://en.wikipedia.org/wiki/exposure_(radiation)", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.CHARGE, power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.MASS, power=-1), ]
    RADIATION = "radiation", "https://en.wikipedia.org/wiki/radiation", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.RADIATION_ABSORBED_DOSE,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME,
                                               power=-1), ]
    DATA_TRANSFER_RATE = "data transfer rate", "https://en.wikipedia.org/wiki/data_transmission", [
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.DATA_STORAGE,
                                               power=1),
        QuantulumAnnotationEntityDimensionType(base=QuantulumAnnotationEntityDimensionBaseType.TIME,
                                               power=-1), ]
    UNKNOWN = "unknown", "https://en.wikipedia.org/wiki/unit_(measurement)", []


@dataclass
class QuantulumAnnotationUnitTypeMixin:
    name_: str
    surfaces: List[str]
    entity: QuantulumAnnotationEntityType
    uri: str
    symbols: str
    dimensions: List[QuantulumAnnotationEntityDimensionType]


class QuantulumAnnotationUnit(QuantulumAnnotationUnitTypeMixin, Enum):
    DIMENSIONLESS = "dimensionless", [
        "dimensionless"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Dimensionless_quantity", [], []
    PERCENTAGE = "percentage", ["percentage",
                                "percent"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Percentage", [], [
        "%", "pct", "pct."]
    PER_MILLE = "per mille", ["per mille", "permill", "permil", "permille", "per mil",
                              "per mill"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Per_mille", [], [
        "\u2030"]
    PARTS_PER_MILLION = "parts-per-million", ["parts-per-million",
                                              "parts per million"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Parts-per_notation", [], [
        "ppm"]
    PARTS_PER_BILLION = "parts-per-billion", ["parts-per-billion",
                                              "parts per billion"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Parts-per_notation", [], [
        "ppb"]
    PARTS_PER_TRILLION = "parts-per-trillion", ["parts-per-trillion",
                                                "parts per trillion"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Parts-per_notation", [], [
        "ppt"]
    BASIS_POINT = "basis point", ["basis point", "bip", "beep", "permyriad", "per myriad",
                                  "per ten thousand"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Basis_point", [], [
        "bp", "\u2031"]
    COUNT = "count", ["instance", "time",
                      "count"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Count_data", [], []
    TURN = "turn", ["turn", "revolution", "cycle",
                    "circle"], QuantulumAnnotationEntityType.DIMENSIONLESS, "https://en.wikipedia.org/wiki/Turn_(geometry)", [], []
    BARN = "barn", ["barn"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Barn_(unit)", [], [
        "b"]
    METRE = "metre", ["metre",
                      "meter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Metre", [], ["m"]
    EXAMETRE = "exametre", ["exametre",
                            "exameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/1_exametre", [], [
        "Em"]
    PETAMETRE = "petametre", ["petametre",
                              "petameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/1_petametre", [], [
        "Pm"]
    TERAMETRE = "terametre", ["terametre",
                              "terameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/1_terametre", [], [
        "Tm"]
    GIGAMETRE = "gigametre", ["gigametre",
                              "gigameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Gigametre", [], [
        "Gm"]
    MEGAMETRE = "megametre", ["megametre",
                              "megameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Megametre", [], [
        "Mm"]
    KILOMETRE = "kilometre", ["kilometre",
                              "kilometer"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Kilometre", [], [
        "km"]
    HECTOMETRE = "hectometre", ["hectometre",
                                "hectometer"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Hectometre", [], [
        "hm"]
    DECAMETRE = "decametre", ["decametre", "decameter", "dekametre",
                              "dekameter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Decametre", [], [
        "dam", "Dm", "dkm"]
    DECIMETRE = "decimetre", ["decimetre",
                              "decimeter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Decimetre", [], [
        "dm"]
    CENTIMETRE = "centimetre", ["centimetre",
                                "centimeter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Centimetre", [], [
        "cm"]
    MILLIMETRE = "millimetre", ["millimetre",
                                "millimeter"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Millimetre", [], [
        "mm"]
    MICROMETRE = "micrometre", ["micrometre", "micrometer",
                                "micron"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Micrometre", [], [
        "\u00b5m"]
    NANOMETRE = "nanometre", ["nanometre",
                              "nanometer"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Nanometre", [], [
        "nm"]
    PICOMETRE = "picometre", ["picometre",
                              "picometer"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Picometre", [], [
        "pm"]
    FEMTOMETRE = "femtometre", ["femtometre",
                                "femtometer"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Femtometre", [], [
        "fm"]
    PARSEC = "parsec", ["parsec"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Parsec", [], [
        "pc"]
    LIGHT_YEAR = "light-year", ["light-year",
                                "light year"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Light-year", [], [
        "ly"]
    ASTRONOMICAL_UNIT = "astronomical unit", [
        "astronomical unit"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Astronomical_unit", [], [
        "au", "AU", "ua", "UA"]
    LEAGUE = "league", ["league",
                        "nautical league"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/League_(unit)", [], [
        "lea", "st lea", "n lea", "n league", "st league"]
    MILE = "mile", ["mile",
                    "statute mile"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Mile", [], [
        "mi"]
    NAUTICAL_MILE = "nautical mile", [
        "nautical mile"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Nautical_mile", [], ["M",
                                                                                                                    "NM",
                                                                                                                    "nmi"]
    ELL = "ell", ["ell"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Ell", [], []
    FURLONG = "furlong", [
        "furlong"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Furlong", [], ["fur"]
    FATHOM = "fathom", ["fathom"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Fathom", [], [
        "fath"]
    YARD = "yard", ["yard"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Yard", [], ["yd"]
    FOOT = "foot", ["foot"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Foot_(unit)", [], [
        "ft", "'", "\u2032"]
    CUBIT = "cubit", ["cubit"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Cubit", [], []
    SPAN = "span", ["span"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Span_(unit)", [], []
    INCH = "inch", ["inch"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Inch", [], ["in",
                                                                                                              "\"",
                                                                                                              "\u2033"]
    ÅNGSTRÖM = "ångström", ["\u00e5ngstr\u00f6m", "\u00e5ngstrom", "angstr\u00f6m",
                            "angstrom"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Ångström", [], [
        "\u00c5"]
    TWIP = "twip", ["twip"], QuantulumAnnotationEntityType.LENGTH, "https://en.wikipedia.org/wiki/Twip", [], []
    SOLAR_MASS = "solar mass", [
        "solar mass"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Solar_mass", [], ["M\u2609"]
    EARTH_MASS = "earth mass", [
        "earth mass"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Earth_mass", [], ["M\u2295"]
    SHORT_TON = "short ton", ["short ton",
                              "ton"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Short_ton", [], []
    LONG_TON = "long ton", ["long ton", "imperial ton",
                            "weight ton"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Long_ton", [], []
    KILOGRAM = "kilogram", ["kilogram", "kilogramme",
                            "kilo"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Kilogram", [], [
        "kg"]
    GRAM = "gram", ["gram", "gramme"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Gram", [], [
        "g", "gm"]
    MILLIGRAM = "milligram", ["milligram",
                              "milligramme"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Kilogram#SI_multiples", [], [
        "mg"]
    MICROGRAM = "microgram", ["microgram",
                              "microgramme"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Microgram", [], [
        "\u00b5g", "mcg"]
    ATOMIC_MASS_UNIT = "atomic mass unit", ["atomic mass unit", "unified atomic mass unit",
                                            "dalton"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Atomic_mass_unit", [], [
        "u", "Da", "amu"]
    POUND_MASS = "pound-mass", ["pound",
                                "pound-mass"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Pound_(mass)", [], [
        "lb", "lbm"]
    OUNCE = "ounce", ["ounce"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Ounce", [], ["oz",
                                                                                                                "\u2125"]
    TON = "ton", ["ton"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Ton", [], []
    TONNE = "tonne", ["tonne",
                      "metric ton"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Tonne", [], [
        "t"]
    QUINTAL = "quintal", ["quintal"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Quintal", [], [
        "q"]
    QUARTER = "quarter", [
        "quarter"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Quarter_(unit)", [], ["qr"]
    CARAT = "carat", ["carat"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Carat_(mass)", [], [
        "ct"]
    BUSHEL = "bushel", ["bushel"], QuantulumAnnotationEntityType.MASS, "https://en.wikipedia.org/wiki/Bushel", [], [
        "bsh", "bu"]
    DOLLAR = "dollar", ["dollar"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Dollar", [], [
        "$"]
    UNITED_STATES_DOLLAR = "united states dollar", ["united states dollar", "us dollar",
                                                    "american dollar"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/United_States_dollar", [], [
        "USD", "US$"]
    EURO = "euro", ["euro"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Euro", [], [
        "\u20ac", "EUR"]
    POUND_STERLING = "pound sterling", ["pound sterling",
                                        "pound"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Pound_sterling", [], [
        "\u00a3", "GBP"]
    CANADIAN_DOLLAR = "canadian dollar", [
        "canadian dollar"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Pound_sterling", [], [
        "CAD", "C$"]
    AUSTRALIAN_DOLLAR = "australian dollar", [
        "australian dollar"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Australian_dollar", [], [
        "AUD", "A$"]
    NEW_ZEALAND_DOLLAR = "new zealand dollar", [
        "new zealand dollar"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/New_Zealand_dollar", [], [
        "NZD", "NZ$"]
    JAPANESE_YEN = "japanese yen", ["japanese yen",
                                    "yen"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Japanese_yen", [], [
        "\u5186", "\u5713", "\u00a5", "JPY"]
    SWISS_FRANC = "swiss franc", ["swiss franc",
                                  "franc"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Swiss_franc", [], [
        "Fr", "SFr", "FS", "CHF"]
    SOUTH_AFRICAN_RAND = "south african rand", ["south african rand",
                                                "rand"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/South_African_rand", [], [
        "R", "ZAR"]
    BRAZILIAN_REAL = "brazilian real", ["brazilian real", "real",
                                        "reais"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/South_African_rand", [], [
        "R$", "BRL"]
    INDIAN_RUPEE = "indian rupee", ["indian rupee",
                                    "rupee"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Indian_rupee", [], [
        "\u20b9", "INR"]
    MEXICAN_PESO = "mexican peso", ["mexican peso",
                                    "peso"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Mexican_peso", [], [
        "MXN"]
    RUSSIAN_RUBLE = "russian ruble", ["russian ruble", "russian rouble", "ruble",
                                      "rouble"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Russian_ruble", [], [
        "\u20bd", "RUB"]
    CHINESE_YUAN = "chinese yuan", ["chinese yuan",
                                    "yuan"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/Chinese_yuan", [], [
        "\u00a5", "\u5143", "CNY"]
    SOUTH_KOREAN_WON = "south korean won", ["south korean won", "won",
                                            "korean republic won"], QuantulumAnnotationEntityType.CURRENCY, "https://en.wikipedia.org/wiki/South_Korean_won", [], [
        "\uc6d0", "\u20a9", "KRW"]
    CUBIC_METRE = "cubic metre", ["cubic metre", "cubic meter", "kiloliter",
                                  "kilolitre"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=3), ], ["cu m",
                                                                                                                "kL"]
    CUBIC_KILOMETRE = "cubic kilometre", ["cubic kilometre",
                                          "cubic kilometer"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOMETRE, power=3), ], []
    CUBIC_CENTIMETRE = "cubic centimetre", ["cubic centimetre", "cubic centimeter", "millilitre",
                                            "milliliter"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_centimetre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.CENTIMETRE, power=3), ], [
        "cc", "ccm", "mL", "ml"]
    CUBIC_MILLIMETRE = "cubic millimetre", ["cubic millimetre", "cubic millimeter", "microliter",
                                            "microlitre"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MILLIMETRE, power=3), ], [
        "\u00b5l", "\u00b5L"]
    LITRE = "litre", ["cubic decimetre", "cubic decimeter", "litre",
                      "liter"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Litre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.DECIMETRE, power=3), ], ["l",
                                                                                                                    "L",
                                                                                                                    "ltr"]
    DROP = "drop", ["drop"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Drop_(unit)", [], []
    BARREL = "barrel", ["barrel", "barrel dry",
                        "dry barrel"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Barrel_(unit)", [], [
        "bbl", "bbl dry"]
    GALLON = "gallon", ["gallon"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Gallon", [], [
        "gal"]
    QUART = "quart", ["quart", "dry quart", "liquid quart", "quart dry",
                      "quart liquid"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Quart", [], [
        "qt", "qt liq", "qt dry"]
    PINT = "pint", ["pint", "dry pint", "liquid pint", "pint dry",
                    "pint liquid"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Pint", [], [
        "pt", "pt liq", "p", "pt dry"]
    CUP = "cup", ["cup"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cup_(unit)", [], []
    FLUID_OUNCE = "fluid ounce", [
        "fluid ounce"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Fluid_ounce", [], ["fl oz",
                                                                                                                "oz fl",
                                                                                                                "floz",
                                                                                                                "ozfl"]
    TABLESPOON = "tablespoon", ["tablespoon",
                                "table spoon"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Tablespoon", [], [
        "tbsp"]
    DESSERTSPOON = "dessertspoon", ["dessertspoon",
                                    "dessert spoon"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Dessert_spoon", [], [
        "dstspn"]
    TEASPOON = "teaspoon", ["teaspoon",
                            "tea spoon"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Teaspoon", [], [
        "tsp"]
    CUBIC_MILE = "cubic mile", ["cubic mile",
                                "cu mile"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_mile", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MILE, power=3), ], ["cu mi"]
    CUBIC_YARD = "cubic yard", ["cubic yard",
                                "cu yard"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_yard", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.YARD, power=3), ], ["cu yd"]
    CUBIC_FOOT = "cubic foot", ["cubic foot",
                                "cu foot"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_foot", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=3), ], ["cu ft"]
    CUBIC_INCH = "cubic inch", ["cubic inch",
                                "cu inch"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Cubic_inch", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.INCH, power=3), ], ["cu in"]
    ACRE_FOOT = "acre foot", ["acre foot",
                              "acre-foot"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Acre-foot", [], [
        "ac*ft"]
    STERE = "stere", ["stere"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Stere", [], ["st"]
    PECK = "peck", ["peck"], QuantulumAnnotationEntityType.VOLUME, "https://en.wikipedia.org/wiki/Peck", [], ["pk"]
    KELVIN = "kelvin", [
        "kelvin"], QuantulumAnnotationEntityType.TEMPERATURE, "https://en.wikipedia.org/wiki/Kelvin", [], ["K",
                                                                                                           "\u00b0K"]
    DEGREE_CELSIUS = "degree celsius", ["degree celsius", "Celsius", "centigrade",
                                        "degree centigrade"], QuantulumAnnotationEntityType.TEMPERATURE, "https://en.wikipedia.org/wiki/Celsius", [], [
        "C", "\u00b0C"]
    DEGREE_FAHRENHEIT = "degree fahrenheit", ["degree fahrenheit",
                                              "Fahrenheit"], QuantulumAnnotationEntityType.TEMPERATURE, "https://en.wikipedia.org/wiki/Fahrenheit", [], [
        "F", "\u00b0F"]
    DEGREE_RANKINE = "degree rankine", ["degree rankine",
                                        "Rankine"], QuantulumAnnotationEntityType.TEMPERATURE, "https://en.wikipedia.org/wiki/Rankine_scale", [], [
        "\u00b0R", "\u00b0Ra"]
    CIRCULAR_MIL = "circular mil", [
        "circular mil"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Circular_mil", [], ["cmil"]
    SQUARE_METRE = "square metre", ["square metre",
                                    "square meter"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=2), ], ["sq m"]
    SQUARE_KILOMETRE = "square kilometre", ["square kilometre",
                                            "square kilometer"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_kilometre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOMETRE, power=2), ], [
        "sq km"]
    HECTARE = "hectare", ["square hectometre",
                          "square hectometer"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Hectare", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HECTOMETRE, power=2), ], [
        "sq hm", "ha"]
    SQUARE_MILE = "square mile", [
        "square mile"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_mile", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MILE, power=2), ], ["sq mi"]
    SQUARE_YARD = "square yard", ["square yard",
                                  "gaj"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_yard", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.YARD, power=2), ], ["sq yd"]
    SQUARE_FOOT = "square foot", [
        "square foot"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_foot", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=2), ], ["sq ft"]
    SQUARE_INCH = "square inch", [
        "square inch"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Square_inch", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.INCH, power=2), ], ["sq in"]
    ACRE = "acre", ["acre"], QuantulumAnnotationEntityType.AREA, "https://en.wikipedia.org/wiki/Acre", [], ["ac"]
    PASCAL = "pascal", ["pascal"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pascal", [], [
        "Pa"]
    HECTOPASCAL = "hectopascal", [
        "hectopascal"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pascal", [], ["hPa"]
    KILOPASCAL = "kilopascal", [
        "kilopascal"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pascal", [], ["kPa"]
    MEGAPASCAL = "megapascal", [
        "megapascal"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pascal", [], ["MPa"]
    GIGAPASCAL = "gigapascal", [
        "gigapascal"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pascal", [], ["GPa"]
    BAR = "bar", ["bar"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Bar_(unit)", [], []
    MILLIBAR = "millibar", [
        "millibar"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Bar_(unit)", [], ["mbar"]
    MICROBAR = "microbar", [
        "microbar"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Bar_(unit)", [], [
        "\u00b5bar"]
    POUND_PER_SQUARE_INCH = "pound per square inch", ["pound per square inch",
                                                      "pound-force per square inch"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Pounds_per_square_inch", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.POUND_MASS, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.INCH, power=-2), ], ["psi"]
    TORR = "torr", ["torr"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Torr", [], ["Torr"]
    MILLIMETER_OF_MERCURY = "millimeter of mercury", ["millimetre of mercury", "millimetre mercury",
                                                      "millimeter of mercury",
                                                      "millimeter mercury"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Millimeter_of_mercury", [], [
        "mmHg"]
    CENTIMETER_OF_WATER = "centimeter of water", ["centimeter of water",
                                                  "centimetre of water"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Centimetre_of_water", [], [
        "cmH2O", "cm H2O"]
    INCH_OF_WATER = "inch of water", ["inch of water",
                                      "inch water column"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Inch_of_water", [], [
        "inH2O", "inAq"]
    INCH_OF_MERCURY = "inch of mercury", ["inch of mercury",
                                          "inch mercury"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Inch_of_mercury", [], [
        "inHg", "\"Hg"]
    STANDARD_ATMOSPHERE = "standard atmosphere", ["standard atmosphere",
                                                  "atmosphere"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Atmosphere_(unit)", [], [
        "atm"]
    TECHNICAL_ATMOSPHERE = "technical atmosphere", [
        "technical atmosphere"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Technical_atmosphere", [], [
        "at"]
    BARYE = "barye", ["barye", "barad", "barrie", "bary", "baryd", "baryed",
                      "barie"], QuantulumAnnotationEntityType.PRESSURE, "https://en.wikipedia.org/wiki/Barye", [], [
        "Ba"]
    JOULE = "joule", ["joule"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Joule", [], ["J"]
    MILLIJOULE = "millijoule", [
        "millijoule"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Joule", [], ["mJ"]
    KILOJOULE = "kilojoule", [
        "kilojoule"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Joule", [], ["kJ"]
    ELECTRONVOLT = "electronvolt", ["electron volt", "electronvolt",
                                    "electron-volt"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Electronvolt", [], [
        "eV"]
    KILOELECTRONVOLT = "kiloelectronvolt", ["kiloelectron volt", "kiloelectronvolt",
                                            "kiloelectron-volt"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Electronvolt", [], [
        "keV"]
    MEGAELECTRONVOLT = "megaelectronvolt", ["megaelectron volt", "megaelectronvolt",
                                            "megaelectron-volt"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Electronvolt", [], [
        "MeV"]
    GIGAELECTRONVOLT = "gigaelectronvolt", ["gigaelectron volt", "gigaelectronvolt", "gigaelectron-volt",
                                            "bevatron"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Electronvolt", [], [
        "GeV", "BeV"]
    TERAELECTRONVOLT = "teraelectronvolt", ["teraelectron volt", "teraelectronvolt",
                                            "teraelectron-volt"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Electronvolt", [], [
        "TeV"]
    HARTREE = "hartree", ["hartree",
                          "hartree energy"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Hartree", [], [
        "Eh", "Ha"]
    ERG = "erg", ["erg"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Erg", [], []
    KILOWATT_HOUR = "kilowatt hour", ["kilowatt hour", "kilowatthour",
                                      "kilowatt-hour"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Kilowatt_hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOWATT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=1), ], ["kWh"]
    WATT_SECOND = "watt second", ["watt second", "watt-second",
                                  "wattsecond"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Watt_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.WATT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=1), ], ["W s",
                                                                                                                 "W*s",
                                                                                                                 "W\u00b7s"]
    HORSEPOWER_HOUR = "horsepower-hour", ["horsepower hour", "horsepowerhour",
                                          "horsepower-hour"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Horsepower-hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HORSEPOWER, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=1), ], ["hph"]
    CALORIE = "calorie", ["calorie", "small calorie",
                          "gram calorie"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Calorie", [], [
        "cal"]
    KILOCALORIE = "kilocalorie", ["kilocalorie", "large calorie",
                                  "kilogram calorie"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Calorie", [], [
        "kcal", "Cal"]
    BRITISH_THERMAL_UNIT = "british thermal unit", [
        "british thermal unit"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/British_thermal_unit", [], [
        "btu", "BTU", "Btu"]
    MEGA_BRITISH_THERMAL_UNIT = "mega british thermal unit", [
        "mega british thermal unit"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/British_thermal_unit", [], [
        "MBTU", "MMBtu", "mmBtu"]
    QUAD = "quad", ["quad",
                    "quadrillion british thermal unit"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Quad_(unit)", [], []
    GIGATON = "gigaton", ["gigaton",
                          "gigatonne"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/TNT_equivalent", [], [
        "Gt", "Gton"]
    MEGATON = "megaton", ["megaton",
                          "megatonne"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/TNT_equivalent", [], [
        "Mt", "Mton"]
    KILOTON = "kiloton", ["kiloton",
                          "kilotonne"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/TNT_equivalent", [], [
        "kt", "kton"]
    THERM = "therm", ["therm",
                      "thermie"], QuantulumAnnotationEntityType.ENERGY, "https://en.wikipedia.org/wiki/Therm", [], [
        "thm"]
    TON_OF_REFRIGERATION = "ton of refrigeration", ["ton of refrigeration",
                                                    "refrigeration ton"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Ton_of_refrigeration", [], [
        "TR"]
    WATT = "watt", ["watt"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Watt", [], ["W"]
    KILOWATT = "kilowatt", [
        "kilowatt"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Watt", [], ["kW"]
    MEGAWATT = "megawatt", [
        "megawatt"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Watt", [], ["MW"]
    GIGAWATT = "gigawatt", [
        "gigawatt"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Watt", [], ["GW"]
    HORSEPOWER = "horsepower", ["horsepower", "pferdestarke", "uk horsepower", "british horsepower",
                                "boiler horsepower", "metric horsepower",
                                "hydraulic horsepower"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Horsepower", [], [
        "hp"]
    VOLT_AMPERE = "volt-ampere", ["volt-ampere", "volt ampere",
                                  "voltampere"], QuantulumAnnotationEntityType.POWER, "https://en.wikipedia.org/wiki/Volt-ampere", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.VOLT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.AMPERE, power=1), ], ["VA"]
    NEWTON = "newton", [
        "newton"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Newton_(unit)", [], ["N"]
    KILONEWTON = "kilonewton", [
        "kilonewton"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Newton_(unit)", [], ["kN"]
    DYNE = "dyne", ["dyne"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Dyne", [], ["dyn"]
    KILOGRAM_FORCE = "kilogram-force", ["kilogram-force", "kilogram force", "kilogramforce", "kilopond",
                                        "force kilogram"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Kilogram-force", [], [
        "kgf", "kp"]
    GRAM_FORCE = "gram-force", ["gram-force", "gram force", "gramforce", "pond",
                                "force gram"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Kilogram-force", [], [
        "gf"]
    TON_FORCE = "ton-force", ["ton-force", "ton force", "tonforce", "force ton", "force tonne", "tonne-force",
                              "tonne force",
                              "tonneforce"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Ton-force", [], [
        "tf", "tonf"]
    POUND_FORCE = "pound-force", ["pound-force", "pound force", "poundforce",
                                  "force pound"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Pound_(force)", [], [
        "lbf"]
    OUNCE_FORCE = "ounce-force", ["ounce-force", "ounce force", "ounceforce",
                                  "force ounce"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Pound_(force)", [], [
        "ozf"]
    POUNDAL = "poundal", [
        "poundal"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Poundal", [], ["pdl"]
    KIP = "kip", ["kip", "kip-force", "kip force",
                  "kipforce"], QuantulumAnnotationEntityType.FORCE, "https://en.wikipedia.org/wiki/Kip_(unit)", [], [
        "klb", "kipf", "klbf"]
    SHAKE = "shake", ["shake"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Shake_(unit)", [], []
    SECOND = "second", ["second"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Second", [], ["s",
                                                                                                                    "sec",
                                                                                                                    "\"",
                                                                                                                    "\u2033"]
    MILLISECOND = "millisecond", [
        "millisecond"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Millisecond", [], ["ms",
                                                                                                              "msec"]
    MICROSECOND = "microsecond", [
        "microsecond"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Microsecond", [], ["\u03bcs",
                                                                                                              "\u03bcsec"]
    NANOSECOND = "nanosecond", [
        "nanosecond"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Nanosecond", [], ["ns",
                                                                                                            "nsec"]
    MINUTE = "minute", ["minute"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Minute", [], [
        "min", "'", "\u2032"]
    HOUR = "hour", ["hour"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Hour", [], ["h", "hr"]
    DAY = "day", ["day"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Day", [], ["d"]
    WEEK = "week", ["week"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Week", [], []
    MONTH = "month", ["month"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Month", [], []
    YEAR = "year", ["year"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Year", [], ["y"]
    FORTNIGHT = "fortnight", [
        "fortnight"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Fortnight", [], []
    LUSTRUM = "lustrum", [
        "lustrum"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Lustrum", [], []
    DECADE = "decade", ["decade"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Decade", [], []
    CENTURY = "century", [
        "century"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Century", [], []
    MILLENNIUM = "millennium", [
        "millennium"], QuantulumAnnotationEntityType.TIME, "https://en.wikipedia.org/wiki/Millennium", [], []
    SPEED_OF_LIGHT = "speed of light", ["speed of light",
                                        "lightspeed"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Speed_of_light", [], [
        "c"]
    KNOT = "knot", ["knot"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Knot_(unit)", [], [
        "kn", "kt"]
    METRE_PER_SECOND = "metre per second", ["metre per second",
                                            "meter per second"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Metre_per_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], ["mps"]
    METRE_PER_HOUR = "metre per hour", ["metre per hour",
                                        "meter per hour"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Metre_per_hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=-1), ], []
    FOOT_PER_SECOND = "foot per second", [
        "foot per second"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Foot_per_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], ["fps"]
    INCH_PER_SECOND = "inch per second", [
        "inch per second"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Inch_per_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.INCH, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], ["ips"]
    KILOMETRE_PER_HOUR = "kilometre per hour", ["kilometre per hour",
                                                "kilometer per hour"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Kilometres_per_hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOMETRE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=-1), ], ["kph"]
    MILE_PER_HOUR = "mile per hour", [
        "mile per hour"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Miles_per_hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MILE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=-1), ], ["MPH",
                                                                                                                "mph"]
    MACH_NUMBER = "mach number", ["mach",
                                  "mach number"], QuantulumAnnotationEntityType.SPEED, "https://en.wikipedia.org/wiki/Mach_number", [], [
        "M", "Ma"]
    DEGREE_ANGLE = "degree angle", ["degree", "degree of arc", "arc degree", "arcdegree",
                                    "angular degree"], QuantulumAnnotationEntityType.ANGLE, "https://en.wikipedia.org/wiki/Degree_(angle)", [], [
        "\u00b0", "deg", "arcdeg"]
    RADIAN = "radian", ["radian"], QuantulumAnnotationEntityType.ANGLE, "https://en.wikipedia.org/wiki/Radian", [], [
        "rad", "\u33ad"]
    STERADIAN = "steradian", ["steradian",
                              "square radian"], QuantulumAnnotationEntityType.ANGLE, "https://en.wikipedia.org/wiki/Steradian", [], [
        "sr"]
    MINUTE_OF_ARC = "minute of arc", ["minute", "minute of arc", "arcminute", "minute arc", "angular minute",
                                      "arc minute"], QuantulumAnnotationEntityType.ANGLE, "https://en.wikipedia.org/wiki/Minute_and_second_of_arc", [], [
        "'", "\u2032", "MOA", "arcmin", "amin"]
    SECOND_OF_ARC = "second of arc", ["second", "second of arc", "arcsecond", "second arc", "angular second",
                                      "arc second"], QuantulumAnnotationEntityType.ANGLE, "https://en.wikipedia.org/wiki/Minute_and_second_of_arc", [], [
        "\"", "\u2033", "SOA", "arcsec", "asec"]
    BIT = "bit", ["bit"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Bit", [], ["b"]
    KILOBIT = "kilobit", [
        "kilobit"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Kilobit", [], ["kb",
                                                                                                              "kbit"]
    MEGABIT = "megabit", [
        "megabit"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Megabit", [], ["Mb",
                                                                                                              "Mbit"]
    GIGABIT = "gigabit", [
        "gigabit"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Gigabit", [], ["Gb",
                                                                                                              "Gbit"]
    TERABIT = "terabit", [
        "terabit"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Terabit", [], ["Tb",
                                                                                                              "Tbit"]
    BYTE = "byte", ["byte"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Byte", [], ["B"]
    KILOBYTE = "kilobyte", [
        "kilobyte"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Kilobyte", [], ["kB",
                                                                                                                "K",
                                                                                                                "KB"]
    MEGABYTE = "megabyte", [
        "megabyte"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Megabyte", [], ["MB",
                                                                                                                "MByte"]
    GIGABYTE = "gigabyte", [
        "gigabyte"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Gigabyte", [], ["GB"]
    TERABYTE = "terabyte", [
        "terabyte"], QuantulumAnnotationEntityType.DATA_STORAGE, "https://en.wikipedia.org/wiki/Terabyte", [], ["TB"]
    GAL = "gal", ["gal",
                  "galileo"], QuantulumAnnotationEntityType.ACCELERATION, "https://en.wikipedia.org/wiki/Gal_(unit)", [], [
        "Gal"]
    FOOT_PER_SQUARE_SECOND = "foot per square second", ["foot per second squared",
                                                        "foot per square second"], QuantulumAnnotationEntityType.ACCELERATION, "https://en.wikipedia.org/wiki/Foot_per_second_squared", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-2), ], []
    METRE_PER_SQUARE_SECOND = "metre per square second", ["metre per second squared", "meter per second squared",
                                                          "metre per square second",
                                                          "meter per square second"], QuantulumAnnotationEntityType.ACCELERATION, "https://en.wikipedia.org/wiki/Metre_per_second_squared", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-2), ], []
    NEWTON_METRE = "newton metre", ["newton metre", "newton meter", "newton-meter",
                                    "newton-metre"], QuantulumAnnotationEntityType.TORQUE, "https://en.wikipedia.org/wiki/Newton_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.NEWTON, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=1), ], ["Nm"]
    POISE = "poise", [
        "poise"], QuantulumAnnotationEntityType.DYNAMIC_VISCOSITY, "https://en.wikipedia.org/wiki/Poise", [], ["P"]
    CENTIPOISE = "centipoise", [
        "centipoise"], QuantulumAnnotationEntityType.DYNAMIC_VISCOSITY, "https://en.wikipedia.org/wiki/Poise", [], [
        "cP"]
    STOKES = "stokes", [
        "stokes"], QuantulumAnnotationEntityType.KINEMATIC_VISCOSITY, "https://en.wikipedia.org/wiki/Viscosity#Stokes_.28unit.29", [], [
        "St"]
    CENTISTOKES = "centistokes", [
        "centistokes"], QuantulumAnnotationEntityType.KINEMATIC_VISCOSITY, "https://en.wikipedia.org/wiki/Viscosity#Stokes_.28unit.29", [], [
        "cSt"]
    RHE = "rhe", ["rhe",
                  "reciprocal poise"], QuantulumAnnotationEntityType.FLUIDITY, "https://en.wikipedia.org/wiki/Viscosity#Fluidity", [], []
    DECIBEL = "decibel", [
        "decibel"], QuantulumAnnotationEntityType.SOUND_LEVEL, "https://en.wikipedia.org/wiki/Decibel", [], ["dB"]
    STILB = "stilb", [
        "stilb"], QuantulumAnnotationEntityType.LUMINANCE, "https://en.wikipedia.org/wiki/Stilb_(unit)", [], ["sb"]
    CANDELA_PER_SQUARE_METRE = "candela per square metre", ["candela per square metre", "candela per square meter",
                                                            "nit"], QuantulumAnnotationEntityType.LUMINANCE, "https://en.wikipedia.org/wiki/Candela_per_square_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.CANDELA, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=-2), ], ["nt"]
    CANDELA = "candela", ["candela",
                          "candle"], QuantulumAnnotationEntityType.LUMINOUS_INTENSITY, "https://en.wikipedia.org/wiki/Candela", [], [
        "cd"]
    LUMEN = "lumen", [
        "lumen"], QuantulumAnnotationEntityType.LUMINOUS_FLUX, "https://en.wikipedia.org/wiki/Lumen_(unit)", [], ["lm"]
    LUX = "lux", ["lux"], QuantulumAnnotationEntityType.ILLUMINANCE, "https://en.wikipedia.org/wiki/Lux", [], ["lx"]
    CYCLE_PER_SECOND = "cycle per second", [
        "cycle per second"], QuantulumAnnotationEntityType.INSTANCE_FREQUENCY, "https://en.wikipedia.org/wiki/Cycle_per_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.TURN, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], ["cps"]
    REVOLUTIONS_PER_MINUTE = "revolutions per minute", [
        "revolutions per minute"], QuantulumAnnotationEntityType.INSTANCE_FREQUENCY, "https://en.wikipedia.org/wiki/Revolutions_per_minute", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.TURN, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MINUTE, power=-1), ], ["rpm",
                                                                                                                  "RPM"]
    HERTZ = "hertz", ["hertz",
                      "revolutions per second"], QuantulumAnnotationEntityType.FREQUENCY, "https://en.wikipedia.org/wiki/Hertz", [], [
        "Hz", "\u3390", "rps"]
    INVERSE_SECOND = "inverse second", ["inverse second", "reciprocal second",
                                        "per second"], QuantulumAnnotationEntityType.FREQUENCY, "https://en.wikipedia.org/wiki/Inverse_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], []
    MEGAHERTZ = "megahertz", [
        "megahertz"], QuantulumAnnotationEntityType.FREQUENCY, "https://en.wikipedia.org/wiki/Hertz", [], ["MHz",
                                                                                                           "M\u3390"]
    MOLE = "mole", [
        "mole"], QuantulumAnnotationEntityType.AMOUNT_OF_SUBSTANCE, "https://en.wikipedia.org/wiki/Mole_(unit)", [], [
        "mol"]
    STATCOULOMB = "statcoulomb", ["statcoulomb", "franklin",
                                  "electrostatic unit of charge"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Statcoulomb", [], [
        "statC", "Fr", "esu"]
    COULOMB = "coulomb", [
        "coulomb"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Coulomb", [], ["C"]
    MILLICOULOMB = "millicoulomb", [
        "millicoulomb"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Coulomb", [], ["mC"]
    MICROCOULOMB = "microcoulomb", [
        "microcoulomb"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Coulomb", [], ["\u00b5C"]
    AMPERE_HOUR = "ampere-hour", ["ampere-hour", "ampere hour",
                                  "amp-hour"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Coulomb", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.AMPERE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=1), ], ["Ah"]
    AMPERE = "ampere", ["ampere"], QuantulumAnnotationEntityType.CURRENT, "https://en.wikipedia.org/wiki/Ampere", [], [
        "A", "amp"]
    STATVOLT = "statvolt", [
        "statvolt"], QuantulumAnnotationEntityType.ELECTRIC_POTENTIAL, "https://en.wikipedia.org/wiki/Statvolt", [], []
    VOLT = "volt", [
        "volt"], QuantulumAnnotationEntityType.ELECTRIC_POTENTIAL, "https://en.wikipedia.org/wiki/Volt", [], ["V"]
    OHM = "ohm", [
        "ohm"], QuantulumAnnotationEntityType.ELECTRICAL_RESISTANCE, "https://en.wikipedia.org/wiki/Ohm", [], ["\u03a9"]
    STATMHO = "statmho", [
        "statmho"], QuantulumAnnotationEntityType.ELECTRICAL_CONDUCTANCE, "https://en.wikipedia.org/wiki/Statmho", [], []
    STATOHM = "statohm", [
        "statohm"], QuantulumAnnotationEntityType.ELECTRICAL_RESISTANCE, "https://en.wikipedia.org/wiki/Statmho", [], []
    SIEMENS = "siemens", ["siemens",
                          "mho"], QuantulumAnnotationEntityType.ELECTRICAL_CONDUCTANCE, "https://en.wikipedia.org/wiki/Siemens_(unit)", [], [
        "S"]
    FARADAY = "faraday", [
        "faraday"], QuantulumAnnotationEntityType.CHARGE, "https://en.wikipedia.org/wiki/Faraday_constant", [], []
    FARAD = "farad", ["farad"], QuantulumAnnotationEntityType.CAPACITANCE, "https://en.wikipedia.org/wiki/Farad", [], [
        "F"]
    MILLIFARAD = "millifarad", [
        "millifarad"], QuantulumAnnotationEntityType.CAPACITANCE, "https://en.wikipedia.org/wiki/Farad", [], ["mF"]
    MICROFARAD = "microfarad", [
        "microfarad"], QuantulumAnnotationEntityType.CAPACITANCE, "https://en.wikipedia.org/wiki/Farad", [], ["\u03bcF"]
    HENRY = "henry", [
        "henry"], QuantulumAnnotationEntityType.INDUCTANCE, "https://en.wikipedia.org/wiki/Henry_(unit)", [], ["H"]
    AMPERE_TURN = "ampere-turn", ["ampere-turn",
                                  "ampere turn"], QuantulumAnnotationEntityType.MAGNETOMOTIVE_FORCE, "https://en.wikipedia.org/wiki/Ampere-turn", [], [
        "AT", "At"]
    OERSTED = "oersted", [
        "oersted"], QuantulumAnnotationEntityType.MAGNETIC_FIELD, "https://en.wikipedia.org/wiki/Oersted", [], ["Oe"]
    WEBER = "weber", [
        "weber"], QuantulumAnnotationEntityType.MAGNETIC_FLUX, "https://en.wikipedia.org/wiki/Weber_(unit)", [], ["Wb"]
    MILLIWEBER = "milliweber", [
        "milliweber"], QuantulumAnnotationEntityType.MAGNETIC_FLUX, "https://en.wikipedia.org/wiki/Weber_(unit)", [], [
        "mWb"]
    MICROWEBER = "microweber", [
        "microweber"], QuantulumAnnotationEntityType.MAGNETIC_FLUX, "https://en.wikipedia.org/wiki/Weber_(unit)", [], [
        "\u00b5Wb"]
    MAXWELL = "maxwell", [
        "maxwell"], QuantulumAnnotationEntityType.MAGNETIC_FLUX, "https://en.wikipedia.org/wiki/Maxwell_(unit)", [], [
        "Mx"]
    TESLA = "tesla", [
        "tesla"], QuantulumAnnotationEntityType.MAGNETIC_FIELD, "https://en.wikipedia.org/wiki/Tesla_(unit)", [], ["T"]
    GAUSS = "gauss", [
        "gauss"], QuantulumAnnotationEntityType.MAGNETIC_FIELD, "https://en.wikipedia.org/wiki/Gauss_(unit)", [], ["G",
                                                                                                                   "Gs"]
    BECQUEREL = "becquerel", [
        "becquerel"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Becquerel", [], ["Bq"]
    MILLIBECQUEREL = "millibecquerel", [
        "millibecquerel"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Becquerel", [], [
        "mBq"]
    KILOBECQUEREL = "kilobecquerel", [
        "kilobecquerel"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Becquerel", [], [
        "kBq"]
    MEGABECQUEREL = "megabecquerel", [
        "megabecquerel"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Becquerel", [], [
        "MBq"]
    GIGABECQUEREL = "gigabecquerel", [
        "gigabecquerel"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Becquerel", [], [
        "GBq"]
    CURIE = "curie", [
        "curie"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Curie", [], ["Ci"]
    RUTHERFORD = "rutherford", [
        "rutherford"], QuantulumAnnotationEntityType.RADIOACTIVITY, "https://en.wikipedia.org/wiki/Rutherford_(unit)", [], [
        "Rd"]
    ROENTGEN = "roentgen", ["roentgen",
                            "r\u00f6ntgen"], QuantulumAnnotationEntityType.RADIATION_EXPOSURE, "https://en.wikipedia.org/wiki/Roentgen_(unit)", [], [
        "R"]
    RAD = "rad", [
        "rad"], QuantulumAnnotationEntityType.RADIATION_ABSORBED_DOSE, "https://en.wikipedia.org/wiki/Rad_(unit)", [], []
    SIEVERT = "sievert", [
        "sievert"], QuantulumAnnotationEntityType.RADIATION_ABSORBED_DOSE, "https://en.wikipedia.org/wiki/Sievert", [], [
        "Sv"]
    GRAY = "gray", [
        "gray"], QuantulumAnnotationEntityType.RADIATION_ABSORBED_DOSE, "https://en.wikipedia.org/wiki/Gray_(unit)", [], [
        "Gy"]
    KILOGRAY = "kilogray", [
        "kilogray"], QuantulumAnnotationEntityType.RADIATION_ABSORBED_DOSE, "https://en.wikipedia.org/wiki/Gray_(unit)", [], [
        "kGy"]
    MILLIGRAY = "milligray", [
        "milligray"], QuantulumAnnotationEntityType.RADIATION_ABSORBED_DOSE, "https://en.wikipedia.org/wiki/Gray_(unit)", [], [
        "mGy"]
    PIXEL = "pixel", ["pixel", "dots", "pel",
                      "picture element"], QuantulumAnnotationEntityType.TYPOGRAPHICAL_ELEMENT, "https://en.wikipedia.org/wiki/Pixel", [], [
        "px"]
    MEGAPIXEL = "megapixel", [
        "megapixel"], QuantulumAnnotationEntityType.TYPOGRAPHICAL_ELEMENT, "https://en.wikipedia.org/wiki/Pixel#Megapixel", [], [
        "MP"]
    BOARD_FOOT = "board-foot", ["board-foot",
                                "board foot"], QuantulumAnnotationEntityType.VOLUME_LUMBER, "https://en.wikipedia.org/wiki/Board_foot", [], [
        "FBM", "BDFT", "BF"]
    KATAL = "katal", [
        "katal"], QuantulumAnnotationEntityType.CATALYTIC_ACTIVITY, "https://en.wikipedia.org/wiki/Katal", [], ["kat"]
    GRAM_PER_CUBIC_CENTIMETRE = "gram per cubic centimetre", ["gram per cubic centimetre",
                                                              "gram per cubic centimeter"], QuantulumAnnotationEntityType.DENSITY, "https://en.wikipedia.org/wiki/Gram_per_cubic_centimetre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.GRAM, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.CENTIMETRE, power=-3), ], []
    KILOGRAM_PER_CUBIC_METRE = "kilogram per cubic metre", ["kilogram per cubic metre",
                                                            "kilogram per cubic meter"], QuantulumAnnotationEntityType.DENSITY, "https://en.wikipedia.org/wiki/Kilogram_per_cubic_metre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOGRAM, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=-3), ], []
    GRAM_PER_LITRE = "gram per litre", ["gram per litre",
                                        "gram per liter"], QuantulumAnnotationEntityType.CONCENTRATION, "https://en.wikipedia.org/wiki/Gram_per_litre", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.GRAM, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.LITRE, power=-1), ], []
    CUBIC_METRE_PER_SECOND = "cubic metre per second", ["cubic metre per second", "cubic meter per second",
                                                        "cumec"], QuantulumAnnotationEntityType.VOLUMETRIC_FLOW, "https://en.wikipedia.org/wiki/Cubic_metre_per_second", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.METRE, power=3),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], []
    CUBIC_FOOT_PER_SECOND = "cubic foot per second", [
        "cubic foot per second"], QuantulumAnnotationEntityType.VOLUMETRIC_FLOW, "https://en.wikipedia.org/wiki/Cubic_foot#Cubic_foot_per_minute", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=3),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], [
        "CFPM", "CFM"]
    STANDARD_CUBIC_CENTIMETRE_PER_MINUTE = "standard cubic centimetre per minute", [
        "standard cubic centimetre per minute"], QuantulumAnnotationEntityType.VOLUMETRIC_FLOW, "https://en.wikipedia.org/wiki/SCCM_(flow_unit)", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.CENTIMETRE, power=3),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MINUTE, power=-1), ], [
        "SCCM"]
    STANDARD_CUBIC_FEET_PER_MINUTE = "standard cubic feet per minute", [
        "standard cubic feet per minute"], QuantulumAnnotationEntityType.VOLUMETRIC_FLOW, "https://en.wikipedia.org/wiki/Standard_cubic_feet_per_minute", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.FOOT, power=3),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MINUTE, power=-1), ], [
        "SCFM"]
    STANDARD_LITRE_PER_MINUTE = "standard litre per minute", [
        "standard litre per minute"], QuantulumAnnotationEntityType.VOLUMETRIC_FLOW, "https://en.wikipedia.org/wiki/Standard_litre_per_minute", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.LITRE, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MINUTE, power=-1), ], ["SLM",
                                                                                                                  "SLPM"]
    POUND_PER_HOUR = "pound per hour", [
        "pound per hour"], QuantulumAnnotationEntityType.MASS_FLOW, "https://en.wikipedia.org/wiki/Pound_per_hour", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.POUND_MASS, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.HOUR, power=-1), ], ["PPH"]
    BIT_PER_SECOND = "bit per second", ["bit per second",
                                        "baud"], QuantulumAnnotationEntityType.DATA_TRANSFER_RATE, "https://en.wikipedia.org/wiki/Bit_rate", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.BIT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], ["bps",
                                                                                                                  "Bd"]
    KILOBIT_PER_SECOND = "kilobit per second", [
        "kilobit per second"], QuantulumAnnotationEntityType.DATA_TRANSFER_RATE, "https://en.wikipedia.org/wiki/Bit_rate", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.KILOBIT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], [
        "kbps"]
    MEGABIT_PER_SECOND = "megabit per second", [
        "megabit per second"], QuantulumAnnotationEntityType.DATA_TRANSFER_RATE, "https://en.wikipedia.org/wiki/Bit_rate", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.MEGABIT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], [
        "Mbps"]
    GIGABIT_PER_SECOND = "gigabit per second", [
        "gigabit per second"], QuantulumAnnotationEntityType.DATA_TRANSFER_RATE, "https://en.wikipedia.org/wiki/Bit_rate", [
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.GIGABIT, power=1),
        QuantulumAnnotationUnitDimensionType(base=QuantulumAnnotationUnitDimensionBaseType.SECOND, power=-1), ], [
        "Gbps"]
    DARCY = "darcy", ["darcy",
                      "darcy unit"], QuantulumAnnotationEntityType.PERMEABILITY, "https://en.wikipedia.org/wiki/Darcy_(unit)", [], []
    LANGLEY = "langley", [
        "langley"], QuantulumAnnotationEntityType.IRRADIANCE, "https://en.wikipedia.org/wiki/Langley_(unit)", [], ["Ly"]
    DENIER = "denier", [
        "denier"], QuantulumAnnotationEntityType.LINEAR_MASS_DENSITY, "https://en.wikipedia.org/wiki/Units_of_textile_measurement", [], [
        "den"]
    TEX = "tex", [
        "tex"], QuantulumAnnotationEntityType.LINEAR_MASS_DENSITY, "https://en.wikipedia.org/wiki/Units_of_textile_measurement", [], []
    DECITEX = "decitex", [
        "decitex"], QuantulumAnnotationEntityType.LINEAR_MASS_DENSITY, "https://en.wikipedia.org/wiki/Units_of_textile_measurement", [], [
        "dtex"]
    JANSKY = "jansky", [
        "jansky"], QuantulumAnnotationEntityType.FLUX_DENSITY, "https://en.wikipedia.org/wiki/Jansky", [], ["Jy"]
    MILLIJANSKY = "millijansky", ["millijansky", "milli flux unit",
                                  "millijanskys"], QuantulumAnnotationEntityType.FLUX_DENSITY, "https://en.wikipedia.org/wiki/Jansky", [], [
        "mJy", "mfu", "m.f.u."]
    UNKNOWN = "unknown", [
        "unknown"], QuantulumAnnotationEntityType.UNKNOWN, "", [], []

    @classmethod
    def from_quantulum(cls, obj: Unit) -> Self:
        candidates = []
        for unit in cls:
            if unit.name_ == obj.name:
                return unit
            if unit.surfaces and obj.name in unit.surfaces:
                candidates.append(unit)

        if candidates:
            logging.warning(f"Multiple candidates for {obj.name}: {candidates}")
            return random.choice(candidates)

        unit = cls.UNKNOWN
        return unit


class QuantulumAnnotationQuantity(BaseModel):
    value: str
    unit: QuantulumAnnotationUnit
    surface: str
    span: Tuple[int, int]
    uncertainty: Optional[float] = None
    derived_unit: Optional[QuantulumAnnotationUnitTypeMixin] = None
    derived_entity: Optional[QuantulumAnnotationEntityTypeMixin] = None

    @classmethod
    def from_quantulum(cls, obj: Quantity) -> Self:
        unit = QuantulumAnnotationUnit.from_quantulum(obj.unit)
        if unit == QuantulumAnnotationUnit.UNKNOWN:
            logging.warning(f"Unknown unit {obj.unit.name}")
            derived_unit = QuantulumAnnotationUnitTypeMixin(
                name_=obj.unit.name,
                uri=obj.unit.uri,
                entity=QuantulumAnnotationEntityType.UNKNOWN,
                surfaces=obj.unit.surfaces,
                symbols=obj.unit.symbols,
                dimensions=obj.unit.dimensions,
            )
            derived_entity = QuantulumAnnotationEntityTypeMixin(
                name_=obj.unit.entity.name,
                uri=obj.unit.entity.uri,
                dimensions=obj.unit.entity.dimensions,
            )
        else:
            derived_unit = None
            derived_entity = None

        return cls(
            value=str(obj.value),
            unit=unit,
            surface=obj.surface,
            span=obj.span,
            uncertainty=obj.uncertainty,
            derived_unit=derived_unit,
            derived_entity=derived_entity
        )


class QuantulumAnnotationInstance(BaseModel):
    entries: List[QuantulumAnnotationQuantity]

    @classmethod
    def from_quantulum(cls, obj: List[Quantity]) -> Self:
        return cls(
            entries=[QuantulumAnnotationQuantity.from_quantulum(quantity) for quantity in obj]
        )
