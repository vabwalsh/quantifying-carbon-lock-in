# %%
# import libraries
import pandas as pd
import numpy as np
from functools import reduce

# %%
# return the data in plotting format
def format_consid_commit(df, asset):
    # get the unique countries in the dataset
    countries = df['country'].unique()

    # create a list of all possible column names for the pivot table
    statuses = df['Status'].unique()
    years = np.arange(2021, 2101)
    col_names = [f"{asset}.{s}.{y}" for s in statuses for y in years]

    # create an empty pivot table with the desired column names
    pivot = pd.DataFrame(index = countries, columns = col_names)

    # loop through each country
    for country in countries:
        # loop through each year and status
        for year in years:
            for status in statuses:
                # calculate the sum of CO2 for this combination of year and status
                mask = (df['country'] == country) & (df['Status'] == status) & (df['Start year'] <= year) & (df['Planned retire'] > year)
                co2_sum = df.loc[mask, 'CO2 (Mt/yr)'].sum()
                # set the value of the pivot table to the CO2 sum
                col_name = f"{asset}.{status}.{year}"
                pivot.loc[country, col_name] = co2_sum

    # fill any missing values with 0
    pivot = pivot.fillna(0).reset_index().rename(columns = {'index':'country'})
    
    return(pivot)

# %%
# write a function that combines my dataframes however specified
# fillna with 0 here so that in calculations we get negative values instead of more NAs
def merge_dataframes(dfs):
    return reduce(lambda left, right: pd.merge(left, right, on='country', how='outer').fillna(0), dfs)

# %%
def make_yr_based_total(df, new_col_name):
    
    df_new = df.copy()
    
    # select the year range to bother totaling
    for year in range(2021,2101):
        # keep track of columns with the same year here
        cols_to_total = []

        for col_name in df_new.columns[1:]: 
            # if the column of this iteration has the yr in it, add it to the list
            if str(year) == str(col_name[-4:]):
                cols_to_total.append(col_name)
        
        # for each year in the original data, create a column with the total of all data for that year
        df_new[new_col_name + str(year)] = np.nansum(df_new[cols_to_total], axis = 1)
    
    # return the last 80 columns of the data, to get the totals, then add back the country retroactively
    new_cols = df_new.iloc[:,-80:]
    new_cols['country'] = df_new['country']
    
    print('year totals made for ' + str(new_col_name))
    
    return(new_cols)

# %%
def aggregate_to_master(coal, gas, steel, tong, scen):
    
    # could try to separate considered and committed emissions by operation status
    #consid_steel_plants = steel[steel['Status'] != 'operating']
    #commit_steel_plants = steel[steel['Status'] == 'operating']

    consid_coal_plants = coal[coal['Status'] != 'operating']
    commit_coal_plants = coal[coal['Status'] == 'operating']

    consid_gas_plants = gas[gas['Status'] != 'operating']
    commit_gas_plants = gas[gas['Status'] == 'operating']
    
    # create the plotting ready data frames (considered only)
    coal_cons_pivot = format_consid_commit(consid_coal_plants, 'coal')
    gas_cons_pivot = format_consid_commit(consid_gas_plants, 'gas')
    #steel_cons_pivot = format_consid_commit(consid_steel_plants, 'steel')

    # create the plotting ready data frames (committed only)
    coal_comm_pivot = format_consid_commit(commit_coal_plants, 'coal')
    gas_comm_pivot = format_consid_commit(commit_gas_plants, 'gas')
    #steel_comm_pivot = format_consid_commit(commit_steel_plants, 'steel')
    
    print('considered and committed data separated')
    
    # create the plotting ready data frames (consid and commit)
    coal_pivot = format_consid_commit(coal, 'coal')
    gas_pivot = format_consid_commit(gas, 'gas')
    #steel_pivot = format_consid_commit(steel, 'steel')
    
    print('completed initial coal, gas, and steel formatting')
    
    # make dfs with the cons and comms totals
    coal_cons = make_yr_based_total(coal_cons_pivot,'coal.consid.total.')
    gas_cons = make_yr_based_total(gas_cons_pivot,'gas.consid.total.')
    #steel_cons = make_yr_based_total(steel_cons_pivot,'steel.consid.total.')

    coal_comm = make_yr_based_total(coal_comm_pivot, 'coal.commit.total.')
    gas_comm = make_yr_based_total(gas_comm_pivot, 'gas.commit.total.')
    #steel_comm = make_yr_based_total(steel_comm_pivot, 'steel.commit.total.')
    
    print('created totals for coal/gas/steel')
    
    # 1 Total
    # created considered electricity
    # (1) combine the gas and coal dfs (commit and consid respectively)
    #gas_coal_comm = merge_dataframes([gas_comm_pivot, coal_comm_pivot])
    gas_coal_cons = merge_dataframes([gas_cons_pivot, coal_cons_pivot])

    # (2) add these together to create the considered electricity
    #elec_commit = make_yr_based_total(gas_coal_comm, 'elec.commit.total.')
    elec_cons = make_yr_based_total(gas_coal_cons, 'elec.consid.total.')

    print('considered electricty metric created from gas and coal (GEM)')

    # 1.5 Total
    # created committed electricity
    # (1) take a subset of the Tong data that is only electricity
    comm_elec_cols = ['country']

    for col in tong.columns:
        if 'Electricity' in col:
            comm_elec_cols.append(col)
 
    elec_commit = make_yr_based_total(tong[comm_elec_cols], 'elec.commit.total.')
    
    print('committed electricty metric taken from Tong subset')
    
    # 2 Total
    # create committed industry from the tong emissions
    industry_commit = make_yr_based_total(tong, 'industry.commit.total.')
    
    # 3 Total
    # create considered industry with a custom metric
    # made from: consid_elec, commit_elec.2021, and industry.commit.2021
    # first, combine all the input data 
    pre_inds_cons = merge_dataframes([elec_cons, elec_commit, tong]).fillna(0)

    # create an empty df to propogate with considered emissions from industry
    industry_cons = pd.DataFrame()

    # make sure this has the same countries as the original data
    industry_cons['country'] = pre_inds_cons['country']

    # for all the years in the data, propogate the considered emissions df
    for yr in np.arange(2021, 2101):
        industry_cons['industry.consid.total.' + str(yr)] = (pre_inds_cons['elec.consid.total.' + str(yr)] / pre_inds_cons['elec.commit.total.2021']) * pre_inds_cons['Industry.2021']

    # replace the inf and NaN values from dividing by 0 with 0s
    industry_cons = industry_cons.replace([np.inf, np.nan], 0)
    
    print('considered industry metric created from industry/elec 2021 ration and considered elec')
    
    # 4
    # # make committed emissions total from industry and elec -- OUTDATED AND REPLACED BY USING ALL TONG DATA
    # inds_elec_comm = merge_dataframes([industry_commit, elec_commit])
    # comm_total = make_yr_based_total(inds_elec_comm, 'commit.total.')

    # make committed emissions total from tong data
    comm_total = make_yr_based_total(tong, 'commit.total.')

    # make considered emissions total from industry and and gas and coal-- BUT NOT STEEL
    # to include steel, add steel_cons to the list below
    gas_coal_inds_cons = merge_dataframes([gas_cons, coal_cons, industry_cons])
    cons_total = make_yr_based_total(gas_coal_inds_cons, 'consid.total.')
    
    # 5
    # make comm+consid total from combining these
    cons_total_comms_total = merge_dataframes([comm_total, cons_total])
    comm_cons_total = make_yr_based_total(cons_total_comms_total, 'consid+commit.total.')
    
    # 6
    # Make "expectable" emissions from scenario - (consid + commit)
    # this has to account for rcp and ssp, so can't use the regular merge functions
    merged_df = scen.merge(comm_cons_total, on = 'country', how = 'left').fillna(0)
    
    # holding df to propogate with expectable values
    expectable = pd.DataFrame({'country': merged_df['country'], 'SSP': merged_df['SSP'], 'RCP': merged_df['RCP']})

    for year in range(2021, 2101):
        ex_col_name = 'expectable.' + str(year)
        sum_col_name = 'consid+commit+scen.' + str(year)

        expectable[ex_col_name] = merged_df[str(year)] - merged_df['consid+commit.total.' + str(year)]
        expectable[sum_col_name] = merged_df[str(year)] + merged_df['consid+commit.total.' + str(year)]
        
    print('expectable emissions created')
    
    # 6  
    # This line removes the data from 1850-2020, which is introduced by the complete GEM datasets
    scenario_CO2_2021_on = scen.iloc[:,:3].join(scen.iloc[:,175:])
    
    # 7
    master = pd.merge(scenario_CO2_2021_on, expectable, on = ['country','RCP','SSP'], how = 'outer').merge(gas_pivot, 
                                                    on = 'country', how = 'outer').merge(coal_pivot, 
                                                    on = 'country', how = 'outer').merge(gas_cons, 
                                                    on = 'country', how = 'outer').merge(coal_cons, 
                                                    on = 'country', how = 'outer').merge(industry_cons, 
                                                    on = 'country', how = 'outer').merge(gas_comm, 
                                                    on = 'country', how = 'outer').merge(coal_comm, 
                                                    on = 'country', how = 'outer').merge(elec_commit,
                                                    on = 'country', how = 'outer').merge(elec_cons, 
                                                    on = 'country', how = 'outer').merge(industry_commit, 
                                                    on = 'country', how = 'outer').merge(cons_total, 
                                                    on = 'country', how = 'outer').merge(comm_total, 
                                                    on = 'country', how = 'outer').merge(comm_cons_total, 
                                                    on = 'country', how = 'outer').fillna(0)
                                                    
                                                    # not to self: include elec_cons
                                                    # to incorporate the steel data back in to the master file, uncomment the lines below
                                                    # you will also need to modify the value of the considered emissions total (line 4)
                                                    #.merge(steel_pivot, on = 'country', how = 'outer')
                                                    #.merge(steel_cons, on = 'country', how = 'outer')
                                                    #.merge(steel_comm,#on = 'country', how = 'outer')
    
    print('master file merge successful')
    
    # parse the region mapping
    regions = pd.read_csv('data/cntry_short_region_map.csv').drop(columns = 'short')
    
    # this is what makes the master file not have lines for the countries in the not-working code below (e.g. N. Korea)
    region_merge = pd.merge(master, regions, how = 'left', on = 'country')

    # put region column at the front of the df
    reg = region_merge.pop('region')
    region_merge.insert(1, reg.name, reg)
    region_merge.to_csv('data/master.csv')
    
    print('master file merged with regions')
    
    return(region_merge)

# %%
if __name__ == "__main__":
    aggregate_to_master
    make_yr_based_total


