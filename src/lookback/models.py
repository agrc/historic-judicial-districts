from collections import namedtuple
from pathlib import Path

import arcpy
import pandas as pd


def clean_name(name):
    """Reformat name to better match format in the historic county boundaries shapefile

    Args:
        name (str): A name to clean

    Returns:
        str: name casefolded with spaces and periods removed
    """

    cleaned_name = name.casefold()
    cleaned_name = cleaned_name.replace(' ', '')
    cleaned_name = cleaned_name.replace('.', '')
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
        self.counties_df = None
        self.districts_df = None
        self.counties = []
        self.combined_change_df = None
        self.output_df = None

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
        self.counties_df = pd.DataFrame(counties_list)

        #: Create county key- name_Sx
        self.counties_df['county_key'] = self.counties_df['ID'] + '_S' + self.counties_df['VERSION'].astype(str)

    def load_districts(self, districts_csv):
        """Read historical district info into districts_df.

        Cleans name with clean_name(), parses dates, and calculates district
        key from CountyName and Versin fields.

        Args:
            districts_csv (str): Path to the historical districts data
        """

        print(f'Loading districts from {districts_csv}...')
        self.districts_df = pd.read_csv(districts_csv)

        #: change name to better match the county shapefile id
        self.districts_df['CountyName'] = self.districts_df['CountyName'].apply(clean_name)

        #: Clean up dates
        self.districts_df['StartDate'] = pd.to_datetime(self.districts_df['StartDate'])
        self.districts_df['EndDate'] = pd.to_datetime(self.districts_df['EndDate'])

        #: Create district key- name_Dx
        self.districts_df['district_key'] = (
            self.districts_df['CountyName'].str.casefold() + '_D' + self.districts_df['Version'].astype(str)
        )

    def setup_counties(self):
        """Get a list of counties from districts_df and load them in as County objects.
        """

        county_names = self.districts_df['CountyName'].unique()
        for name in county_names:
            print(f'Setting up {name}...')
            county = County(name)
            county.setup(self.counties_df, self.districts_df)
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
        self.combined_change_df = pd.DataFrame()  #columns=['date', 'county_version', 'district'])
        for county in self.counties:
            self.combined_change_df = self.combined_change_df.append(county.change_dates_df)
        if out_path:
            self.combined_change_df.to_csv(out_path)

    def insert_geometries(self):
        """Join shape/counties_df back into change dates to get relevant info
        """

        print('Coying geometries into change dates...')
        self.output_df = pd.DataFrame()
        for county in self.counties:
            county.copy_geometries_into_change_dates()
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
            ['CHANGE_DATE', 'DATE'],  #: change_df name
            ['CHANGE_ID', 'TEXT'],  #: change_df county_name
            ['SHP_NAME', 'TEXT'],  #: shape_df NAME
            ['SHP_ID', 'TEXT'],  #: shape_df ID
            ['SHP_FIPS', 'TEXT'],  #: shape_df FIPS
            ['SHP_VERSION', 'TEXT'],  #: shape_df VERSION
            ['DST_NUMBER', 'TEXT'],  #: district_df district
            ['SHP_START_DATE', 'DATE'],  #: shape_df START_DATE
            ['SHP_END_DATE', 'DATE'],  #: shape_df END_DATE
            ['DST_START_DATE', 'DATE'],  #: district_df date
            ['DST_END_DATE', 'DATE'],  #: district_df end_date
            ['SHP_CHANGE', 'TEXT'],  #: shape_df CHANGE
            ['SHP_CITATION', 'TEXT'],  #: shape_df CITATION
            ['SHP_AREA_SQMI', 'DOUBLE'],  #: shape_df AREA_SQMI
            ['SHP_KEY', 'TEXT'],  #: shape_df county_key
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
            'county_key': 'SHP_KEY',
            'district_key': 'DST_KEY',
            'SHAPE@': 'SHAPE@',
            'date': 'CHANGE_DATE',
            'county_name': 'CHANGE_ID'
        }

        arcpy.management.AddFields(out_path, new_fields)

        print(f'Writing out to {out_path}...')

        #: Rename the data frame columns to match the output fields
        renamed_df = self.output_df.rename(columns=df_renamer)
        cursor_fields = df_renamer.values()  #: Only look at the renamed columns
        with arcpy.da.InsertCursor(out_path, list(cursor_fields)) as insert_cursor:
            for row in renamed_df[cursor_fields].values.tolist():
                insert_cursor.insertRow(nulls_to_nones(row))


class County:
    """Data and processing for a specific county within the total dataset.

    Attributes:
        name (str): County's name, lowercased and spaces/periods removed
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
        self.shape_df = counties_df[counties_df['ID'].str.contains(self.name)].copy()  #: copy to avoid chained indexing
        self.shape_df.set_index('START_DATE', inplace=True)
        self.shape_df['START_DATE'] = self.shape_df.index  #: re-add start date for output data
        self.shape_df.sort_index(inplace=True)

        #: create a local district dataframe of just the county, change the index to the start date of each version
        self.district_df = districts_df[districts_df['CountyName'].str.contains(self.name, case=False)].copy()
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
            change_date.county_name = self.name

            #: Get the county key for this date
            for county_row in self.shape_df.itertuples():
                if change_date.date >= county_row.Index and change_date.date <= county_row.END_DATE:
                    change_date.county_version = county_row.county_key
                    break
            #: Get the district key for this date
            for district_row in self.district_df.itertuples():
                if change_date.date >= district_row.Index and change_date.date <= district_row.EndDate:
                    change_date.district_number = district_row.NewDistrict
                    change_date.district_version = district_row.district_key
                    break

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

    def copy_geometries_into_change_dates(self):
        """Add geometries back into change date dataframe

        Joins the shape and district dataframes to the change date data to
        add geometries and other relevant info for each change date.
        """

        first_join = pd.merge(
            self.change_dates_df,
            self.shape_df,
            how='left',
            left_on='county_version',
            right_on='county_key',
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
