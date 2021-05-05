import numpy as np
import pandas as pd
import pytest

from lookback import models


class TestChangeDatesGeneralCase:

    @pytest.fixture
    def shape_data(self):
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
    def district_data(self):
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

    def test_change_dates_shape_before_district(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[0, test_columns].values.tolist() == [
            np.datetime64('2020-02-05'), 'co', 'uts_co_S1', 'n/a', 'n/a'
        ]

    def test_change_dates_new_district_existing_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[1, test_columns].values.tolist() == [
            np.datetime64('2020-02-10'), 'co', 'uts_co_S1', '1', 'co_D1'
        ]

    def test_change_dates_change_district_same_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[2, test_columns].values.tolist() == [
            np.datetime64('2020-02-15'), 'co', 'uts_co_S1', '2', 'co_D2'
        ]

    def test_change_dates_same_district_change_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[3, test_columns].values.tolist() == [
            np.datetime64('2020-02-20'), 'co', 'uts_co_S2', '2', 'co_D2'
        ]

    def test_change_dates_change_district_change_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[4, test_columns].values.tolist() == [
            np.datetime64('2020-02-25'), 'co', 'uts_co_S3', '3', 'co_D3'
        ]

    def test_change_dates_change_district_change_shape_no_district_end_date(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[5, test_columns].values.tolist() == [
            np.datetime64('2020-03-01'), 'co', 'uts_co_S4', '4', 'co_D4'
        ]


class TestChangeDatesRichlandCase:

    @pytest.fixture
    def richland_shape_data(self):
        shape_df = pd.DataFrame(
            data={
                'shape_key': ['uts_richland_S1', 'uts_rich_S1', 'uts_rich_S2'],
                'START_DATE': ['2020-02-01', '2020-02-10', '2020-02-15'],
                'END_DATE': ['2020-02-09', '2020-02-14', '2020-02-24'],
            },
        )
        shape_df['END_DATE'] = pd.to_datetime(shape_df['END_DATE'])
        shape_df['START_DATE'] = pd.to_datetime(shape_df['START_DATE'])
        shape_df.set_index('START_DATE', drop=False, inplace=True)

        return shape_df

    @pytest.fixture
    def richland_district_data(self):
        district_df = pd.DataFrame(
            data={
                'NewDistrict': ['1', '1', '2'],
                'district_key': ['richland_D1', 'rich_D1', 'rich_D2'],
                'StartDate': ['2020-02-5', '2020-02-10', '2020-02-20'],
                'EndDate': [None, '2020-02-19', None],
            },
        )
        district_df['StartDate'] = pd.to_datetime(district_df['StartDate'])
        district_df['EndDate'] = pd.to_datetime(district_df['EndDate'])
        district_df.set_index('StartDate', drop=False, inplace=True)

        return district_df

    def test_change_dates_richland_shape_no_district(self, mocker, richland_shape_data, richland_district_data):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[0, test_columns].values.tolist() == [
            np.datetime64('2020-02-01'), 'rich', 'uts_richland_S1', 'n/a', 'n/a'
        ]

    def test_change_dates_richland_shape_richland_district(self, mocker, richland_shape_data, richland_district_data):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[1, test_columns].values.tolist() == [
            np.datetime64('2020-02-05'), 'rich', 'uts_richland_S1', '1', 'richland_D1'
        ]

    def test_change_dates_rich_shape_rich_district(self, mocker, richland_shape_data, richland_district_data):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[2, test_columns].values.tolist() == [
            np.datetime64('2020-02-10'), 'rich', 'uts_rich_S1', '1', 'rich_D1'
        ]

    def test_change_dates_rich_shape_rich_district_no_district_end_date(
        self, mocker, richland_shape_data, richland_district_data
    ):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['change_date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[4, test_columns].values.tolist() == [
            np.datetime64('2020-02-20'), 'rich', 'uts_rich_S2', '2', 'rich_D2'
        ]


class TestAddingExtraFields:

    def test_unique_district_key_creation(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01'],
                'district_number': ['1', '1S'],
                'EndDate': ['2029-12-31', '2039-12-31'],
                'county_version': ['uts_foo_S1', 'uts_foo_S1'],
                'END_DATE': ['2029-12-31', '2039-12-31'],
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['COMBINED_DST_KEY']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == ['1_2020-01-01']
        assert county_mock.joined_df.loc[1, test_columns].values.tolist() == ['1S_2030-01-01']

    def test_end_date_normal_county_mid_cycle_district_changes(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01', '2040-01-01'],  #: 3 so that there's a +1 for end date calc
                'district_number': ['1', '1S', '2S'],
                'EndDate': ['2029-12-31', '2039-12-31', '2049-12-31'],  #: District end date
                'county_version': ['uts_foo_S1', 'uts_foo_S1', 'uts_foo_S1'],  #: uts_something_Sx
                'END_DATE': ['2049-12-31', '2049-12-31', '2049-12-31'],  #: shape end date
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])
        county_mock.joined_df['END_DATE'] = pd.to_datetime(county_mock.joined_df['END_DATE'])
        county_mock.joined_df['EndDate'] = pd.to_datetime(county_mock.joined_df['EndDate'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['change_end_date']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == [np.datetime64('2029-12-31')]
        assert county_mock.joined_df.loc[1, test_columns].values.tolist() == [np.datetime64('2039-12-31')]

    def test_end_date_normal_county_mid_cycle_shape_changes(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01', '2040-01-01'],  #: 3 so that there's a +1 for end date calc
                'district_number': ['1', '1', '1'],
                'EndDate': ['2049-12-31', '2049-12-31', '2049-12-31'],  #: District end date
                'county_version': ['uts_foo_S1', 'uts_foo_S2', 'uts_foo_S3'],  #: uts_something_Sx
                'END_DATE': ['2029-12-31', '2039-12-31', '2049-12-31'],  #: shape end date
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])
        county_mock.joined_df['END_DATE'] = pd.to_datetime(county_mock.joined_df['END_DATE'])
        county_mock.joined_df['EndDate'] = pd.to_datetime(county_mock.joined_df['EndDate'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['change_end_date']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == [np.datetime64('2029-12-31')]
        assert county_mock.joined_df.loc[1, test_columns].values.tolist() == [np.datetime64('2039-12-31')]

    def test_end_date_normal_county_mid_cycle_both_change(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01', '2040-01-01'],  #: 3 so that there's a +1 for end date calc
                'district_number': ['1', '1S', '5'],
                'EndDate': ['2029-12-31', '2039-12-31', '2049-12-31'],  #: District end date
                'county_version': ['uts_foo_S1', 'uts_foo_S2', 'uts_foo_S3'],  #: uts_something_Sx
                'END_DATE': ['2029-12-31', '2039-12-31', '2049-12-31'],  #: shape end date
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])
        county_mock.joined_df['END_DATE'] = pd.to_datetime(county_mock.joined_df['END_DATE'])
        county_mock.joined_df['EndDate'] = pd.to_datetime(county_mock.joined_df['EndDate'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['change_end_date']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == [np.datetime64('2029-12-31')]
        assert county_mock.joined_df.loc[1, test_columns].values.tolist() == [np.datetime64('2039-12-31')]

    def test_end_date_normal_county_end_district_end_notatime(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01'],  #: 3 so that there's a +1 for end date calc
                'district_number': ['1', '1S'],
                'EndDate': ['2029-12-31', None],  #: District end date
                'county_version': ['uts_foo_S1', 'uts_foo_S1'],  #: uts_something_Sx
                'END_DATE': ['2029-12-31', '2037-07-07'],  #: shape end date (shape ends before current time)
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])
        county_mock.joined_df['END_DATE'] = pd.to_datetime(county_mock.joined_df['END_DATE'])
        county_mock.joined_df['EndDate'] = pd.to_datetime(county_mock.joined_df['EndDate'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['change_end_date']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == [np.datetime64('2029-12-31')]
        assert pd.isnull(county_mock.joined_df.loc[1, test_columns].values.tolist()[0])

    def test_end_date_extinct_county_end_both_same_date(self, mocker):
        county_mock = mocker.Mock()
        county_mock.joined_df = pd.DataFrame(
            data={
                'change_date': ['2020-01-01', '2030-01-01'],  #: 3 so that there's a +1 for end date calc
                'district_number': ['1', '1S'],
                'EndDate': ['2029-12-31', '2037-07-07'],  #: District end date
                'county_version': ['utt_extinct_S1', 'utt_extinct_S1'],  #: utt for territory, all utt except richland
                #: are extinct
                'END_DATE': ['2029-12-31', '2037-07-07'],  #: shape end date
            }
        )
        county_mock.joined_df['change_date'] = pd.to_datetime(county_mock.joined_df['change_date'])
        county_mock.joined_df['END_DATE'] = pd.to_datetime(county_mock.joined_df['END_DATE'])
        county_mock.joined_df['EndDate'] = pd.to_datetime(county_mock.joined_df['EndDate'])

        models.County.add_extra_fields(county_mock)

        test_columns = ['change_end_date']
        assert county_mock.joined_df.loc[0, test_columns].values.tolist() == [np.datetime64('2029-12-31')]
        assert county_mock.joined_df.loc[1, test_columns].values.tolist() == [np.datetime64('2037-07-07')]


class TestCountyKeyGeneration:

    def test_shapefile_uts_to_county_key(self):
        assert models.create_county_key('uts_saltlake') == 'saltlake'

    def test_shapefile_utt_to_county_key(self):
        assert models.create_county_key('utt_shambip') == 'shambip'

    def test_shapefile_ter_to_county_key(self):
        assert models.create_county_key('utt') == 'utt'

    def test_district_complex_to_county_key(self):
        assert models.create_county_key('St. Marys') == 'stmarys'

    def test_richland_rename_county_key(self):
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


class TestSetups:

    @pytest.fixture
    def all_districts_df(self):
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

    def test_load_districts_simple(self, mocker, all_districts_df):
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

    def test_load_districts_rich(self, mocker, all_districts_df):
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

    def test_state_setup_richland_into_rich(self, mocker):
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

    def test_county_setup_richland_into_rich(self, mocker):
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


class TestFinalJoins:

    @pytest.fixture
    def shape_data(self):
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
    def district_data(self):
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

    @pytest.fixture
    def change_dates_df(self):
        change_dates_df = pd.DataFrame(
            data={
                'change_date': ['2020-02-05', '2020-02-10', '2020-02-15', '2020-02-20', '2020-02-25', '2020-03-01'],
                'county_name': ['co', 'co', 'co', 'co', 'co', 'co'],
                'county_version': ['uts_co_S1', 'uts_co_S1', 'uts_co_S1', 'uts_co_S2', 'uts_co_S3', 'uts_co_S4'],
                'district_number': ['n/a', '1', '2', '2', '3', '4'],
                'district_version': ['n/a', 'co_D1', 'co_D2', 'co_D2', 'co_D3', 'co_D4'],
                'change_end_date': ['2020-02-09', '2020-02-14', '2020-02-19', '2020-02-24', '2020-02-29', None],
            }
        )
        change_dates_df['change_date'] = pd.to_datetime(change_dates_df['change_date'])
        change_dates_df['change_end_date'] = pd.to_datetime(change_dates_df['change_end_date'])

        return change_dates_df

    def test_join_shapes_and_districts_basic_check(self, mocker, change_dates_df, shape_data, district_data):

        county_mock = mocker.Mock(spec=models.County)
        county_mock.change_dates_df = change_dates_df
        county_mock.shape_df = shape_data
        county_mock.district_df = district_data

        models.County.join_shapes_and_districts(county_mock)

        assert county_mock.joined_df.loc[1, :].values.tolist() == [
            #: change_dates_df
            np.datetime64('2020-02-10'),
            'co',
            'uts_co_S1',
            '1',
            'co_D1',
            np.datetime64('2020-02-14'),
            #: shape_df
            'uts_co_S1',
            np.datetime64('2020-02-05'),
            np.datetime64('2020-02-19'),
            #: district_df
            '1',
            'co_D1',
            np.datetime64('2020-02-10'),
            np.datetime64('2020-02-14'),
        ]

    def test_join_shapes_and_districts_no_district(self, mocker, change_dates_df, shape_data, district_data):

        county_mock = mocker.Mock(spec=models.County)
        county_mock.change_dates_df = change_dates_df
        county_mock.shape_df = shape_data
        county_mock.district_df = district_data

        models.County.join_shapes_and_districts(county_mock)

        assert models.nulls_to_nones(county_mock.joined_df.loc[0, :].values.tolist()) == [
            #: change_dates_df
            np.datetime64('2020-02-05'),
            'co',
            'uts_co_S1',
            'n/a',
            'n/a',
            np.datetime64('2020-02-09'),
            #: shape_df
            'uts_co_S1',
            np.datetime64('2020-02-05'),
            np.datetime64('2020-02-19'),
            #: district_df should be all Nones thanks to nulls_to_nones()
            None,
            None,
            None,
            None,
        ]

    def test_join_shapes_and_districts_no_shape(self, mocker):

        county_mock = mocker.Mock(spec=models.County)

        #: Set up shape data
        county_mock.shape_df = pd.DataFrame(
            data={
                'shape_key': ['uts_co_S1', 'uts_co_S2'],
                'START_DATE': ['2020-02-05', '2020-02-20'],
                'END_DATE': ['2020-02-19', '2020-02-24'],
            },
        )
        county_mock.shape_df['END_DATE'] = pd.to_datetime(county_mock.shape_df['END_DATE'])
        county_mock.shape_df['START_DATE'] = pd.to_datetime(county_mock.shape_df['START_DATE'])
        county_mock.shape_df.set_index('START_DATE', drop=False, inplace=True)

        #: Set up district data
        county_mock.district_df = pd.DataFrame(
            data={
                'NewDistrict': ['1', '2', '3'],
                'district_key': ['co_D1', 'co_D2', 'co_D3'],
                'StartDate': ['2020-02-01', '2020-02-05', '2020-02-20'],
                'EndDate': ['2020-02-04', '2020-02-19', None],
            },
        )
        county_mock.district_df['StartDate'] = pd.to_datetime(county_mock.district_df['StartDate'])
        county_mock.district_df['EndDate'] = pd.to_datetime(county_mock.district_df['EndDate'])
        county_mock.district_df.set_index('StartDate', drop=False, inplace=True)

        #: Set up change dates data
        county_mock.change_dates_df = pd.DataFrame(
            data={
                'change_date': ['2020-02-01', '2020-02-05', '2020-02-20'],
                'county_name': ['co', 'co', 'co'],
                'county_version': ['n/a', 'uts_co_S1', 'uts_co_S2'],
                'district_number': ['1', '2', '3'],
                'district_version': ['co_D1', 'co_D2', 'co_D3'],
                'change_end_date': ['2020-02-04', '2020-02-19', None],
            }
        )
        county_mock.change_dates_df['change_date'] = pd.to_datetime(county_mock.change_dates_df['change_date'])
        county_mock.change_dates_df['change_end_date'] = pd.to_datetime(county_mock.change_dates_df['change_end_date'])

        models.County.join_shapes_and_districts(county_mock)

        assert models.nulls_to_nones(county_mock.joined_df.loc[0, :].values.tolist()) == [
            #: change_dates_df
            np.datetime64('2020-02-01'),
            'co',
            'n/a',
            '1',
            'co_D1',
            np.datetime64('2020-02-04'),
            #: shape_df should be all Nones thanks to nulls_to_nones()
            None,
            None,
            None,
            #: district_df
            '1',
            'co_D1',
            np.datetime64('2020-02-01'),
            np.datetime64('2020-02-04'),
        ]


class TestDistricts:

    @pytest.fixture
    def joined_df(self):
        joined_df = pd.DataFrame(
            data={
                'COUNTY_KEY': ['foo', 'foo', 'foo', 'bar', 'bar', 'bar'],
                'DST_NUMBER': ['1', '1', '2', '1', '2', '3'],
                'CHANGE_DATE': ['date1', 'date2', 'date3', 'date4', 'date5', 'date6'],
            }
        )

        return joined_df

    def test_setup_gets_just_the_districts_data(self, mocker, joined_df):
        district_mock = mocker.Mock(speck=models.District)
        models.District.__init__(district_mock, '1', joined_df)

        assert district_mock.district_records['DST_NUMBER'].unique().tolist() == ['1']
        assert district_mock.district_records['COUNTY_KEY'].unique().tolist() == ['foo', 'bar']
        assert district_mock.district_records['CHANGE_DATE'].unique().tolist() == ['date1', 'date2', 'date4']

    def test_build_versions_dataframes(self, mocker):
        district_mock = mocker.Mock()
        district_mock.label = '1'
        district_mock.row_key_and_versions = {
            's1_d1': [
                np.datetime64('2020-01-01'),
                np.datetime64('2021-01-01'),
            ],
            's1_d2': [
                np.datetime64('2022-01-01'),
                np.datetime64('2023-01-01'),
            ],
        }

        models.District.build_versions_dataframe(district_mock)
        assert district_mock.versions_df['UNIQUE_ROW_KEY'].tolist() == ['s1_d1', 's1_d1', 's1_d2', 's1_d2']
        assert district_mock.versions_df['DST_VERSION_KEY'].tolist() == [
            '1_2020-01-01',
            '1_2021-01-01',
            '1_2022-01-01',
            '1_2023-01-01',
        ]

    def test_join_version_information_record_occurs_twice(self, mocker):

        district_mock = mocker.Mock()
        district_mock.deduped_versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': ['s1_d1', 's2_d1', 's1_d1'],
                'DST_KEY': ['1_2020-01-01', '1_2020-01-01', '1_2021-01-01']
            }
        )
        district_mock.district_records = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': ['s1_d1', 's2_d1'],
                'geometry': ['geometry1', 'geometry2']
            }
        )

        models.District.join_version_information(district_mock)

        assert district_mock.versions_full_info_df['UNIQUE_ROW_KEY'].tolist() == ['s1_d1', 's2_d1', 's1_d1']
        assert district_mock.versions_full_info_df['DST_KEY'].tolist() == [
            '1_2020-01-01', '1_2020-01-01', '1_2021-01-01'
        ]
        assert district_mock.versions_full_info_df['geometry'].tolist() == ['geometry1', 'geometry2', 'geometry1']

    def test_join_version_information_extra_geometries_ignored(self, mocker):

        district_mock = mocker.Mock()
        district_mock.deduped_versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': ['s1_d1', 's2_d1', 's1_d1'],
                'DST_KEY': ['1_2020-01-01', '1_2020-01-01', '1_2021-01-01']
            }
        )
        district_mock.district_records = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': ['s1_d1', 's2_d1', 's5_d6'],
                'geometry': ['geometry1', 'geometry2', 'geometry5']
            }
        )

        models.District.join_version_information(district_mock)

        assert district_mock.versions_full_info_df['UNIQUE_ROW_KEY'].tolist() == ['s1_d1', 's2_d1', 's1_d1']
        assert district_mock.versions_full_info_df['DST_KEY'].tolist() == [
            '1_2020-01-01', '1_2020-01-01', '1_2021-01-01'
        ]
        assert district_mock.versions_full_info_df['geometry'].tolist() == ['geometry1', 'geometry2', 'geometry1']

    def test_removes_county_that_changes_after_last_district_change_date(self, mocker):
        test_state_df = pd.DataFrame(
            data={
                'CHANGE_DATE': ['2020-01-01', '2020-01-01', '2030-01-01'],
                'CHANGE_END_DATE': ['2039-12-31', '2029-12-31', '2039-12-31'],
                'DST_NUMBER': ['1', '1', '42'],
                'SHP_KEY': ['shape1', 'shape2', 'shape2'],
                'DST_KEY': ['dst1', 'dst1', 'dst42'],
            }
        )
        test_state_df['CHANGE_DATE'] = pd.to_datetime(test_state_df['CHANGE_DATE'])
        test_state_df['CHANGE_END_DATE'] = pd.to_datetime(test_state_df['CHANGE_END_DATE'])

        test_district = models.District('1', test_state_df)
        test_district.find_records_versions()
        assert test_district.row_key_and_versions == {
            'shape1__dst1': [np.datetime64('2020-01-01'), np.datetime64('2030-01-01')],
            'shape2__dst1': [np.datetime64('2020-01-01')],
        }

    def test_remove_duplicate_version_rows_one_changes_at_end(self, mocker):
        versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': [
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co2_s1__d1',
                    'co2_s1__d2',
                    'co2_s1__d2',
                ],
                'DST_VERSION_KEY': [
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2040-01-01',
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2040-01-01',
                ],
                'DST_VERSION_DATE': [
                    '2020-01-01',
                    '2030-01-01',
                    '2040-01-01',
                    '2020-01-01',
                    '2030-01-01',
                    '2040-01-01',
                ],
            }
        )
        versions_df['DST_VERSION_DATE'] = pd.to_datetime(versions_df['DST_VERSION_DATE'])

        district_mock = mocker.Mock()
        district_mock.versions_df = versions_df

        models.District.remove_duplicate_version_rows(district_mock)

        assert district_mock.deduped_versions_df['UNIQUE_ROW_KEY'].tolist() == [
            'co1_s1__d1',
            'co1_s1__d1',
            'co2_s1__d1',
            'co2_s1__d2',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_KEY'].tolist() == [
            'foo_2020-01-01',
            'foo_2030-01-01',
            'foo_2020-01-01',
            'foo_2030-01-01',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_DATE'].tolist() == [
            np.datetime64('2020-01-01'),
            np.datetime64('2030-01-01'),
            np.datetime64('2020-01-01'),
            np.datetime64('2030-01-01'),
        ]

    def test_remove_duplicate_version_rows_new_one_after_multiple_change_dates(self, mocker):
        versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': [
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co2_s1__d1',
                ],
                'DST_VERSION_KEY': [
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2040-01-01',
                    'foo_2040-01-01',
                ],
                'DST_VERSION_DATE': [
                    '2020-01-01',
                    '2030-01-01',
                    '2040-01-01',
                    '2040-01-01',
                ],
            }
        )
        versions_df['DST_VERSION_DATE'] = pd.to_datetime(versions_df['DST_VERSION_DATE'])

        district_mock = mocker.Mock()
        district_mock.versions_df = versions_df

        models.District.remove_duplicate_version_rows(district_mock)

        assert district_mock.deduped_versions_df['UNIQUE_ROW_KEY'].tolist() == [
            'co1_s1__d1',
            'co1_s1__d1',
            'co2_s1__d1',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_KEY'].tolist() == [
            'foo_2020-01-01',
            'foo_2040-01-01',
            'foo_2040-01-01',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_DATE'].tolist() == [
            np.datetime64('2020-01-01'),
            np.datetime64('2040-01-01'),
            np.datetime64('2040-01-01'),
        ]

        #: TODO: more test cases for deduplication, then implement dedup according to method in notebook
    def test_remove_duplicate_version_rows_many_of_same(self, mocker):
        versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': [
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co1_s1__d1',
                ],
                'DST_VERSION_KEY': [
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2040-01-01',
                ],
                'DST_VERSION_DATE': [
                    np.datetime64('2020-01-01'),
                    np.datetime64('2030-01-01'),
                    np.datetime64('2040-01-01'),
                ],
            }
        )
        versions_df['DST_VERSION_DATE'] = pd.to_datetime(versions_df['DST_VERSION_DATE'])

        district_mock = mocker.Mock()
        district_mock.versions_df = versions_df

        models.District.remove_duplicate_version_rows(district_mock)

        assert district_mock.deduped_versions_df['UNIQUE_ROW_KEY'].tolist() == [
            'co1_s1__d1',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_KEY'].tolist() == [
            'foo_2020-01-01',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_DATE'].tolist() == [
            np.datetime64('2020-01-01'),
        ]

    def test_remove_duplicate_version_rows_first_one_ends(self, mocker):
        versions_df = pd.DataFrame(
            data={
                'UNIQUE_ROW_KEY': [
                    'co1_s1__d1',
                    'co1_s1__d1',
                    'co2_s1__d1',
                    'co2_s1__d2',
                    'co2_s1__d2',
                ],
                'DST_VERSION_KEY': [
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2020-01-01',
                    'foo_2030-01-01',
                    'foo_2040-01-01',
                ],
                'DST_VERSION_DATE': [
                    '2020-01-01',
                    '2030-01-01',
                    '2020-01-01',
                    '2030-01-01',
                    '2040-01-01',
                ],
            }
        )
        versions_df['DST_VERSION_DATE'] = pd.to_datetime(versions_df['DST_VERSION_DATE'])

        district_mock = mocker.Mock()
        district_mock.versions_df = versions_df

        models.District.remove_duplicate_version_rows(district_mock)

        assert district_mock.deduped_versions_df['UNIQUE_ROW_KEY'].tolist() == [
            'co1_s1__d1',
            'co1_s1__d1',
            'co2_s1__d1',
            'co2_s1__d2',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_KEY'].tolist() == [
            'foo_2020-01-01',
            'foo_2030-01-01',
            'foo_2020-01-01',
            'foo_2030-01-01',
        ]
        assert district_mock.deduped_versions_df['DST_VERSION_DATE'].tolist() == [
            np.datetime64('2020-01-01'),
            np.datetime64('2030-01-01'),
            np.datetime64('2020-01-01'),
            np.datetime64('2030-01-01'),
        ]


class test_get_unique_district_versions():

    @pytest.fixture
    def unique_dates(self):
        return [np.datetime64('2020-01-01'), np.datetime64('2021-01-01'), np.datetime64('2022-01-01')]

    def test_get_unique_district_versions_assigns_to_one(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2020-01-01')
        end_date = np.datetime64('2020-12-31')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2020-01-01')]

    def test_get_unique_district_versions_assigns_to_two(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2020-01-01')
        end_date = np.datetime64('2021-12-31')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2020-01-01'), np.datetime64('2021-01-01')]

    def test_get_unique_district_versions_assigns_to_all_with_no_ending_date(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2020-01-01')
        end_date = np.datetime64('nat')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2020-01-01'), np.datetime64('2021-01-01'), np.datetime64('2022-01-01')]

    def test_get_unique_district_versions_assigns_to_all_with_later_ending_date(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2020-01-01')
        end_date = np.datetime64('2024-01-01')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2020-01-01'), np.datetime64('2021-01-01'), np.datetime64('2022-01-01')]

    def test_get_unique_district_versions_assigns_to_last_two_with_no_ending_date(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2021-01-01')
        end_date = np.datetime64('nat')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2021-01-01'), np.datetime64('2022-01-01')]

    def test_get_unique_district_versions_assigns_to_last_two_with_later_ending_date(self, unique_dates, mocker):
        district_mock = mocker.Mock()
        start_date = np.datetime64('2021-01-01')
        end_date = np.datetime64('2024-01-01')

        versions = models.District._get_unique_district_versions(district_mock, unique_dates, start_date, end_date)

        assert versions == [np.datetime64('2021-01-01'), np.datetime64('2022-01-01')]

    # def test_assign_versions_comprehension(self, mocker, joined_df):
    #     district_mock = mocker.Mock()

    #     district_mock._get_version.return_value = 'assigned'

    #     #: Need to run setup through __init__ to make sure the index is reset the same as IRL, as having an index
    #     #: that does not match the new series index from assign_versions will cause problems.
    #     models.District.__init__(district_mock, '1', joined_df)
    #     models.District.assign_versions(district_mock)

    #     assert district_mock.district_records['district_version'].tolist() == ['assigned', 'assigned', 'assigned']

    # def test_assign_versions_create_district_version_key(self, mocker, joined_df):
    #     district_mock = mocker.Mock()

    #     district_mock._get_version.return_value = 1

    #     #: Need to run setup through __init__ to make sure the index is reset the same as IRL, as having an index
    #     #: that does not match the new series index from assign_versions will cause problems.
    #     models.District.__init__(district_mock, '1', joined_df)
    #     models.District.assign_versions(district_mock)

    #     assert district_mock.district_records['district_version_key'].tolist() == ['D1_V01', 'D1_V01', 'D1_V01']
