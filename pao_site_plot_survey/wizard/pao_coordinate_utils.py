# -*- coding: utf-8 -*-
"""Coordinate parsing shared by every site-import wizard (standard Excel,
KML, GLOBALG.A.P. audit-duration format...). Kept here, not on any one
wizard, so all of them handle plain decimal degrees, decimal-comma and
degrees/minutes/seconds notation the same way."""
import re

# Matches a degrees/minutes/seconds coordinate with optional hemisphere letter,
# e.g. 18°30'32.46"N, 100 34 43.5 O, -100° 34' 43.5". Degrees is the only
# required group; minutes/seconds default to 0 when absent.
DMS_HEMISPHERE_RE = re.compile(r'[NSEWOnsewo]')
DMS_NUMBER_RE = re.compile(r'-?\d+(?:[.,]\d+)?')


def parse_coordinate(raw):
    """Parse a single latitude/longitude value that may be either a plain
    decimal degree value (18.509017, or "18,509017" with a decimal comma)
    or a degrees/minutes/seconds string (18°30'32.46"N, -100 34 43.5 O)."""
    if raw is None or raw == '':
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text.replace(',', '.'))
    except ValueError:
        pass
    return dms_to_decimal(text)


def dms_to_decimal(text):
    hemisphere_match = DMS_HEMISPHERE_RE.search(text)
    hemisphere = hemisphere_match.group(0).upper() if hemisphere_match else None
    cleaned = DMS_HEMISPHERE_RE.sub('', text)
    numbers = [float(n.replace(',', '.')) for n in DMS_NUMBER_RE.findall(cleaned)]
    if not numbers:
        raise ValueError(text)
    negative = numbers[0] < 0
    degrees = abs(numbers[0])
    minutes = numbers[1] if len(numbers) > 1 else 0.0
    seconds = numbers[2] if len(numbers) > 2 else 0.0
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if negative or hemisphere in ('S', 'W', 'O'):
        decimal = -decimal
    return decimal


def parse_combined_point(raw):
    """Parse a single cell holding both coordinates together as
    'lat lon' / 'lat,lon', in decimal or DMS notation for each part
    (e.g. '25°19\'43.59"N 111°40\'41.52"W')."""
    raw = (raw or '').strip()
    if not raw:
        return None, None
    parts = raw.split()
    if len(parts) != 2:
        parts = [p.strip() for p in raw.split(',') if p.strip()]
    if len(parts) != 2:
        raise ValueError(raw)
    lat = parse_coordinate(parts[0])
    lng = parse_coordinate(parts[1])
    if lat is None or lng is None:
        raise ValueError(raw)
    return lat, lng
