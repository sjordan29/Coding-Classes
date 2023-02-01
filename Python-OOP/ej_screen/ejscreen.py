from typing import Union, List
from abc import ABC, abstractmethod

import requests
from shapely.geometry import Polygon, LineString, Point, base
from urllib.parse import urlencode
import pandas as pd
import geopandas as gpd


UNITS = {
    'miles': '9035',
    'kilometers': '9036',
}


# Thoughts
# A lot of confusing / annoying logic in EJScreenAPI 
# Have "Handler" abstract base class,
# Then a census / geometry handler that handles all the logic from there. 
class Handler(ABC):
    @abstractmethod
    def determine_request_type():
        """Determine if job is a batch or single job"""
        pass

    @abstractmethod
    def _format_inputs():
        pass
    
    @abstractmethod
    def define_aoi():
        pass

class GeometryHandler(Handler):
    def determine_request_type(self, geometry):
        """Determine if job is a batch or single job

        For geometries, if it's a Shapely base geometry or a list, it's a single run
        and if it's a geopandas geodataframe, then it's a batch run. 
        """
        self.geometry = geometry
        if isinstance(self.geometry, base.BaseGeometry):
            request_type = 'Single'
        elif isinstance(self.geometry, List):
            request_type = 'Single'
            self.geometry = self._format_inputs()
        elif isinstance(self.geometry, gpd.GeoDataFrame):
            request_type = 'Batch'
        return request_type, self.geometry
    
    def _format_inputs(self):
        """"""
        if len(self.geometry) == 1:
            self.geometry = Point(self.geometry)
            self._request_type = 'Single'
        elif (len(self.geometry) > 1) and (self.geometry[0] == self.geometry[-1]):
            self.geometry = Polygon(self.geometry)
            self._request_type = 'Single'
        elif (len(self.geometry) > 1):
            self.geometry = LineString(self.geometry)
            self._request_type = 'Single'
        else:
            raise ValueError("aoi_input must be a geodataframe, Shapely geometry, or Shapely-compatible list of coordinate pairs")

    
    def define_aoi(self):
        if isinstance(self.geometry, Point):
            if self.buffer is None:
                print(f'Buffer required for Point type geometry. Assuming a buffer of 1 {self.unit}.')
                self.buffer = 1
            return PointAOI(self.geometry, self.buffer, self.unit)
        elif isinstance(self.geometry, LineString):
            if self.buffer is None:
                print(f'Buffer required for LineString type geometry. Assuming a buffer of 1 {self.unit}.')
                self.buffer = 1
            return LineAOI(self.geometry, self.buffer, self.unit)
        elif isinstance(self.geometry, Polygon):
            return PolygonAOI(self.geometry, self.buffer, self.unit)



 

class EJScreenAPI:
    api_base_url = 'https://ejscreen.epa.gov/mapper/ejscreenRESTbroker.aspx'

    def __init__(self, 
        namestr: float = None,
        geometry: Union[Point, LineString, Polygon, gpd.GeoDataFrame] = None,
        buffer: float = None,
        unit: str = 'miles', 
        areatype: str = None,
        areaid: float = None,):

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
        self._determine_aoi_type()
        print("AOI type:", self._aoi_type)
        
        # format AOI input for Geometry
        if self._aoi_type == "Geometry":
            self._format_geometry() # determines if single or batch request

        self.request_aoi = self._define_aoi()
    
    def _determine_aoi_type(self):
        if (self.namestr is None) & (not self.geometry is None):
            self._aoi_type = "Geometry"
        elif (not self.namestr is None) & (self.geometry is None):
            self._aoi_type = "Census"
        else:
            raise ValueError("Query type ambiguous. Please enter area_id for Census data OR geometry for geographic data.")

    def _define_aoi(self):
        # parse type of aoi (geometry or census and then which sub-type)
        if isinstance(self.geometry, Point):
            if self.buffer is None:
                print(f'Buffer required for Point type geometry. Assuming a buffer of 1 {self.unit}.')
                self.buffer = 1
            return PointAOI(self.geometry, self.buffer, self.unit)
        elif isinstance(self.geometry, LineString):
            if self.buffer is None:
                print(f'Buffer required for LineString type geometry. Assuming a buffer of 1 {self.unit}.')
                self.buffer = 1
            return LineAOI(self.geometry, self.buffer, self.unit)
        elif isinstance(self.geometry, Polygon):
            return PolygonAOI(self.geometry, self.buffer, self.unit)
        elif isinstance(self.areaid, float):
            if len(str(self.areaid)) == 5:
                return County(self.areaid)
            elif len(str(self.areaid)) == 7:
                return City(self.areaid)
            elif len(str(self.areaid)) == 11:
                return Tract(self.areaid)
            elif len(str(self.areaid)) == 12:
                return BlockGroup(self.areaid)
            else:
                raise ValueError("areaid must be a county, census tract, or block group FIPS code")
        pass

    def _format_geometry(self):
        # TO DO: currently assumes 
        if isinstance(self.geometry, base.BaseGeometry):
            self._request_type = 'Single'
        elif isinstance(self.geometry, gpd.GeoDataFrame):
            self._request_type = 'Batch'
        else:
            if isinstance(self.geometry, List):
                if len(self.geometry) == 1:
                    self.geometry = Point(self.geometry)
                    self._request_type = 'Single'
                elif (len(self.geometry) > 1) and (self.geometry[0] == self.geometry[-1]):
                    self.geometry = Polygon(self.geometry)
                    self._request_type = 'Single'
                elif (len(self.geometry) > 1):
                    self.geometry = LineString(self.geometry)
                    self._request_type = 'Single'
                else:
                    raise ValueError("aoi_input must be a geodataframe, Shapely geometry, or Shapely-compatible list of coordinate pairs")

                    

    def send_request(self):
        self.full_url = self.api_base_url + "?" +  urlencode(self.request_aoi.payload, safe=":+{}[]'', ").replace("+", '')
        self.response = requests.get(self.full_url)
        self.json = self.response.json()

    
    def _json_to_df(self):
        df = pd.json_normalize(self.json)
        # convert % columns to decimals
        # might be better to just look up which fields are %s based on documentation
        for col in df.columns:
            if str(df[col][0])[-1] == "%":
                df[col] = df[col].str.rstrip('%').astype('float') / 100
        # convert to numeric
        df = df.apply(pd.to_numeric, errors='ignore')
        return df
    
    def get_data(self, type='json'):
        if type == 'json':
            return self.json
        elif type == 'pandas':
            return self._json_to_df()
        elif type == 'geopandas':
            df = self._json_to_df()
            geometry = [self.geometry]
            return gpd.GeoDataFrame(df, crs = "EPSG:4326", geometry=geometry)
        else:
            raise ValueError("type must be 'json', 'pandas', or 'geopandas'")


    def batch_request(self) -> pd.DataFrame:
        #  just geodataframes?
        pass



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


