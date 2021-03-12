#!/usr/bin/env python
# * coding: utf8 *
"""
a description of what this module does.
this file is for testing linting...
"""

from lookback.models import State


def main():
    districts_csv = r'C:\gis\Projects\HistoricCounties\Data\JudicialDistricts\test.csv'
    counties_shp = r'C:\gis\Projects\HistoricCounties\Data\HistoricalCountyBoundaries\UT_Historical_Counties\UT_Historical_Counties.shp'
    change_dates_csv = r'C:\gis\Projects\HistoricCounties\Data\JudicialDistricts\change_dates.csv'
    output_fc = r'C:\gis\Projects\HistoricCounties\HistoricCounties.gdb\test_output'

    state = State()
    state.load_counties(counties_shp)
    state.load_districts(districts_csv)
    state.setup_counties()
    state.calc_counties()

    # print(state.counties[1].change_dates_df)
    state.combine_change_dfs(change_dates_csv)
    state.insert_geometries(output_fc, counties_shp)

    # state.test_counties()


if __name__ == '__main__':

    main()
