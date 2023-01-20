from typing import Union, List

import requests
from shapely.geometry import Polygon, LineString, Point, base
from urllib.parse import urlencode
import pandas as pd
import geopandas as gpd


UNITS = {
    'miles': '9035',
    'kilometers': '9036',
}


# need tow ork out logic 

class EJScreenAPI:
    api_base_url = 'https://ejscreen.epa.gov/mapper/ejscreenRESTbroker.aspx'

    def __init__(self, 
        namestr: Union[str, List[Union[str, int]]] = None,
        geometry: Union[Point, LineString, Polygon, gpd.GeoDataFrame] = None,
        buffer: float = None,
        unit: str = 'miles', 
        areatype: Union[str, List[str]] = None,
        areaid: Union[str, List[str, int]] = None,):

        # initialize parameters
        self.namestr = namestr
        self.geometry = geometry
        self.buffer = buffer
        self.unit = unit
        self.areatype = areatype
        self.areaid = areaid
        self._request_type = None # batch or single - determine based on type of namestr or geometry
        self._aoi_type = None # census or geometry

        # determine if census-type aoi or geometry-type aoi

        self._format_aoi_input() # determines if single or batch request

    def _define_aoi(self):
        # parse type of aoi (geometry or census and then which sub-type)
        if isinstance(self.aoi_input, Point):
            return PointAOI(self.geom, self.buffer, self.unit)
        pass

    def _format_aoi_input(self):
        # need to get geometry to shapely geometry for EJGeometry classes
        if isinstance(self.aoi_input, base.BaseGeometry):
            self._request_type = 'Single'
        elif isinstance(self.aoi_input, gpd.GeoDataFrame):
            self._request_type = 'Batch'
        else:
            if isinstance(self.aoi_input, List):
                if len(self.aoi_input) == 1:
                    self._aoi_input = Point(self._aoi_input)
                    self._request_type = 'Single'
                elif (len(self.aoi_input) > 1) and (self.aoi_input[0] == self.aoi_input[-1]):
                    self._aoi_input = Polygon(self.aoi_input)
                    self._request_type = 'Single'
                elif (len(self.aoi_input) > 1):
                    self._aoi_input = LineString(self.aoi_input)
                    self._request_type = 'Single'
                else:
                    raise ValueError("aoi_input must be a geodataframe, Shapely geometry, or Shapely-compatible list of coordinate pairs")

                    

    def send_request(self):
        self.full_url = self.api_base_url + "?" +  urlencode(self.payload, safe=":+{}[]'', ").replace("+", '')
        self.response = requests.get(self.full_url)

    def get_data(self):
        return self.response.json()

    def batch_request(self) -> pd.DataFrame:
        #  just geodataframes?
        pass



### GEOMETRY 
class GeometryAOI: 
    def __init__(self, geom = Union[Polygon, LineString, Point], buffer: float = 1, unit: str = 'miles'):
        self.geom = geom
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
        coords = self.geom.coords[:]
        geom_list = [list(t) for t in coords] # convert tuples to list
        return geom_list

    def _define_spatial_reference(self):
        pass

class PointAOI(GeometryAOI):
    def _define_spatial_reference(self):
        x, y = self.geom.xy 
        geom_dict = {'spatialReference':{'wkid':4326},'x':x[0],'y':y[0]}
        return geom_dict

class LineAOI(GeometryAOI):
    def _define_spatial_reference(self):
        geom_list = self._stylize_geometry()
        geom_dict = {'spatialReference':{'wkid':4326},'paths': geom_list}
        return geom_dict

class PolygonAOI(GeometryAOI):
    def _define_spatial_reference(self):
        geom_list = self._stylize_geometry()
        geom_dict = {'spatialReference':{'wkid':4326},'rings': geom_list}
        return geom_dict


## Census
class Census: 
    def __init__(self, geom: str):
        self.geom = geom
        self.payload = {
            'namestr': '', 
            'geometry': '', 
            'distance': '',
            'unit': '',
            'areatype': '',
            'areaid': '', 
            'f':'pjson'
        }

class BlockGroup(Census):
    pass

class Tract(Census):
    pass

class City(Census):
    pass

class County(Census):
    pass


