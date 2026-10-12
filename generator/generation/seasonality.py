from __future__ import annotations

import math
from datetime import datetime

def diurnal_factor(at: datetime) -> float:
    #Суточный множитель: пик около 19:00, минимум около 03:00.

    #Пик в 19:00 после работы, минимум 3:00 - все спят

    hour = at.hour + at.minute / 60.0 + at.second / 3600.0
    return math.cos(2.0 * math.pi * (hour - 19.0) / 24.0)


def annual_factor(at: datetime) -> float:
    """Годовой множитель для северного полушария.

    Максимум — середина июля (~день 196), минимум — середина января.
    """
    day_of_year = float(at.timetuple().tm_yday)
    return math.cos(2.0 * math.pi * (day_of_year - 196.0) / 365.25)