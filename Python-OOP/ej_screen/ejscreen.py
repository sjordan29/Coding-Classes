from typing import Union

import requests
from shapely.geometry import Polygon, LineString, Point
from urllib.parse import urlencode
import pandas as pd
import geopandas as gpd

from handler import GeometryHandler, CensusHandler

 

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
        self._key_parameter = None # will be geometry if Geometry or areaid if Census 
        self._request_type = None # batch or single - determine based on type of namestr or geometry
        self._aoi_type = None # census or geometry

        # determine if census-type aoi or geometry-type aoi
        self._aoi_type = self._determine_aoi_type()
        self._request_type, self.geometry = self._aoi_type.determine_request_type()
        self.request_aoi = self._aoi_type.define_aoi()
    
    def _determine_aoi_type(self):
        if (self.namestr is None) & (not self.geometry is None):
            # self._aoi_type = "Geometry"
            return GeometryHandler(self.geometry, self.buffer, self.unit)
        elif (not self.namestr is None) & (self.geometry is None):
            # self._aoi_type = "Census"
            return CensusHandler(self.areaid, self.geometry)
        else:
            raise ValueError("Query type ambiguous. Please enter area_id for Census data OR geometry for geographic data.")


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