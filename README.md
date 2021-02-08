# agrc/python

![Build Status](https://github.com/agrc/python/workflows/Build%20and%20Test/badge.svg)
[![codecov](https://codecov.io/gh/agrc/python/branch/main/graph/badge.svg)](https://codecov.io/gh/agrc/historic-judicial-districts)

Home of `lookback`, a tool to create the county composition of historic judicial districts based on a shapefile of historic county boundaries and a csv of counties and their assigned districts over the year.
## Installation

1. Create new environment for the project
   - `conda create --clone arcgispro-py3 --name lookback`
1. Install an editable package for development
   - `pip install -e ".[tests]"`
