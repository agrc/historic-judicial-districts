from collections import namedtuple
from pathlib import Path

import arcpy
import pandas as pd


def create_county_key(name):
    """Creates a properly-formatted county key from name. May rename to match current county names.

    Args:
        name (str): Name from either the boundaries shapefile's ID field or the district's name field

    Returns:
        str: name stripped from any prepended 'xyz_', whitespace, and periods.
    """

    cleaned_name = name.split('_')[-1].casefold().replace(' ', '').replace('.', '')

    if cleaned_name == 'richland':
        cleaned_name = 'rich'

    return cleaned_name


def nulls_to_nones(row):
    """Replace any pandas null values in a list with None

    Args:
        row (List): Row of data as a list of arbitrary objects

    Returns:
        List: List of data appropriately cleaned.
    """

    new_row = []
    for item in row:
        if pd.isnull(item):
            new_row.append(None)
        else:
            new_row.append(item)
    return new_row


class ChangeDate:
    """Holds information about unique dates when either shape or district change

    Attributes:
        date (datetime): The start date for a new shape or district version
        county_name (str): Name of the county, cleaned.
        county_version (str): County join key, 'uts_<name>_S<version>'
        district_number (str): District number (includes '1S' and '1N')
        district_version (str): District join key, '<name>_D<version>'
    """

    def __init__(self, date):
        self.date = date
        self.county_name = 'n/a'
        self.county_version = 'n/a'
        self.district_number = 'n/a'
        self.district_version = 'n/a'

    def __repr__(self):
        return ', '.join([
            str(self.date), self.county_name, self.county_version,
            str(self.district_number), self.district_version
        ])


class State:
    """Contains statewide data and methods to operate over all counties.

    Attributes:
        counties_df (pd.DataFrame): Dataframe of the historic boundaries
            shapefile.
        districts_df (pd.DataFrame): Counties and their assigned districts
            over time.
        counties (List[County]): Objects for each unique county in
            districts_df.
        combined_change_df (pd.DataFrame): Change dates from all the
            different counties.
        output_df (pd.DataFrame): Final data with geometries and other info
            from counties_df/districts_df merged into change dates.
    """

    def __init__(self):
        self.all_shapes_df = None
        self.all_districts_df = None
        self.counties = []
        self.combined_change_df = None
        self.output_df = None
        self.districts = []

    def load_counties(self, counties_shp):
        """Read historical boundaries shapefile into counties_df

        Calculates a key based on ID and VERSION fields.

        Args:
            counties_shp (str): Path to the historical boundaries shapefile
        """

        #: Read counties shapefile in as dict, transform dict to dataframe
        print(f'Loading counties from {counties_shp}...')
        counties_list = []
        county_fields = [f.name for f in arcpy.ListFields(counties_shp)]
        county_fields.append('SHAPE@')  #: Get the geometry so we can create a new feature class
        with arcpy.da.SearchCursor(counties_shp, county_fields) as search_cursor:
            for row in search_cursor:
                counties_list.append(dict(zip(county_fields, row)))
        self.all_shapes_df = pd.DataFrame(counties_list)

        #: Create shape key- name_Sx
        self.all_shapes_df['shape_key'] = self.all_shapes_df['ID'] + '_S' + self.all_shapes_df['VERSION'].astype(str)

        #: Create county key
        self.all_shapes_df['county_key'] = self.all_shapes_df['ID'].apply(create_county_key)

    def load_districts(self, districts_csv):
        """Read historical district info into districts_df.

        Cleans name with clean_name(), parses dates, and calculates district
        key from CountyName and Version fields.

        Args:
            districts_csv (str): Path to the historical districts data
        """

        print(f'Loading districts from {districts_csv}...')
        self.all_districts_df = pd.read_csv(districts_csv)

        #: Create ID column to better match the county shapefile id
        self.all_districts_df['county_key'] = self.all_districts_df['CountyName'].apply(create_county_key)

        #: Clean up dates
        self.all_districts_df['StartDate'] = pd.to_datetime(self.all_districts_df['StartDate'])
        self.all_districts_df['EndDate'] = pd.to_datetime(self.all_districts_df['EndDate'])

        #: Create district key- name_Dx
        self.all_districts_df['district_key'] = (
            self.all_districts_df['CountyName'].str.casefold() + '_D' + self.all_districts_df['Version'].astype(str)
        )

    def setup_counties(self):
        """Get a list of counties from districts_df and load them in as County objects.
        """

        county_names = self.all_districts_df['county_key'].unique()
        for name in county_names:
            print(f'Setting up {name}...')
            county = County(name)
            county.setup(self.all_shapes_df, self.all_districts_df)
            self.counties.append(county)

    def verify_counties(self):
        """Run verification code against shapes and districts
        """

        for county in self.counties:
            print(f'\n--- {county.name} ---')
            county.verify_county_districts()
            county.verify_county_shapes()

    def calc_counties(self):
        """Calculate unique change dates for each county
        """

        for county in self.counties:
            county.calc_change_dates()

    def combine_change_dfs(self, out_path=None):
        """Combine all individual county change dates into one dataframe.

        Args:
            out_path (str, optional): Path to save master change dates
                dataframe as csv if desired.
        """
        self.combined_change_df = pd.DataFrame()
        for county in self.counties:
            self.combined_change_df = self.combined_change_df.append(county.change_dates_df)
        if out_path:
            self.combined_change_df.to_csv(out_path)

    def get_shape_district_info(self):
        """Get shape/district info for each change date for each county
        """

        print('mergeing shape/district info into change dates...')
        self.output_df = pd.DataFrame()
        for county in self.counties:
            county.join_shapes_and_districts()
            self.output_df = self.output_df.append(county.joined_df)

    def output_to_featureclass(self, out_path, template_shp):
        """Write final data in output_df out to specified feature class.

        Manually sets the output fields and then copies/renames the dataframe
        columns to match these field names.

        Args:
            out_path (str): Path to a feature class (can not exist already)
            template_shp (str): Path to the historical boundaries shapefile
                for projection info.
        """

        print(f'Creating output {out_path}...')
        out_gdb = str(Path(out_path).parent)
        out_name = str(Path(out_path).name)
        template_prj = str(Path(template_shp).with_suffix('.prj'))
        arcpy.management.CreateFeatureclass(out_gdb, out_name, 'POLYGON', spatial_reference=template_prj)

        new_fields = [
            ['CHANGE_DATE', 'DATE'],  #: change_df date
            ['COUNTY_KEY', 'TEXT'],  #: change_df county_name
            ['SHP_NAME', 'TEXT'],  #: shape_df NAME
            ['SHP_ID', 'TEXT'],  #: shape_df ID
            ['SHP_FIPS', 'TEXT'],  #: shape_df FIPS
            ['SHP_VERSION', 'TEXT'],  #: shape_df VERSION
            ['DST_NAME', 'TEXT'],  #: district_df CountyName
            ['DST_NUMBER', 'TEXT'],  #: district_df district
            ['SHP_START_DATE', 'DATE'],  #: shape_df START_DATE
            ['SHP_END_DATE', 'DATE'],  #: shape_df END_DATE
            ['DST_START_DATE', 'DATE'],  #: district_df date
            ['DST_END_DATE', 'DATE'],  #: district_df end_date
            ['SHP_CHANGE', 'TEXT'],  #: shape_df CHANGE
            ['SHP_CITATION', 'TEXT'],  #: shape_df CITATION
            ['SHP_AREA_SQMI', 'LONG'],  #: shape_df AREA_SQMI
            ['SHP_KEY', 'TEXT'],  #: shape_df shape_key
            ['DST_KEY', 'TEXT'],  #: district_df district_key
        ]

        df_renamer = {
            'NAME': 'SHP_NAME',
            'ID': 'SHP_ID',
            'FIPS': 'SHP_FIPS',
            'VERSION': 'SHP_VERSION',
            'START_DATE': 'SHP_START_DATE',
            'END_DATE': 'SHP_END_DATE',
            'CHANGE': 'SHP_CHANGE',
            'CITATION': 'SHP_CITATION',
            'AREA_SQMI': 'SHP_AREA_SQMI',
            'StartDate': 'DST_START_DATE',
            'EndDate': 'DST_END_DATE',
            'district_number': 'DST_NUMBER',
            'shape_key': 'SHP_KEY',
            'district_key': 'DST_KEY',
            'SHAPE@': 'SHAPE@',
            'date': 'CHANGE_DATE',
            'county_name': 'COUNTY_KEY',
            'CountyName': 'DST_NAME',
        }

        arcpy.management.AddFields(out_path, new_fields)

        print(f'Writing out to {out_path}...')

        #: Rename the data frame columns to match the output fields
        renamed_df = self.output_df.rename(columns=df_renamer)
        cursor_fields = df_renamer.values()  #: Only look at the renamed columns
        with arcpy.da.InsertCursor(out_path, list(cursor_fields)) as insert_cursor:
            for row in renamed_df[cursor_fields].values.tolist():
                insert_cursor.insertRow(nulls_to_nones(row))

    def setup_districts(self):

        print('Setting up districts...')
        district_numbers = self.output_df['district_number'].unique()
        for number in district_numbers:
            district = District(number, self.output_df)
            self.districts.append(district)


class County:
    """Data and processing for a specific county within the total dataset.

    Attributes:
        name (str): County's name from districts_df, lowercased and spaces/periods removed
        shape_df (pd.DataFrame): Information from the shapefile about
            the different historical geomtries involved.
        district_df (pd.DataFrame): Information about the different
            district designations over time.
        change_dates_df (pd.DataFrame): Information about each unique date
            when either a shape or district changes (or both).
        joined_df (pd.DataFrame): change_dates_df with shape_df and
            district_df joined back in for each row.
    """

    def __init__(self, name):
        self.name = name
        self.shape_df = None
        self.district_df = None
        self.change_dates_df = None
        self.joined_df = None

    def setup(self, counties_df, districts_df):
        """Copy out and format the dataframe entries specific to this county

        Args:
            counties_df (pd.DataFrame): Main counties geometry dataframe
            districts_df (pd.DataFrame): Main counties districts dataframe
        """

        #: create a local shape dataframe of just the county, change the index to the start date of each version
        self.shape_df = counties_df[counties_df['county_key'].str.contains(self.name)].copy()  #: avoid chained indexing
        self.shape_df.set_index('START_DATE', inplace=True)
        self.shape_df['START_DATE'] = self.shape_df.index  #: re-add start date for output data
        self.shape_df.sort_index(inplace=True)

        #: create a local district dataframe of just the county, change the index to the start date of each version
        self.district_df = districts_df[districts_df['county_key'].str.contains(self.name)].copy()
        self.district_df.set_index('StartDate', inplace=True)
        self.district_df['StartDate'] = self.district_df.index  #: re-add start date for output data
        self.district_df.sort_index(inplace=True)

    def calc_change_dates(self):
        """Create a data structure of all the dates when either a geometry or district changes

        For each change, note the current county version, district number, and district version by checking against
        their start and end dates.
        """

        #: Get a list of ChangeDate objects for all the dates for this county
        dates = list(pd.Series(self.shape_df.index.union(self.district_df.index)))
        change_dates = [ChangeDate(date) for date in dates]

        for change_date in change_dates:
            change_date.county_name = self.name  #: county_key

            #: Get the county key for this date
            shape_df_rows = [row for row in self.shape_df.itertuples()]
            for shape_row in shape_df_rows:
                if change_date.date >= shape_row.START_DATE and change_date.date <= shape_row.END_DATE:
                    change_date.county_version = shape_row.shape_key
                    break

            #: Get the district key for this date
            district_df_rows = [row for row in self.district_df.itertuples()]
            first_district_date = district_df_rows[0].StartDate

            for district_row in district_df_rows:
                #: Get the earliest start date
                if district_row.StartDate < first_district_date:
                    first_district_date = district_row.StartDate

                if change_date.date >= district_row.StartDate and change_date.date <= district_row.EndDate:
                    change_date.district_number = district_row.NewDistrict
                    change_date.district_version = district_row.district_key
                    break
                #: If we've gotten to the end of the district rows without breaking, and it doesn't have an end date,
                #and it's after the first date district date, assume that it is the final district and should be added
                if (
                    district_row == district_df_rows[-1] and pd.isnull(district_row.EndDate) and
                    change_date.date > first_district_date
                ):
                    change_date.district_number = district_row.NewDistrict
                    change_date.district_version = district_row.district_key
                    break

                #: Richland scenario: a renamed county in both shapes and districts, and the original
                #: name's district entry doesn't have an end date
                #: This should come after the final row check to be sure it doesn't pick up the final district
                #: that shouldn't have an end date.
                if change_date.date >= district_row.StartDate and pd.isnull(district_row.EndDate):
                    change_date.district_number = district_row.NewDistrict
                    change_date.district_version = district_row.district_key

        #: Now we can use a namedtuple to translate our object to dataframe rows
        #: (Didn't use one at first because we had to alter the list of ChangeDate items in the iterations)
        ChangeDatesTuple = namedtuple(
            'ChangeDatesTuple', 'date county_name county_version district_number district_version'
        )
        new_dates = [
            ChangeDatesTuple(cd.date, cd.county_name, cd.county_version, cd.district_number, cd.district_version)
            for cd in change_dates
        ]
        self.change_dates_df = pd.DataFrame(new_dates)

        #: End date is one day before the next rows start date
        self.change_dates_df['change_end_date'] = self.change_dates_df['date'].shift(-1) - pd.Timedelta(days=1)

    def join_shapes_and_districts(self):
        """Join shape and district info based on shape/district_keys

        Joins the shape and district dataframes to the change date data to add geometries and other relevant info for
        each change date.
        """

        first_join = pd.merge(
            self.change_dates_df,
            self.shape_df,
            how='left',
            left_on='county_version',
            right_on='shape_key',
            validate='m:1'
        )
        self.joined_df = pd.merge(
            first_join,
            self.district_df,
            how='left',
            left_on='district_version',
            right_on='district_key',
            validate='m:1'
        )

    def verify_county_districts(self):
        """Verify the districts for this county.

        For each row, make sure a) no gaps between StartDate (index) and previous row's EndDate and
        b) row's OldDistrict is previous row's NewDistrict
        """

        sorted_district_df = self.district_df.sort_index()
        sorted_district_df['StartDate'] = sorted_district_df.index

        sorted_district_df['DistrictMatch'] = sorted_district_df['OldDistrict'].eq(
            sorted_district_df['NewDistrict'].shift()
        )

        sorted_district_df['DateMatch'] = sorted_district_df['StartDate'].eq(
            sorted_district_df['EndDate'].shift() + pd.Timedelta(days=1)
        )

        print(sorted_district_df)

    def verify_county_shapes(self):
        """Verify the shapes for this county.

        For each row, make sure there are no gaps between START_DATE (index) and previous row's END_DATE.
        """

        sorted_shape_df = self.shape_df.sort_index()
        sorted_shape_df['StartDate'] = sorted_shape_df.index

        sorted_shape_df['DateMatch'] = sorted_shape_df['StartDate'].eq(
            sorted_shape_df['END_DATE'].shift() + pd.Timedelta(days=1)
        )

        print(sorted_shape_df.loc[:, ['END_DATE', 'ID', 'VERSION', 'DateMatch']])


class District:

    def __init__(self, label, joined_df):
        self.label = label
        self.district_records = joined_df[joined_df['district_number'] == self.label].copy()
        #: Need to reset index, otherwise the series assignment in assign_versions may assign to an index
        #: that doesn't exist in the dataframe
        self.district_records.reset_index(inplace=True)
        #: Pre-populate our version dict with the max possible versions, indexed at 1 instead of 0
        max_occurrences = self.district_records.groupby('county_name')['county_name'].count().max()
        self.versions = {}
        for i in range(1, max_occurrences + 1):
            self.versions[i] = []

    def assign_versions(self):
        #: Assign each row in district_records a version number
        #:  If the county doesn't exist in latest version, assign to that version
        #:  If it does, increment version and assign
        self.district_records['district_version'] = pd.Series([
            self._get_version(name) for name in self.district_records['county_name']
        ])

    def _get_version(self, name):
        for version_number in self.versions:
            if name not in self.versions[version_number]:
                self.versions[version_number].append(name)
                return version_number
