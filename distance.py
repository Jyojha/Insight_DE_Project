# For details see http://www.movable-type.co.uk/scripts/gis-faq-5.1.html

from math import asin, sin, cos, sqrt, pi

# Haight St and Central Ave
lonlat1 = (-122.44364908616127, 37.77042637070029)

# Haight St and Masonic Ave
lonlat2 = (-122.4453449903129, 37.77021017487183)


# in meters
EARTH_RADIUS = 6367000

def deg2rad(d):
    return pi * d / 180

def haversin(x, y, R=EARTH_RADIUS):
    lon1, lat1 = x
    lon2, lat2 = y

    lon1, lat1, lon2, lat2 = map(deg2rad, (lon1, lat1, lon2, lat2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(min(1,sqrt(a)))

    return R * c
