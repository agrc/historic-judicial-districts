#!/usr/bin/env python
# * coding: utf8 *
"""
a description of what this module does.
this file is for testing linting...
"""

from . import models

if __name__ == '__main__':

    districts_csv = r'C:\gis\Projects\HistoricCounties\Data\JudicialDistricts\test.csv'
    counties_shp = r'C:\gis\Projects\HistoricCounties\Data\HistoricalCountyBoundaries\UT_Historical_Counties\UT_Historical_Counties.shp'

    state = models.State()
    state.load_counties(counties_shp)
    state.load_districts(districts_csv)
    state.setup_counties()

    print(state.counties['Beaver'])
