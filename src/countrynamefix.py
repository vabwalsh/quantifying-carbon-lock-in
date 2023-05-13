# %%
import pandas as pd
import numpy as np

# %%
def parse_raw_data():
    
    # read in the country names column from each of the initial datasets used in affetcable emissions
    tong_ctry = pd.read_csv('data/tong_committed_emissions/tong_panel.csv')
    
    # Remove the values in the Tong data which can't be mapped to a country, this currently corresponds to ~0.37% of the global committed emissions
    drop_areas = ['Other Africa', 'Other non-OECD Americas', 'Other non-OECD Asia']
    
    # Create a boolean mask to filter out rows with the specified country values
    mask = ~tong_ctry['Country'].isin(drop_areas)
    tong_fltr = tong_ctry[mask]

    scen_ctry = pd.read_csv('data/Guetschow_PMSSPBIE_KYOTOGHGAR4_subset.csv', encoding = 'latin1')
    coal_ctry = pd.read_csv('data/GEM_coalplants_july2022.csv')
    gas_ctry = pd.read_csv('data/GEM_gasplants_august2022.csv')
    steel_ctry = pd.read_csv('data/GEM_steelplants_march2022.csv', dtype = 'str')
    
    return(tong_fltr, scen_ctry, coal_ctry, gas_ctry, steel_ctry)

# %%
# The contents of the 'data/missing_alt_names.csv' file are manually added to the 'data/accurate_cntry_name_mapping.csv' file
# Check if there are any country names in the dataset currently in use which aren't listed as a possible 
# alternative specification in the country name mapping file, and create a list of new names to manually

def gen_and_check_missing_names_list(tong_ctry, scen_ctry, coal_ctry, gas_ctry, steel_ctry):

    # Read the file with a two column list mapping the correct country names to all alternative specifications
    # if any of the country names in the original data inputs have been changed, it's possible they aren't included in this file
    # this function will throw an error if this is the case
    alt_names_file = pd.read_csv('data/accurate_cntry_name_mapping.csv', usecols = ['country.name.en', 'country.name.alt'], dtype = str)

    # combine all these country names into a seires, and remove the repeats
    countries_in_data = pd.concat([tong_ctry['Country']] + [scen_ctry['country']] + [coal_ctry['Country']] + [gas_ctry['Country']] + [steel_ctry['Country']]).drop_duplicates(keep='first')

    # check what values from the countries in the data are not in the alt names file, and add these to a file cataloging these discrepancies
    missing_name_specifications = pd.DataFrame(countries_in_data[countries_in_data.isin(alt_names_file['country.name.alt']) == False].values)

    # write this file to a csv
    missing_name_specifications.to_csv('data/missing_alt_names.csv', index = False)
    print('any country names in the data which missing from the country name mapping file <accurate_cntry_name_mapping.csv> have been written to <missing_alt_names.csv>')

    # check that the length of this file is 0, because if not, that means that there are some unmapped countries or regions in the data
    if len(missing_name_specifications.values) != 0:
        raise Exception('All countries in the data are not accounted for in the alt names file, revise the file locally and run again')

    print('country name mapping file <accurate_cntry_name_mapping.csv> parsed, no missing country names were found')
    
    # return the clean country mapping (if there are no country names unspecified by the alt names file)
    return(alt_names_file)

# %%
def export_cntry_data_fix(clean_country_mapping, tong_ctry, scen_ctry, coal_ctry, gas_ctry, steel_ctry):

    # try to replace the country names in each dataset with the country names suggested by the mapping
    tong_cntry_fix = clean_country_mapping.merge(tong_ctry, left_on = 'country.name.alt', right_on = 'Country', how = 'inner').drop(columns = ['country.name.alt', 'Country'])
    scen_cntry_fix = clean_country_mapping.merge(scen_ctry, left_on = 'country.name.alt', right_on = 'country', how = 'inner').drop(columns = ['country.name.alt', 'country'])
    coal_cntry_fix = clean_country_mapping.merge(coal_ctry, left_on = 'country.name.alt', right_on = 'Country', how = 'inner').drop(columns = ['country.name.alt', 'Country'])
    gas_cntry_fix = clean_country_mapping.merge(gas_ctry, left_on = 'country.name.alt', right_on = 'Country', how = 'inner').drop(columns = ['country.name.alt', 'Country'])
    steel_cntry_fix = clean_country_mapping.merge(steel_ctry, left_on = 'country.name.alt', right_on = 'Country', how = 'inner').drop(columns = ['country.name.alt', 'Country'])

    # write the data with cleaned country names to the appropriate file
    tong_cntry_fix.to_csv('data/tong_cntry_fix.csv')
    scen_cntry_fix.to_csv('data/scen_cntry_fix.csv')
    coal_cntry_fix.to_csv('data/coal_cntry_fix.csv')
    gas_cntry_fix.to_csv('data/gas_cntry_fix.csv')
    steel_cntry_fix.to_csv('data/steel_cntry_fix.csv')
    
    print('initial data inputs written to files with corrected country names')
    
    return(tong_cntry_fix, scen_cntry_fix, coal_cntry_fix, gas_cntry_fix, steel_cntry_fix)

# %%
def countrynamefix():
   
    # execute component functions in order
    tong_ctry, scen_ctry, coal_ctry, gas_ctry, steel_ctry = parse_raw_data()
    clean_country_mapping = gen_and_check_missing_names_list(tong_ctry, scen_ctry, coal_ctry, gas_ctry, steel_ctry)
    tong_cntry_fix, scen_cntry_fix, coal_cntry_fix, gas_cntry_fix, steel_cntry_fix = export_cntry_data_fix(clean_country_mapping, tong_ctry, scen_ctry, coal_ctry, gas_ctry, steel_ctry)
    
    return(tong_cntry_fix, scen_cntry_fix, coal_cntry_fix, gas_cntry_fix, steel_cntry_fix)

# %%
if __name__ == "__main__":
    countrynamefix


