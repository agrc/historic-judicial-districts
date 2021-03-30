import numpy as np
import pandas as pd
import pytest

from lookback import models


@pytest.fixture
def shape_data():
    shape_df = pd.DataFrame(
        data={
            'county_key': ['uts_co_S1', 'uts_co_s2', 'uts_co_s3', 'uts_co_s4'],
            'START_DATE': ['2020-02-05', '2020-02-20', '2020-02-25', '2020-03-01'],
            'END_DATE': ['2020-02-19', '2020-02-24', '2021-02-28', '2021-01-01'],
        },
    )
    shape_df['END_DATE'] = pd.to_datetime(shape_df['END_DATE'])
    shape_df['START_DATE'] = pd.to_datetime(shape_df['START_DATE'])
    shape_df.set_index('START_DATE', drop=False, inplace=True)

    return shape_df


@pytest.fixture
def district_data():
    district_df = pd.DataFrame(
        data={
            'NewDistrict': ['1', '2', '3', '4'],
            'district_key': ['co_D1', 'co_D2', 'co_D3', 'co_D4'],
            'StartDate': ['2020-02-10', '2020-02-15', '2020-02-25', '2020-03-01'],
            'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28', None],
        },
    )
    district_df['StartDate'] = pd.to_datetime(district_df['StartDate'])
    district_df['EndDate'] = pd.to_datetime(district_df['EndDate'])
    district_df.set_index('StartDate', drop=False, inplace=True)

    return district_df


def test_change_dates_without_district_end_date(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[5, test_columns].values.tolist() == [
        np.datetime64('2020-03-01'), 'co', 'uts_co_s4', '4', 'co_D4'
    ]
