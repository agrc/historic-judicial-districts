from collections import namedtuple

import arcpy
import pandas as pd


def clean_name(name):
    clean_name = name.casefold()
    clean_name = clean_name.replace(' ', '')
    clean_name = clean_name.replace('.', '')
    return clean_name


class ChangeDate:

    def __init__(self, date):
        self.date = date
        self.county_version = 'n/a'
        self.district = 'n/a'

    def __repr__(self):
        return ', '.join([str(self.date), self.county_version, str(self.district)])


class State:

    def __init__(self):
        self.counties_df = None
        self.districts_df = None
        self.counties = []  #: list of County objects

    def load_counties(self, counties_shp):

        #: Read counties shapefile in as dict, transform dict to dataframe
        print(f'Loading counties from {counties_shp}...')
        counties_list = []
        county_fields = [f.name for f in arcpy.ListFields(counties_shp)]
        with arcpy.da.SearchCursor(counties_shp, county_fields) as search_cursor:
            for row in search_cursor:
                counties_list.append(dict(zip(county_fields, row)))
        self.counties_df = pd.DataFrame(counties_list)

        #: Create county key- name_Sx
        self.counties_df['county_key'] = self.counties_df['ID'] + '_S' + self.counties_df['VERSION'].astype(str)

    def load_districts(self, districts_csv):

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
        #: Get a list of counties from the districts data frame and load them in as County objects

        county_names = self.districts_df['CountyName'].unique()
        for name in county_names:
            print(f'Setting up {name}...')
            county = County(name)
            county.setup(self.counties_df, self.districts_df)
            self.counties.append(county)

    def calc_counties(self):
        for county in self.counties:
            county.calc_change_dates()

    def combine_change_dfs(self, out_path):
        combined_change_df = pd.DataFrame()  #columns=['date', 'county_version', 'district'])
        for county in self.counties:
            combined_change_df = combined_change_df.append(county.change_dates_df)
        # print(combined_change_df)
        combined_change_df.to_csv(out_path)


class County:

    def __init__(self, name):
        self.name = name
        self.shape_df = None  #: All entries for this county in the historical county shape/geography dataframe
        self.district_df = None  #: All entries for this county in the historical district composition dataframe
        self.change_dates_df = None  #: The change dates with corresponding district and shape versions

    def setup(self, counties_df, districts_df):
        #: create a local shape dataframe of just the county, change the index to the start date of each version
        self.shape_df = counties_df[counties_df['ID'].str.contains(self.name)].copy()  #: copy to avoid chained indexing
        self.shape_df.set_index('START_DATE', inplace=True)
        self.shape_df.sort_index(inplace=True)

        #: create a local district dataframe of just the county, change the index to the start date of each version
        self.district_df = districts_df[districts_df['CountyName'].str.contains(self.name, case=False)].copy()
        self.district_df.set_index('StartDate', inplace=True)
        self.district_df.sort_index(inplace=True)

    def get_versions(self):
        #         check_dates = self.all_dates + pd.Timedelta(days=1)
        #         versions_df = pd.DataFrame(self.all_dates + pd.Timedelta(days=1))
        pass

    def calc_change_dates(self):

        #: Get a list of ChangeDate objects for all the dates for this county
        dates = list(pd.Series(self.shape_df.index.union(self.district_df.index)))
        change_dates = [ChangeDate(date) for date in dates]

        for change_date in change_dates:
            #: Get the county key for this date
            for county_row in self.shape_df.itertuples():
                if change_date.date >= county_row.Index and change_date.date <= county_row.END_DATE:
                    change_date.county_version = county_row.county_key
                    break
            #: Get the district key for this date
            for district_row in self.district_df.itertuples():
                if change_date.date >= district_row.Index and change_date.date <= district_row.EndDate:
                    change_date.district = district_row.NewDistrict
                    break

        #: Now we can use a namedtuple to translate our object to dataframe rows
        #: (Didn't use one at first because we had to alter the list of ChangeDate items in the iterations)
        ChangeDatesTuple = namedtuple('ChangeDatesTuple', 'date county_version district')
        new_dates = [ChangeDatesTuple(cd.date, cd.county_version, cd.district) for cd in change_dates]
        self.change_dates_df = pd.DataFrame(new_dates)
