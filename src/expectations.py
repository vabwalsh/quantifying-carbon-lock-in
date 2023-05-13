# %%
import pandas as pd
import numpy as np

# %%
def make_expectation_over_data(data, area):
    
    credence = pd.read_csv('data/credences-venmans-carr.csv')

    scen_and_prob = data.merge(credence, on = ['RCP', 'SSP'], how = 'inner').fillna(0)

    # make a copy of the merged data in order to weight it
    scen_and_prob_weighted = scen_and_prob.copy()

    # make active cols which should be weighted separate variable, matters b/c prob vars shouldn't be included
    # in final output or get weighted by the following calculation
    prob_cols_to_ignore = ['country', 'region', 'SSP', 'RCP', 'Central', 'Pessimistic', ' optimistic']

    # multiply each row of emissions in the merged dataset of global emissions by the central probability of it's scenario 
    # by its data's central estimate of the likelyhood
    for col in scen_and_prob_weighted:
        if col not in prob_cols_to_ignore:
            scen_and_prob_weighted[col] = scen_and_prob_weighted[col] * scen_and_prob_weighted['Central']

    columns_to_drop = ['Central', ' optimistic', 'Pessimistic']
    existing_columns_to_drop = [col for col in columns_to_drop if col in scen_and_prob_weighted.columns]

    expectation = scen_and_prob_weighted.groupby(['country', 'region', 'SSP', 'RCP']).sum().drop(columns=existing_columns_to_drop).reset_index()
    
    return(expectation)

# %%
if __name__ == "__main__":
    make_expectation_over_data


