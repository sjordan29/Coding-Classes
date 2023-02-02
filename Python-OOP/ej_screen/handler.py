
from typing import Union, List
from abc import ABC, abstractmethod

import requests
from shapely.geometry import Polygon, LineString, Point, base
import pandas as pd
import geopandas as gpd

from aoi import PointAOI, LineAOI, PolygonAOI, BlockGroup, Tract, City, County


# Thoughts
# A lot of confusing / annoying logic in EJScreenAPI 
# Have "Handler" abstract base class,
# Then a census / geometry handler that handles all the logic from there. 
class Handler(ABC):
    @abstractmethod
    def __init__():
        pass 

    @abstractmethod
    def determine_request_type():
        """Determine if job is a batch or single job"""
        pass

    @abstractmethod
    def _format_inputs(self):
        pass
    
    @abstractmethod
    def define_aoi(self):
        pass

class GeometryHandler(Handler):
    def __init__(self, geometry, buffer, unit):
        self.geometry = geometry
        self.buffer = buffer
        self.unit = unit


    def determine_request_type(self):
        """Determine if job is a batch or single job

        For geometries, if it's a Shapely base geometry or a list, it's a single run
        and if it's a geopandas geodataframe, then it's a batch run. 
        """
        if isinstance(self.geometry, base.BaseGeometry):
            request_type = 'Single'
        elif isinstance(self.geometry, List):
            request_type = 'Single'
            self._format_inputs()
        elif isinstance(self.geometry, gpd.GeoDataFrame):
            request_type = 'Batch'
        return request_type, self.geometry
    
    def _format_inputs(self):
        """Format geometry"""
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
        """Define the AOI class used for the API
        
        If the geometry is a Point, use PointAOI
        If the geometry is a LineString, use LineAOI
        If the geometry is a Polygon, use PolygonAOI
        """
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


class CensusHandler(Handler):
    def __init__(self, areaid, geometry):
        self.areaid = areaid
        self.geometry = geometry

    def determine_request_type(self):
        """For now, request type is always single. """
        request_type = 'Single'
        return request_type, self.geometry

    def _format_inputs(self):
        """Not needed for now. Think about if this would be needed?"""
        pass

    def define_aoi(self):
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