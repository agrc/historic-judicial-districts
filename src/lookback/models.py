from collections import namedtuple
from pathlib import Path
from typing import List

import arcpy
import numpy as np
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


def pairwise(iterable):
    """Yields an item and the item after it in an iterable

    Args:
        iterable (iterable): The collection to iterate over

    Yields:
        tuple: An item and the next item
    """

    it = iter(iterable)
    a = next(it, None)

    for b in it:
        yield (a, b)
        a = b


def _fix_change_end_dates(change_end_date, shape_key, shape_end, district_end):

    #: Change end date scenarios:
    #:  District exists before shape, shape then changes before district does (Duchesne/dagget)
    #:      change date should be when shape is created, not when district changes
    #:      captured properly in existing change end date is next change date - 1
    #:  Extinct counties: Last record should have a change end date that is max(shp end date, district end date)
    #:      not captured by change end date is next change date - 1 because there is no next date
    #:  Shape exists before district
    #:      captured properly in existing change end date is next change date - 1 because next date is usually
    #:          district creation date
    #:  Extant counties: Shape ends at 2003, district does not have an end date
    #:      captured properly in existing change end date is next change date - 1 because there isn't a next
    #:          so it gets NaT
    # self.change_dates_df['change_end_date'] = self.change_dates_df['change_date'].shift(-1) - pd.Timedelta(days=1)

    #: If it's an extinct county (utt in shape name) with a NaT end time, return the latest of the shape or district end
    #: utt_richland should pass because it's change_date shouldn't be null due to there being a row after for uts_rich
    if pd.isnull(change_end_date) and 'utt_' in shape_key:
        return max(shape_end, district_end)

    #: Otherwise, just return the original date
    return change_end_date


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
        self.counties: List[County] = []
        self.combined_change_df = None
        self.output_df = None
        self.districts: List[District] = []
        self.district_versions_dict = {}
        self.district_versions_df: pd.DataFrame

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
            county.add_extra_fields()
            self.output_df = self.output_df.append(county.joined_df)

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
            'change_date': 'CHANGE_DATE',
            'county_name': 'COUNTY_KEY',
            'CountyName': 'DST_NAME',
            'change_end_date': 'CHANGE_END_DATE',
        }

        self.output_df.rename(columns=df_renamer, inplace=True)

    def output_to_featureclass(self, out_path, epsg=26912):
        """Write final data in output_df out to specified feature class.

        Manually sets the output fields, which should match the dataframe columns as renamed previously.

        Args:
            out_path (str): Path to a feature class (can not exist already)
            epsg (int, optional): EPSG code for output project. Defualts to 26912 (UTM 12N NAD83)
        """

        print(f'Creating output {out_path}...')
        out_gdb = str(Path(out_path).parent)
        out_name = str(Path(out_path).name)
        # template_prj = str(Path(template_shp).with_suffix('.prj'))
        spatial_reference = arcpy.SpatialReference(epsg)
        arcpy.management.CreateFeatureclass(out_gdb, out_name, 'POLYGON', spatial_reference=spatial_reference)

        new_fields = [
            ['CHANGE_DATE', 'DATE'],  #: change_df date
            ['CHANGE_END_DATE', 'DATE'],  #: change_df change_end_date
            ['COUNTY_KEY', 'TEXT'],  #: change_df county_name
            ['COMBINED_DST_KEY', 'TEXT'],  #: DST_NUMBER + _ + CHANGE_DATE
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

        arcpy.management.AddFields(out_path, new_fields)

        print(f'Writing out to {out_path}...')

        #: Rename the data frame columns to match the output fields
        cursor_fields = [field_name[0] for field_name in new_fields]  #: Only look at the renamed columns
        cursor_fields.append('SHAPE@')  #: Make sure we've got geometry
        with arcpy.da.InsertCursor(out_path, list(cursor_fields)) as insert_cursor:
            for row in self.output_df[cursor_fields].values.tolist():
                insert_cursor.insertRow(nulls_to_nones(row))

    def setup_districts(self):
        """Create districts labeled by their number (used as a string)
        """

        print('Setting up districts...')
        district_numbers = self.output_df['DST_NUMBER'].unique()
        for number in district_numbers:
            district = District(number, self.output_df)
            self.districts.append(district)

    def calc_districts_versions(self):
        """Get the district version info for each record, build the data frame, and rejoin all other info
        """
        for district in self.districts:
            district.find_records_versions()
            district.build_versions_dataframe()
            district.join_version_information()
            district.remove_duplicate_version_rows()

    def combine_district_dicts(self, out_path=None, epsg=26912):
        """Merge all the district's dataframes into a single dataframe, pickle if desired

        Args:
            out_path (str, optional): Path to pickle combined dataframe to. Defaults to None.
        """

        self.district_versions_df = pd.DataFrame()
        for district in self.districts:
            self.district_versions_df = self.district_versions_df.append(district.deduped_versions_df)
        # self.district_versions_df.to_pickle(
        #     r'C:\gis\Projects\HistoricCounties\Data\JudicialDistricts\district_versions_with_dupes.pkl'
        # )
        if out_path:

            print(f'Writing district version parts out to {out_path}...')
            out_gdb = str(Path(out_path).parent)
            out_name = str(Path(out_path).name)
            spatial_reference = arcpy.SpatialReference(epsg)
            arcpy.management.CreateFeatureclass(out_gdb, out_name, 'POLYGON', spatial_reference=spatial_reference)

            new_fields = [
                ['DST_VERSION_KEY', 'TEXT'],
                ['UNIQUE_ROW_KEY', 'TEXT'],
                ['CHANGE_DATE_IN_DST', 'DATE'],
                ['CHANGE_DATE', 'DATE'],  #: change_df date
                ['CHANGE_END_DATE', 'DATE'],  #: change_df change_end_date
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

            arcpy.management.AddFields(out_path, new_fields)

            #: Rename the data frame columns to match the output fields
            cursor_fields = [field_name[0] for field_name in new_fields]  #: Only look at the renamed columns
            cursor_fields.append('SHAPE@')  #: Make sure we've got geometry
            with arcpy.da.InsertCursor(out_path, list(cursor_fields)) as insert_cursor:
                for row in self.district_versions_df[cursor_fields].values.tolist():
                    insert_cursor.insertRow(nulls_to_nones(row))

    def dissolve_districts(self, out_path, epsg=26912):
        """Dissolve the districts based on DST_VERSION_KEY to out_path.

        Args:
            out_path (str): Feature class to save dissolved districts
            epsg (int, optional): EPSG code for output projection. Defaults to 26912 (UTM 12N NAD83)
        """

        print(f'Dissolving districts to {out_path}...')

        spatial_reference = arcpy.SpatialReference(epsg)
        arcpy.management.CreateFeatureclass('memory', 'districts_fc', 'POLYGON', spatial_reference=spatial_reference)

        new_fields = [
            ['DST_VERSION_KEY', 'TEXT'],  #: key for the dissolve
            ['CHANGE_DATE_IN_DST', 'DATE'],
            ['DST_NUMBER', 'TEXT'],
        ]

        arcpy.management.AddFields(r'memory\districts_fc', new_fields)

        #: Rename the data frame columns to match the output fields
        cursor_fields = [field_name[0] for field_name in new_fields]  #: Only look at the renamed columns
        cursor_fields.append('SHAPE@')  #: Make sure we've got geometry
        with arcpy.da.InsertCursor(r'memory\districts_fc', list(cursor_fields)) as insert_cursor:
            for row in self.district_versions_df[cursor_fields].values.tolist():
                insert_cursor.insertRow(nulls_to_nones(row))

        arcpy.management.Dissolve(
            r'memory\districts_fc', out_path, ['DST_VERSION_KEY', 'CHANGE_DATE_IN_DST', 'DST_NUMBER']
        )

    def dissolve_districts_duplicates(self, out_path, epsg=26912):
        """Dissolve all the possible district pieces by DST_VERSION_KEY for full historical record.

        Args:
            out_path (str): Feature class to save dissolved districts
            epsg (int, optional): EPSG code for output projection. Defaults to 26912 (UTM 12N NAD83)
        """

        district_duplicates_versions_df = pd.DataFrame()
        for district in self.districts:
            district_duplicates_versions_df = district_duplicates_versions_df.append(district.versions_full_info_df)

        print(f'Dissolving districts to {out_path}...')

        spatial_reference = arcpy.SpatialReference(epsg)
        arcpy.management.CreateFeatureclass(
            'memory', 'districts_duplicates_fc', 'POLYGON', spatial_reference=spatial_reference
        )

        new_fields = [
            ['DST_VERSION_KEY', 'TEXT'],  #: key for the dissolve
            ['CHANGE_DATE_IN_DST', 'DATE'],
            ['DST_NUMBER', 'TEXT'],
        ]

        arcpy.management.AddFields(r'memory\districts_duplicates_fc', new_fields)

        #: Rename the data frame columns to match the output fields
        cursor_fields = [field_name[0] for field_name in new_fields]  #: Only look at the renamed columns
        cursor_fields.append('SHAPE@')  #: Make sure we've got geometry
        with arcpy.da.InsertCursor(r'memory\districts_duplicates_fc', list(cursor_fields)) as insert_cursor:
            for row in district_duplicates_versions_df[cursor_fields].values.tolist():
                insert_cursor.insertRow(nulls_to_nones(row))

        arcpy.management.Dissolve(
            r'memory\districts_duplicates_fc', out_path, ['DST_VERSION_KEY', 'CHANGE_DATE_IN_DST', 'DST_NUMBER']
        )


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
                #: and it's after the first date district date, assume that it is the final district and should be added
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
            'ChangeDatesTuple', 'change_date county_name county_version district_number district_version'
        )
        new_dates = [
            ChangeDatesTuple(cd.date, cd.county_name, cd.county_version, cd.district_number, cd.district_version)
            for cd in change_dates
        ]
        self.change_dates_df = pd.DataFrame(new_dates)

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

    def add_extra_fields(self):
        """Add combined district version key and a properly-calculated change end date to the data
        """

        #: Add DST_VERSION key to output for joining to dissolved districts
        self.joined_df['COMBINED_DST_KEY'] = [
            '_'.join([number, date.strftime('%Y-%m-%d')])
            for number, date in zip(self.joined_df['district_number'], self.joined_df['change_date'])
        ]

        #: End date is one day before the next rows start date
        self.joined_df['change_end_date'] = self.joined_df['change_date'].shift(-1) - pd.Timedelta(days=1)
        #: Fix the extinct counties' end dates
        #: END_DATE: shape end date, EndDate: district end date
        self.joined_df['change_end_date'] = [
            _fix_change_end_dates(change_end_date, shape_key, shape_end, district_end)
            for change_end_date, shape_key, shape_end, district_end in zip(
                self.joined_df['change_end_date'], self.joined_df['county_version'], self.joined_df['END_DATE'],
                self.joined_df['EndDate']
            )
        ]

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
    """Data and processing for merging all the different county/district recrods into single features based on their
    county number and change date.
    """

    def __init__(self, label, joined_df):
        self.label = label
        self.district_records: pd.DataFrame = joined_df[joined_df['DST_NUMBER'] == self.label].copy()
        self.unique_change_dates = list(joined_df['CHANGE_DATE'].unique())
        self.row_key_and_versions = None
        self.versions_df: pd.DataFrame
        self.deduped_versions_df: pd.DataFrame
        self.versions_full_info_df: pd.DataFrame

    def find_records_versions(self):
        """Generates a dictionary of all the versions that each unique row belongs to.

        Uses every unique change date in the whole state (which ensures it grabs counties leaving the district). For
        each record, determine which of these change dates it belongs to/is present in via
        _get_unique_district_versions and a dictionary comprehension.
        """

        self.district_records['UNIQUE_ROW_KEY'] = [
            str(shp_key) + '__' + str(dst_key)
            for shp_key, dst_key in zip(self.district_records['SHP_KEY'], self.district_records['DST_KEY'])
        ]

        self.row_key_and_versions = {
            row_key: self._get_unique_district_versions(self.unique_change_dates, start_date, end_date)
            for row_key, start_date, end_date in zip(
                self.district_records['UNIQUE_ROW_KEY'],
                self.district_records['CHANGE_DATE'],
                self.district_records['CHANGE_END_DATE'],
            )
        }

    def build_versions_dataframe(self):
        """Each record with its district version identified by 'district-number_date' (ie, '1_1896-01-06')
        """
        versions = []
        for row_key, version_list in self.row_key_and_versions.items():
            for change_date in version_list:
                #: creates [(row_key1, d_key1, date1), (row_key2, d_key1, date1), ...]
                versions.append(
                    (row_key, f'{self.label}_{pd.to_datetime(change_date).strftime("%Y-%m-%d")}', change_date)
                )

        #: CHANGE_DATE_IN_DST is the unique, state-wide change date (that may or may not contain a change for the
        #: particular row key) that the row was evaluated for.
        self.versions_df = pd.DataFrame(versions, columns=['UNIQUE_ROW_KEY', 'DST_VERSION_KEY', 'CHANGE_DATE_IN_DST'])

    def remove_duplicate_version_rows(self):
        """Filters rows based on the earliest unique dates for every UNIQUE_ROW_KEY using the dates from the entire
        district.

        Necessary because _get_unique_district_versions iterates over every change date in the whole state; thus, each
        district contains many records where nothing changed for that record on that date.
        """

        dates_and_row_keys = {}
        all_unique_change_dates = sorted(list(self.versions_full_info_df['CHANGE_DATE_IN_DST'].unique()))
        dates = []

        #: Build sorted dictionary of dates and their URKs so we can compare subsequent dates
        for date in all_unique_change_dates:
            dates_and_row_keys[date] = list(
                self.versions_full_info_df[self.versions_full_info_df['CHANGE_DATE_IN_DST'] == date]['UNIQUE_ROW_KEY']
            )

        #: comparison below using pairwise() won't add the first date, but only add if it's not empty
        if dates_and_row_keys[all_unique_change_dates[0]]:
            dates.append(all_unique_change_dates[0])

        #: Include date if it is list of URKs is different from the previous dates' list (ie, there was a change to the district's config)
        for first_date, next_date in pairwise(dates_and_row_keys):
            if sorted(dates_and_row_keys[first_date]) != sorted(dates_and_row_keys[next_date]):
                dates.append(next_date)

        self.deduped_versions_df = self.versions_full_info_df[
            self.versions_full_info_df['CHANGE_DATE_IN_DST'].isin(dates)]

    def join_version_information(self):
        """For each record and district version, join all other info back in via UNIQUE_ROW_KEY
        """
        self.versions_full_info_df = pd.merge(
            self.versions_df,
            self.district_records,
            how='left',
            left_on='UNIQUE_ROW_KEY',
            right_on='UNIQUE_ROW_KEY',
            validate='m:1'
        )

    def _get_unique_district_versions(self, unique_dates, start_date, end_date):
        """Get a list of versions this record is part of based on start and end date.

        Operates on the start and end date of a single record from a combined district and shape table. Identifies which
        change dates the record belongs to by checking its temporal bounds against each change date in the States's
        full set of change dates.

        Args:
            unique_dates (list[np.datetime64?]): All the change dates for the entire state.
            start_date (np.datetime64?): The record's starting date.
            end_date (np.datetime64?): The record's ending date. Can be the day before a change date in unique_dates
            or NaT if it's the most current version.

        Returns:
            list[np.datetime64?]: list of change dates from unique dates that this record belongs to.
        """
        versions_list = []
        for date in unique_dates:
            #: first check: does the record start before this change date and end after it?
            if start_date <= date <= end_date:
                versions_list.append(date)
                continue

            #: second check: does the record start before this change date and not have an end date?
            if start_date <= date and pd.isnull(end_date):
                versions_list.append(date)

        return versions_list
