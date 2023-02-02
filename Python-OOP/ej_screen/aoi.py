from typing import Union

import requests
from shapely.geometry import Polygon, LineString, Point


UNITS = {
    'miles': '9035',
    'kilometers': '9036',
}


### GEOMETRY 
class GeometryAOI: 
    def __init__(self, geom: Union[Polygon, LineString, Point], buffer: float, unit: str):
        self.geom = geom
        if buffer is None:
            buffer = ""
        self.payload = {
            'namestr': '', 
            'geometry': f"{self._define_spatial_reference()}",
            'distance': str(buffer),
            'unit': UNITS[unit], 
            'areatype': '',
            'areaid': '', 
            'f':'pjson'
        }
    def _stylize_geometry(self):
        pass

    def _define_spatial_reference(self):
        pass

class PointAOI(GeometryAOI):
    def _define_spatial_reference(self):
        x, y = self.geom.xy 
        geom_dict = {'spatialReference':{'wkid':4326},'x':x[0],'y':y[0]}
        return geom_dict

class LineAOI(GeometryAOI):
    def _stylize_geometry(self):
        coords = self.geom.coords[:]
        geom_list = [[list(t) for t in coords]] # convert tuples to list
        return geom_list

    def _define_spatial_reference(self):
        geom_list = self._stylize_geometry()
        geom_dict = {'spatialReference':{'wkid':4326},'paths': geom_list}
        return geom_dict

class PolygonAOI(GeometryAOI):
    def _stylize_geometry(self):
        coords = self.geom.exterior.coords[:]
        geom_list = [[list(t) for t in coords]] # convert tuples to list
        return geom_list

    def _define_spatial_reference(self):
        geom_list = self._stylize_geometry()
        geom_dict = {'spatialReference':{'wkid':4326},'rings': geom_list}
        return geom_dict


## Census
class Census: 
    def __init__(self, FIPS: float, geom: str = None):
        self.geom = geom
        self.payload = {
            'namestr': FIPS, 
            'geometry': '', 
            'distance': '',
            'unit': '9035',
            'areatype': self._define_area_type,
            'areaid': FIPS, 
            'f':'pjson'
        }

class BlockGroup(Census):
    def _define_area_type(self):
        return 'blockgroup'

class Tract(Census):
    def _define_area_type(self):
        return 'tract'

class City(Census):
    def _define_area_type(self):
        return 'city'

class County(Census):
    def _define_area_type(self):
        return 'county'


