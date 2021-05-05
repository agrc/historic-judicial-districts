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
    counties_output_fc = r'C:\gis\Projects\HistoricCounties\HistoricCounties.gdb\test_output_counties'
    districts_output_fc = r'C:\gis\Projects\HistoricCounties\HistoricCounties.gdb\test_output_districts'
    district_version_parts_output_fc = r'C:\gis\Projects\HistoricCounties\HistoricCounties.gdb\test_output_district_version_parts'

    state = State()
    state.load_counties(counties_shp)
    state.load_districts(districts_csv)
    state.setup_counties()
    state.calc_counties()

    # print(state.counties[1].change_dates_df)
    # state.combine_change_dfs(change_dates_csv)
    state.get_shape_district_info()
    state.output_to_featureclass(counties_output_fc)

    state.setup_districts()
    state.calc_districts_versions()
    # state.combine_district_dicts(r'C:\gis\Projects\HistoricCounties\Data\JudicialDistricts\district_versions.pkl')
    state.combine_district_dicts(out_path=district_version_parts_output_fc)
    state.dissolve_districts(districts_output_fc)

    # state.verify_counties()


if __name__ == '__main__':

    main()
