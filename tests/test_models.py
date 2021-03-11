import pandas as pd

from lookback import models


def test_calc_change_dates(mocker):
    county = mocker.Mock()

    #: Mock up shape and districts df
    county.shape_df = pd.DataFrame(
        data={
            'county_key': ['uts_co_S1', 'uts_co_s2', 'uts_co_s3'],
            'END_DATE': ['2020-02-19', '2020-02-24', '2020-02-28'],
        },
        index=['2020-02-05', '2020-02-20', '2020-02-25']
    )
    county.shape_df.index = pd.to_datetime(county.shape_df.index)
    county.shape_df['END_DATE'] = pd.to_datetime(county.shape_df['END_DATE'])

    county.district_df = pd.DataFrame(
        data={
            'NewDistrict': ['1', '2', '3'],
            'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28'],
        },
        index=['2020-02-10', '2020-02-15', '2020-02-25']
    )
    county.district_df.index = pd.to_datetime(county.district_df.index)
    county.district_df['EndDate'] = pd.to_datetime(county.district_df['EndDate'])

    #: Actual Test
    models.County.calc_change_dates(county)

    #: Data output dataframe should match this
    test_df = pd.DataFrame(
        data={
            'date': ['2020-02-05', '2020-02-10', '2020-02-15', '2020-02-20', '2020-02-25'],
            'county_version': ['uts_co_S1', 'uts_co_S1', 'uts_co_S1', 'uts_co_s2', 'uts_co_s3'],
            'district': ['n/a', '1', '2', '2', '3'],
        }
    )
    test_df['date'] = pd.to_datetime(test_df['date'])

    assert test_df.equals(county.change_dates_df)
