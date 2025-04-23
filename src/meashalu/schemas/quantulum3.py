# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan
from typing import List, Self

from pydantic import BaseModel
from quantulum3.classes import Quantity

from meashalu.schemas.quantulum import QuantulumAnnotationQuantity


class Quantulum3AnnotationInstance(BaseModel):
    entries: List[QuantulumAnnotationQuantity]

    @classmethod
    def from_quantulum(cls, obj: List[Quantity]) -> Self:
        return cls(
            entries=[QuantulumAnnotationQuantity.from_quantulum(quantity) for quantity in obj]
        )
