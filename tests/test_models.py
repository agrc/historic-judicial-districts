import numpy as np
import pandas as pd
import pytest

from lookback import models


@pytest.fixture
def shape_data():
    shape_df = pd.DataFrame(
        data={
            'county_key': ['uts_co_S1', 'uts_co_S2', 'uts_co_S3', 'uts_co_S4'],
            'START_DATE': ['2020-02-05', '2020-02-20', '2020-02-25', '2020-03-01'],
            'END_DATE': ['2020-02-19', '2020-02-24', '2020-02-28', '2021-01-01'],
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


def test_change_dates_shape_before_district(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[0, test_columns].values.tolist() == [
        np.datetime64('2020-02-05'), 'co', 'uts_co_S1', 'n/a', 'n/a'
    ]


def test_change_dates_new_district_existing_shape(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[1, test_columns].values.tolist() == [
        np.datetime64('2020-02-10'), 'co', 'uts_co_S1', '1', 'co_D1'
    ]


def test_change_dates_change_district_same_shape(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[2, test_columns].values.tolist() == [
        np.datetime64('2020-02-15'), 'co', 'uts_co_S1', '2', 'co_D2'
    ]


def test_change_dates_same_district_change_shape(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[3, test_columns].values.tolist() == [
        np.datetime64('2020-02-20'), 'co', 'uts_co_S2', '2', 'co_D2'
    ]


def test_change_dates_change_district_change_shape(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[4, test_columns].values.tolist() == [
        np.datetime64('2020-02-25'), 'co', 'uts_co_S3', '3', 'co_D3'
    ]


def test_change_dates_change_district_change_shape_no_district_end_date(mocker, shape_data, district_data):
    county = mocker.Mock()
    county.name = 'co'
    county.shape_df = shape_data
    county.district_df = district_data

    models.County.calc_change_dates(county)

    test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

    assert county.change_dates_df.loc[5, test_columns].values.tolist() == [
        np.datetime64('2020-03-01'), 'co', 'uts_co_S4', '4', 'co_D4'
    ]


def test_shapefile_uts_to_county_key():
    assert models.create_county_key('uts_saltlake') == 'saltlake'


def test_shapefile_utt_to_county_key():
    assert models.create_county_key('utt_shambip') == 'shambip'


def test_shapefile_ter_to_county_key():
    assert models.create_county_key('utt') == 'utt'


def test_district_complex_to_county_key():
    assert models.create_county_key('St. Marys') == 'stmarys'


def test_richland_rename_county_key():
    assert models.create_county_key('Richland') == 'rich'


def test_nulls_to_none():
    test_df = pd.DataFrame(data={'number': [None, None], 'date': [None, None]})
    test_df['number'] = test_df['number'].astype('float64')
    test_df['date'] = pd.to_datetime(test_df['date'])

    none_rows = []
    for row in test_df.values.tolist():
        none_rows.append(models.nulls_to_nones(row))

    for row in none_rows:
        assert row == [None, None]


@pytest.fixture
def names_shape_data():
    shape_df = pd.DataFrame(
        data={
            'ID': ['uts_grand', 'uts_rich', 'uts_rich', 'utt_shambip'],
            'NAME': ['GRAND', 'RICHLAND', 'RICH', 'SHAMBIP (ext)'],
            # 'county_key': ['uts_co_S1', 'uts_co_S2', 'uts_co_S3', 'uts_co_S4'],
            'START_DATE': ['2020-02-05', '2020-02-20', '2020-02-25', '2020-03-01'],
            # 'END_DATE': ['2020-02-19', '2020-02-24', '2020-02-28', '2021-01-01'],
        },
    )
    # shape_df['END_DATE'] = pd.to_datetime(shape_df['END_DATE'])
    shape_df['START_DATE'] = pd.to_datetime(shape_df['START_DATE'])
    # shape_df.set_index('START_DATE', drop=False, inplace=True)

    return shape_df


@pytest.fixture
def names_district_data():
    district_df = pd.DataFrame(
        data={
            'CountyName': ['grand', 'rich', 'richland', 'shambip'],
            # 'NewDistrict': ['1', '2', '3', '4'],
            # 'district_key': ['co_D1', 'co_D2', 'co_D3', 'co_D4'],
            'StartDate': ['2020-02-10', '2020-02-15', '2020-02-25', '2020-03-01'],
            # 'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28', None],
        },
    )
    district_df['StartDate'] = pd.to_datetime(district_df['StartDate'])
    # district_df['EndDate'] = pd.to_datetime(district_df['EndDate'])
    # district_df.set_index('StartDate', drop=False, inplace=True)

    return district_df


#: TODO: this test is not telling me anything useful right now...
def test_setup_both_rich_names_into_rich(names_shape_data, names_district_data):
    test_state = models.State()
    test_state.counties_df = names_shape_data
    test_state.districts_df = names_district_data
    test_state.setup_counties()

    # names = [county.name for county in test_state.counties]
    # assert names == ['grand', 'rich', 'shambip']
    rich_shapes, rich_districts = [
        (county.shape_df, county.district_df) for county in test_state.counties if county.name == 'rich'
    ][0]
    assert rich_shapes.shape == (2, 3)
    assert rich_districts.shape == (2, 2)
