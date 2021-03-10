from collections import namedtuple

import arcpy
import pandas as pd


class ChangeDate:

    def __init__(self, date):
        self.date = date
        self.county_version = 'n/a'
        self.district = 'n/a'

    def __repr__(self):
        return ', '.join([str(self.date), self.county_version, str(self.district)])


class State:

    def __init__(self):
        counties_df = None
        districts_df = None
        counties = []  #: list of County objects

    def load_counties(self, counties_shp):

        #: Read counties shapefile in as dict, transform dict to dataframe
        counties_list = []
        county_fields = [f.name for f in arcpy.ListFields(counties_shp)]
        with arcpy.da.SearchCursor(counties_shp, county_fields) as sc:
            for row in sc:
                counties_list.append(dict(zip(county_fields, row)))
        self.counties_df = pd.DataFrame(counties_list)

        #: Create county key- name_Sx
        self.counties_df['county_key'] = self.counties_df['ID'] + '_S' + self.counties_df['VERSION'].astype(str)

    def load_districts(self, districts_csv):

        self.districts_df = pd.read_csv(districts_csv)

        #: Clean up dates
        self.districts_df['StartDate'] = pd.to_datetime(self.districts_df['StartDate'])
        self.districts_df['EndDate'] = pd.to_datetime(self.districts_df['EndDate'])

        #: Create district key- name_Dx
        self.districts_df['district_key'] = (
            self.districts_df['CountyName'].str.casefold() + '_D' + self.districts_df['Version'].astype(str)
        )

    def setup_counties(self):
        #: Get a list of counties from the districts data frame and load them in as County objects

        county_names = self.districts_df['CountyName'].unique()
        for name in county_names:
            county = County(name)
            county.setup(self.counties_df, self.districts_df)
            self.counties.append(county)


class County:

    def __init__(self, name):
        self.name = name.casefold()
        self.shape_df = None  #: All entries for this county in the historical county shape/geography dataframe
        self.district_df = None  #: All entries for this county in the historical dsitrict composition dataframe
        self.all_dates = None  #: Series of start dates day from both shape_df and district_df

    def setup(self, counties_df, districts_df):
        #: create a local shape dataframe of just the county, change the index to the start date of each version
        self.shape_df = counties_df[counties_df['ID'].str.contains(self.name)].copy()  #: copy to avoid chained indexing
        self.shape_df.set_index('START_DATE', inplace=True)
        self.shape_df.sort_index(inplace=True)

        #: create a local district dataframe of just the county, change the index to the start date of each version
        self.district_df = districts_df[districts_df['CountyName'].str.contains(self.name, case=False)].copy()
        self.district_df.set_index('StartDate', inplace=True)
        self.district_df.sort_index(inplace=True)

        #: create series of dates to check
        self.all_dates = pd.Series(self.shape_df.index.union(self.district_df.index))

    def get_versions(self):
        #         check_dates = self.all_dates + pd.Timedelta(days=1)
        #         versions_df = pd.DataFrame(self.all_dates + pd.Timedelta(days=1))
        pass
