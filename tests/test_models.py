import numpy as np
import pandas as pd
import pytest

from lookback import models


@pytest.fixture
def shape_data():
    shape_df = pd.DataFrame(
        data={
            'shape_key': ['uts_co_S1', 'uts_co_S2', 'uts_co_S3', 'uts_co_S4'],
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


def test_nulls_to_none_normals_ok():
    test_df = pd.DataFrame(data={'number': [1.0, None], 'date': ['2021-03-01', None]})
    test_df['number'] = test_df['number'].astype('float64')
    test_df['date'] = pd.to_datetime(test_df['date'])

    none_rows = []
    # for row in test_df.values.tolist():
    #     none_rows.append(models.nulls_to_nones(row))
    none_rows.append(models.nulls_to_nones(test_df.loc[0, :].values.tolist()))
    none_rows.append(models.nulls_to_nones(test_df.loc[1, :].values.tolist()))

    assert none_rows[0] == [1.0, np.datetime64('2021-03-01')]
    assert none_rows[1] == [None, None]


@pytest.fixture
def all_districts_df():
    district_df = pd.DataFrame(
        data={
            'CountyName': ['grand', 'richland', 'rich', 'shambip'],
            'StartDate': ['2020-02-10', '2020-02-15', '2020-02-25', '2020-03-01'],
            'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28', None],
            'NewDistrict': ['1', '1', '2', '4'],
            'OldDistrict': ['1', '1', '1', '4'],
            'Version': ['1', '1', '2', '1'],
        },
    )

    return district_df


def test_load_districts_simple(mocker, all_districts_df):
    pd.read_csv = mocker.Mock(return_value=all_districts_df)
    test_state = models.State()
    test_state.load_districts('foo')
    assert test_state.all_districts_df.loc[0, :].values.tolist() == [
        'grand',
        np.datetime64('2020-02-10'),
        np.datetime64('2020-02-14'),
        '1',
        '1',
        '1',
        'grand',
        'grand_D1',
    ]


def test_load_districts_rich(mocker, all_districts_df):
    pd.read_csv = mocker.Mock(return_value=all_districts_df)
    test_state = models.State()
    test_state.load_districts('foo')

    assert test_state.all_districts_df.loc[1, :].values.tolist() == [
        'richland',
        np.datetime64('2020-02-15'),
        np.datetime64('2020-02-24'),
        '1',
        '1',
        '1',
        'rich',
        'richland_D1',
    ]
    assert test_state.all_districts_df.loc[2, :].values.tolist() == [
        'rich',
        np.datetime64('2020-02-25'),
        np.datetime64('2020-02-28'),
        '2',
        '1',
        '2',
        'rich',
        'rich_D2',
    ]


def test_state_setup_richland_into_rich(mocker):
    all_districts_df = pd.DataFrame(
        data={
            'CountyName': ['grand', 'richland', 'rich', 'shambip'],
            'StartDate': ['2020-02-10', '2020-02-15', '2020-02-25', '2020-03-01'],
            'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28', None],
            'NewDistrict': ['1', '1', '2', '4'],
            'OldDistrict': ['1', '1', '1', '4'],
            'Version': ['1', '1', '2', '1'],
            'county_key': ['grand', 'rich', 'rich', 'shambip'],
            'district_key': ['grand_D1', 'richland_D1', 'rich_D2', 'shambip_D1']
        },
    )
    mocker.patch('lookback.models.County')
    test_state = mocker.Mock()
    test_state.all_districts_df = all_districts_df
    test_state.counties = []
    models.State.setup_counties(test_state)
    assert len(test_state.counties) == 3


def test_county_setup_richland_into_rich(mocker):
    all_districts_df = pd.DataFrame(
        data={
            'CountyName': ['grand', 'richland', 'rich', 'shambip'],
            'StartDate': ['2020-02-10', '2020-02-15', '2020-02-25', '2020-03-01'],
            'EndDate': ['2020-02-14', '2020-02-24', '2020-02-28', None],
            'NewDistrict': ['1', '1', '2', '4'],
            'OldDistrict': ['1', '1', '1', '4'],
            'Version': ['1', '1', '2', '1'],
            'county_key': ['grand', 'rich', 'rich', 'shambip'],
            'district_key': ['grand_D1', 'richland_D1', 'rich_D2', 'shambip_D1']
        },
    )
    all_shapes_df = pd.DataFrame(
        data={
            'NAME': ['RICHLAND', 'RICH', 'SHAMBIP'],
            'ID': ['uts_rich', 'uts_rich', 'utt_shambip'],
            'START_DATE': ['2020-02-15', '2020-02-25', '2020-03-01'],
            'county_key': ['rich', 'rich', 'shambip']
        }
    )

    rich = models.County('rich')
    rich.setup(all_shapes_df, all_districts_df)

    assert 'RICH' in rich.shape_df['NAME'].unique()
    assert 'RICHLAND' in rich.shape_df['NAME'].unique()
    assert 'SHAMBIP' not in rich.shape_df['NAME'].unique()

    assert 'rich' in rich.district_df['CountyName'].unique()
    assert 'richland' in rich.district_df['CountyName'].unique()
    assert 'grand' not in rich.district_df['CountyName'].unique()
    assert 'sambip' not in rich.district_df['CountyName'].unique()


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
