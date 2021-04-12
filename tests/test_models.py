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

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[0, test_columns].values.tolist() == [
            np.datetime64('2020-02-05'), 'co', 'uts_co_S1', 'n/a', 'n/a'
        ]

    def test_change_dates_new_district_existing_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[1, test_columns].values.tolist() == [
            np.datetime64('2020-02-10'), 'co', 'uts_co_S1', '1', 'co_D1'
        ]

    def test_change_dates_change_district_same_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[2, test_columns].values.tolist() == [
            np.datetime64('2020-02-15'), 'co', 'uts_co_S1', '2', 'co_D2'
        ]

    def test_change_dates_same_district_change_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[3, test_columns].values.tolist() == [
            np.datetime64('2020-02-20'), 'co', 'uts_co_S2', '2', 'co_D2'
        ]

    def test_change_dates_change_district_change_shape(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[4, test_columns].values.tolist() == [
            np.datetime64('2020-02-25'), 'co', 'uts_co_S3', '3', 'co_D3'
        ]

    def test_change_dates_change_district_change_shape_no_district_end_date(self, mocker, shape_data, district_data):
        county = mocker.Mock()
        county.name = 'co'
        county.shape_df = shape_data
        county.district_df = district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

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

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[0, test_columns].values.tolist() == [
            np.datetime64('2020-02-01'), 'rich', 'uts_richland_S1', 'n/a', 'n/a'
        ]

    def test_change_dates_richland_shape_richland_district(self, mocker, richland_shape_data, richland_district_data):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[1, test_columns].values.tolist() == [
            np.datetime64('2020-02-05'), 'rich', 'uts_richland_S1', '1', 'richland_D1'
        ]

    def test_change_dates_rich_shape_rich_district(self, mocker, richland_shape_data, richland_district_data):

        county = mocker.Mock()
        county.name = 'rich'
        county.shape_df = richland_shape_data
        county.district_df = richland_district_data

        models.County.calc_change_dates(county)

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

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

        test_columns = ['date', 'county_name', 'county_version', 'district_number', 'district_version']

        assert county.change_dates_df.loc[4, test_columns].values.tolist() == [
            np.datetime64('2020-02-20'), 'rich', 'uts_rich_S2', '2', 'rich_D2'
        ]


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
                'date': ['2020-02-05', '2020-02-10', '2020-02-15', '2020-02-20', '2020-02-25', '2020-03-01'],
                'county_name': ['co', 'co', 'co', 'co', 'co', 'co'],
                'county_version': ['uts_co_S1', 'uts_co_S1', 'uts_co_S1', 'uts_co_S2', 'uts_co_S3', 'uts_co_S4'],
                'district_number': ['n/a', '1', '2', '2', '3', '4'],
                'district_version': ['n/a', 'co_D1', 'co_D2', 'co_D2', 'co_D3', 'co_D4'],
                'change_end_date': ['2020-02-09', '2020-02-14', '2020-02-19', '2020-02-24', '2020-02-29', None],
            }
        )
        change_dates_df['date'] = pd.to_datetime(change_dates_df['date'])
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
                'date': ['2020-02-01', '2020-02-05', '2020-02-20'],
                'county_name': ['co', 'co', 'co'],
                'county_version': ['n/a', 'uts_co_S1', 'uts_co_S2'],
                'district_number': ['1', '2', '3'],
                'district_version': ['co_D1', 'co_D2', 'co_D3'],
                'change_end_date': ['2020-02-04', '2020-02-19', None],
            }
        )
        county_mock.change_dates_df['date'] = pd.to_datetime(county_mock.change_dates_df['date'])
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
