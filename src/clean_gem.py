# %%
import pandas as pd
import numpy as np
import warnings
import random
warnings.filterwarnings('ignore')

# %% [markdown]
# ### Cleaning the GEM data

# %%
def standardize_cols(coal, gas, steel):
    
    # Subset all of the datasets to include the information needed to create panel data with them
    # and standardize their names

    # Define a dictionary to map old column names to new ones
    coal_cols = {'country.name.en': 'country', 'Status': 'Status', 'Year': 'Start year', 'Planned Retire': 'Planned retire', 'Capacity (MW)': 'Capacity (MW)', 'Annual CO2 (million tonnes / annum)': 'CO2 (Mt/yr)', 'RETIRED':'RETIRED'}
    gas_cols = {'country.name.en': 'country', 'Status': 'Status', 'Start year': 'Start year', 'Planned retire': 'Planned retire', 'Capacity elec. (MW)': 'Capacity (MW)'}
    steel_cols = {'country.name.en': 'country', 'Status': 'Status', 'Start year': 'Start year', 'Closed/idled year': 'Planned retire', 'Plant age (years)': 'Plant age (years)'}

    # Use the dictionary to select and rename the columns for each DataFrame
    coal_subset = coal.rename(columns=coal_cols)[list(coal_cols.values())]
    gas_subset = gas.rename(columns=gas_cols)[list(gas_cols.values())]
    steel_subset = steel.rename(columns=steel_cols)[list(steel_cols.values())]
    
    return coal_subset, gas_subset, steel_subset

# %%
# define a function to filter the plant stati
def filter_stati(df, valid_statuses):
    return df[df['Status'].isin(valid_statuses)]

# %%
# define a functiont to weigh the steel data
def weight_steel(steel_plants_filtered, steel):
    
    # First parse the files with the emissions intensities and capacity utilization rates for each type of steel production in each country
    # if the columns of these files are renamed, you may need to modify this code to clean the files slightly differently
    # These files were originally created by Tom, and are in the FP drive here https://docs.google.com/spreadsheets/d/1TOH_Xq8rIaLiOM_cr0IwZuX5jw6KlRkpv2sJQSciHoc/edit#gid=515274497
    emit_int_weight = pd.read_csv('data/emit_int_weights.csv', index_col = 0).astype(float).reset_index().rename(columns = {'Units: Tonnes of CO2 per tonne of steel': 'country'})
    utr_rate_weight = pd.read_csv('data/utilization_rt_weights.csv', index_col = 0).astype(float).reset_index().rename(columns = {'index': 'country'})

    # Specify the relevant columns from the raw steel data (those which actually measure output), and turn these into a list
    # Then, clean up the values in these columns to make them numeric and non-zero (since we will be multiplying them by other values)
    production_cols = [col for col in steel.columns if 'capacity' in col]
    steel_plants_filtered[production_cols] = steel[production_cols].replace([' ','unknown','>0', np.nan], value = 1).replace('10,000',10000).astype(float)

    # Merge the three datasets based on their country columns, which may not contain all the same values
    rates_df = pd.merge(emit_int_weight, utr_rate_weight, on = 'country', how = 'outer').merge(steel_plants_filtered, on = 'country', how = 'outer') 

    # Because some countries aren't in the weighting factors, replace NaN values created by the merge (where steel data exists, but not weighting factors, or vice versa) with the mean value of the respective column
    # This means countries not included in the emissions intensity and capacity utilization rate datasets will be assigned the mean production, capacity, or emit. int. for that type of steel production
    # Again replace 0 values with 1, so that any emissions intensity or capacity utilization rate of 0 will not result in a 0 value for the weighted steel production
    rates_df = rates_df.fillna(rates_df.mean()).replace(0, 1)

    # Give a list of keywords that can identify the type of steel production
    key = ['crude', 'BOF', 'EAF', 'OHF', 'Iron', 'BF', 'DRI', 'Ferronickel', 'Sinter plant', 'Coking plant', 'Pelletizing']

    # Initialize a DataFrame to store the the product of the three datasets, which already contains the metadata items we want in the final steel output
    result_df = pd.DataFrame(steel_plants_filtered[['country', 'Status', 'Start year', 'Planned retire', 'Plant age (years)']])

    # Iterate over the list of keywords
    for k in key:
        # Find the columns containing the same keyword for emissions intensity and capacity
        intensity_col = [col for col in rates_df.columns if k in col and 'emissions intensity' in col]
        capacity_col = [col for col in rates_df.columns if k in col and 'capacity' in col and 'per annum' in col]
        prod_col = [col for col in rates_df.columns if k in col and '(ttpa)' in col]                                      

        # Check if all columns are found
        if intensity_col and capacity_col and prod_col:
            # Multiply the the production capacity, emissions intensity, and steel production in ttpa together and store the result in a new column
            # emit int = tonnes CO2 / tonnes steel, production capacity = a fraction, and steel production = 1000 tonnes / year
            # to result in emissions units of Mt/yr, first multiply by 1000 to get tonnes CO2/yr, then divide by 1,000,000 again to get MtCO2/yr
            result_df[f'{k}_emissions'] = rates_df[intensity_col[0]] * rates_df[capacity_col[0]] * rates_df[prod_col[0]] * 1000 / 1000000

    # Filter the columns with '_emissions' in their name
    emissions_columns = result_df.filter(like='_emissions', axis=1)

    # Sum the emissions columns along the rows (axis=1)
    result_df['CO2 (Mt/yr)'] = emissions_columns.sum(axis=1)

    # Return only the metadata columns and the newly created CO2 emissions column
    result_df = result_df.drop(emissions_columns.columns, axis=1)

    return result_df

# %%
def clean_gas_starts(filtered_gas):
    
    # Repare the misspecified start years in the filtered_gas data
    # it seems that the gas start years list some massive ranges separated by commas in the start year column
    # based on the wikis, these seem to generally be the first opening of the first unit and the planned closing
    filtered_gas['Start year'] = filtered_gas['Start year'].replace('0',np.nan).astype(str)

    for i, row in filtered_gas.iterrows():

        if isinstance(row['Start year'], str) and ',' in row['Start year']:
            start_year_parts = row['Start year'].split(',')

            start_year = start_year_parts[0].strip()
            retire_year = start_year_parts[1].strip()

            filtered_gas.at[i, 'Start year'] = start_year
            filtered_gas.at[i, 'Planned retire'] = max(float(row['Planned retire']), float(retire_year))
    
    return filtered_gas

# %%
# define a function to clean the gem plant start years up
def clean_GEM(coal_plants, gas_plants, steel_plants):

    # write a function that calculate sthe average start year for each assest type by status and country
    gem_data = [coal_plants, gas_plants, steel_plants]

    for dataset in gem_data:

        # Replace all the weird year values with nans
        dataset['Start year'] = dataset['Start year'].replace(['unclear','',' ','Unclear','NA', 'TBD','lear',
                                                                'tbd','13th plan','unknown', 0, 'not found', 
                                                                'Not found', '0:00', 'nan', '>0'], 
                                                                value = np.nan).replace('2021-30','2026')

        dataset['Planned retire'] = dataset['Planned retire'].replace(['2030s', '2021-2025'], value = np.nan)

        steel_plants['Plant age (years)'] = steel_plants['Plant age (years)'].replace(['unknown'], value = np.nan)
        
        # For plants with multiple years listed (separated by a dash, e.g. "2000-2005"), take the later year
        start_yr_slice = []

        for yr in dataset['Start year']:
            start_yr_slice.append((str(yr))[-4:])

        #print(start_yr_slice)
        # make everything a float so it can be added
        dataset['Start year'] = start_yr_slice
        dataset['Start year'] = dataset['Start year'].astype(float)
        dataset['Planned retire'] = dataset['Planned retire'].astype(float)
        steel_plants['Plant age (years)'] = steel_plants['Plant age (years)'].astype(float)

        # Calculate average start years for each status in the dataset, excluding NaN values
        avg_start_years = np.round(dataset.groupby('Status')['Start year'].mean(), 0)
        #print(np.round(avg_start_years,0))

        # fill missing data in start and retirement years
        # initialize the lists of clean start and retirement years
        start_yrs = []

        # enumerate the #i of rows in the dataset
        for i, row in dataset.iterrows():
            
            # for the steel data, if there is a plant age listed, use that to badck-calculate the start yr
            if dataset.equals(steel_plants) == True and not pd.isna(row['Plant age (years)']):
                # if there is a plant age listed, use that to calculate the start yr
                start_yrs.append(2022 - row['Plant age (years)'])

            # start year conditions
            else:
                if not pd.isna(row['Start year']):
                    start_yrs.append(row['Start year'])

                elif pd.isna(row['Start year']):

                    # Get the average start year for the current status, if available
                    avg_start_year = avg_start_years.get(row['Status'])

                    if avg_start_year is not None:
                        start_yrs.append(avg_start_year)

                    else:
                        # Fallback value in case the average start year for the current status is not available
                        print('error')

        dataset['Start year'] = list(map(float, start_yrs))

        # Calculate average retirement years for each status in the dataset
        retirement_yrs = []

        for i, row in dataset.iterrows():
            if 'RETIRED' in dataset.columns and not pd.isna(row['RETIRED']):
                retirement_yrs.append(row['RETIRED'])

            elif not pd.isna(row['Planned retire']):
                retirement_yrs.append(row['Planned retire'])

            elif pd.isna(row['Planned retire']):
                if row['Status'] == 'operating' and (row['Start year'] + 40) < 2022 and dataset.equals(steel_plants):
                    retirement_yrs.append(row['Start year'] + row['Plant age (years)'] + random.randint(1,15))
                else:
                    retirement_yrs.append(row['Start year'] + 40)

            else: 
                print('error')

        dataset['Planned retire'] = list(map(float, retirement_yrs))

    return coal_plants, gas_plants, steel_plants

# %%
def make_gas_co2(gas_data):

    # 83 Mt CO2 of committed emissions per newly constructed GW of gas-fired capacity
    # gas plant capacity represents possible output if fully operating
    # new gas capacity commits X Mt Co2 = Y MW capacity / 12
    # this means that every plant in the dataset can be assumed to produce Y/12 MtCO2 over it's lifetime

    # this conversion from Davis et al. 2014: https://iopscience.iop.org/article/10.1088/1748-9326/9/8/084018/meta
    # calculate lifetime to get the number of years over which to propogate the annual emissions (counting from the start year)
    gas_data['Lifetime'] = (gas_data['Planned retire'] - gas_data['Start year'])

    # calculate the annual emissions for each plant, the capacity * 1/12 divided over 40 years
    gas_data['CO2 (Mt/yr)'] = (gas_data['Capacity (MW)'] / 12) /  40
    
    return(gas_data)

# %% [markdown]
# #### Main function to call the others

# %%
def format_GEM(coal, gas, steel):
    
    # standardize the column names across the datasets
    coal_subset, gas_subset, steel_subset = standardize_cols(coal, gas, steel)
    
    # Define the valid statuses for each plant type
    coal_statuses = ['operating', 'construction', 'pre-permit', 'announced', 'permitted']
    gas_statuses = ['operating', 'construction', 'announced', 'pre-construction']
    steel_statuses = ['proposed', 'operating', 'construction']

    # Subset the data to the relevant stati for considered or committed emissions (e.g. ignore retired plants)
    coal_plants_filtered = filter_stati(coal_subset, coal_statuses)
    gas_plants_filtered = filter_stati(gas_subset, gas_statuses)
    steel_plants_filtered = filter_stati(steel_subset, steel_statuses)
    
    # weight the steel data by capacity and emissions intensity
    steel_plants_weighted = weight_steel(steel_plants_filtered, steel)
    
    # resolve the misspecified gas data
    gas_plants_yr_fix = clean_gas_starts(gas_plants_filtered)
    
    coal_plants_clean, gas_plants_clean, steel_plants_clean = clean_GEM(coal_plants_filtered, gas_plants_yr_fix, steel_plants_weighted)
    
    # add CO2 to the gas data using the MW to CO2 conversion estimate
    gas_CO2 = make_gas_co2(gas_plants_clean)
    
    steel_plants_clean.to_csv('data/steel_panel.csv')
    coal_plants_clean.to_csv('data/coal_panel.csv')
    gas_CO2.to_csv('data/gas_panel.csv')
    
    return(coal_plants_clean, gas_CO2, steel_plants_clean)

# %% [markdown]
# #### For export test:
# This code coerces the data into the plotting shape, this was original outout for the data aggregation, but is not being used currently. This function can reformat the data into a panel format for plotting as an intermediate step.

# %%
# use with <<format_to_panel(asset_plants_clean, 'asset_name')>>

def format_to_panel(dataset, name):
    
    # a sneaky way to remove the irrelevant RETIRED, Plant age (years), and remaining NaN columns
    dataset = dataset[['country', 'Status', 'Start year', 'Planned retire', 'CO2 (Mt/yr)']].dropna()
    
    # Make the column dtypes numeric, so that they add during the merge instead of concatenating as strings
    dataset.iloc[:,2:] = dataset.iloc[:,2:]#.astype(float)

    # Group the data by the indices which will be used for row and column indices: country, status, and start.
    dataset_pivot = dataset.pivot_table(index = 'country', columns = ['Status', 
                                  'Start year']).sort_values('Start year', axis = 1, 
                                   ascending = True).groupby(by = ['Status','Start year'], axis =1).sum()

    # Standardized column names by recombining the stati and years into names, and using these
    # select stati and years from the multi-index data
    stati = ['country'] + [item[0] for item in dataset_pivot.columns]
    yrs = [''] + [str(item[1])[:-2] for item in dataset_pivot.columns]
    
    # combine stati and yr lists into one
    cols = []
    for i in range(0, len(yrs)):
        cols.append(stati[i] + '.' + yrs[i])
    
    # reset the index of the multi-index, and replace it's col names with 'status.yr'
    reset_data = dataset_pivot.reset_index()
    reset_data.columns = cols
    
    # rename the columns in the horrible plotting format
    reset_data.columns = [name + '.CO2.' + col for col in reset_data.columns]
    reset_data = reset_data.rename(columns = {name + '.CO2.country.': 'country'})

    # Now in units of Mt CO2
    reset_data.to_csv('data/'+ name + '_panel_data_CO2' + '.csv')
    
    return(reset_data)

# %%
if __name__ == "__main__":
    format_GEM
    format_to_panel
    standardize_cols
    filter_stati
    weight_steel
    clean_gas_starts


