# %%
# import libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
#from expectations import make_expectation_over_data
warnings.filterwarnings('ignore')

# %%
#for each dataset, define a function which groups their columns by the plotting variables needed
def make_plot_vars(dataset, affectability_status):
    
    # decide on the plotting variables to creats
    commit_total_cols = []
    consid_total_cols = []
    comm_cons_cols = []
    consid_commit_scen_total_cols = []
    expectable = []
    yr_cols = []

    X = np.arange(2021, 2101)
    # append columns in the dataset to the appropriate group based on their name
    for col in dataset.columns:
        for yr in X:
            if 'commit.total.' + str(yr) == str(col):
                commit_total_cols.append(col)
            if 'consid.total.' + str(yr) == str(col):
                consid_total_cols.append(col)
            if 'consid+commit.total.' + str(yr) == str(col):
                comm_cons_cols.append(col)
            if 'consid+commit+scen.' + str(yr) == str(col):
                consid_commit_scen_total_cols.append(col)
            if 'expectable.' + str(yr) == str(col):
                expectable.append(col)
        if len(col) == 4:
            yr_cols.append(col)
            
    # set expectable emissions >= 0 in all cases
    for col in dataset[expectable].columns:
        if affectability_status == 'raw':
            dataset[col][dataset[col] < 0] = 0
        elif affectability_status == 'affectable':
            dataset[col][dataset[col] < 0] = 0

    # set considered emissions > 0, so that committed emissions always stack below them
    for col in dataset[consid_total_cols].columns:
        dataset[col][dataset[col] == 0] = 0.000001
    
    # return the newly grouped column lists, so that dataset[list_name] returns data corresponding the group
    return(commit_total_cols, consid_total_cols, comm_cons_cols, consid_commit_scen_total_cols, expectable, yr_cols)

# %%
# Specify the name of the file to operate on, a base title string which will name the figures and the plot files,
# and a filepath pointing to where the files should be saved.
def plot_data(dataset, affectability_status, title_str, sub_folder):
    
    # make the plotting variables for a dataset by calling the function defined above
    commit_total_cols, consid_total_cols, comm_cons_cols, consid_commit_scen_total_cols, expectable, yr_cols = make_plot_vars(dataset, affectability_status)
    
    X = np.arange(2021, 2101)
    
    for row in range(len(dataset)):
                
        plt.figure(figsize=(10,3))
        plt.tight_layout()
        plt.stackplot(X, 
                      dataset[commit_total_cols].loc[row],
                      dataset[consid_total_cols].loc[row], 
                      dataset[expectable].loc[row], 
                      labels=['Committed Emissions','Considered Emissions','Expectable'],
                      colors = ['firebrick', 'darksalmon', 'navajowhite'])
        
        plt.plot(X, dataset[commit_total_cols].loc[row], color = 'firebrick', linestyle = 'dashed')
        plt.plot(X, dataset[comm_cons_cols].loc[row], color = 'darksalmon', linestyle = 'dashed')
        
        if affectability_status == 'raw':
            plt.plot(X, dataset[yr_cols].loc[row], color = 'black', label = 'Scenario Emissions')
            
            for col in dataset[expectable].columns:
                plt.fill_between(X, dataset[yr_cols].loc[row], 0, 
                     where = dataset[yr_cols].loc[row] < 0, color = 'navajowhite')

        # specify the plot name to work for both expectation aggregated and singular scenario datasets
        if 'SSP' and 'RCP' in dataset.columns:
            if 'country' in dataset.columns:
                fig_name = str(dataset['country'].loc[row] + '_' 
                               + dataset['SSP'].loc[row] + 'RCP' 
                               + dataset['RCP'].loc[row] + title_str)
                plt.title(title_str + dataset['country'].loc[row] 
                          + ' _' + dataset['SSP'].loc[row] 
                          + 'RCP ' + dataset['RCP'].loc[row])
            elif 'country' not in dataset.columns and 'region' in dataset.columns:
                fig_name = str(dataset['region'].loc[row] + '_' 
                               + dataset['SSP'].loc[row] + 'RCP' 
                               + dataset['RCP'].loc[row] + title_str)
                plt.title(title_str + dataset['region'].loc[row] 
                          + '_' + dataset['SSP'].loc[row] 
                          + 'RCP ' + dataset['RCP'].loc[row])
            elif 'country' not in dataset.columns and 'region' not in dataset.columns:
                fig_name = str('world' + '_' 
                           + dataset['SSP'].loc[row] + 'RCP' 
                           + dataset['RCP'].loc[row] + title_str)
                plt.title(title_str + 'world' 
                      + '_' + dataset['SSP'].loc[row] 
                      + 'RCP' + dataset['RCP'].loc[row])
                
        elif 'SSP' and 'RCP' not in dataset.columns:
            if 'country' in dataset.columns:
                fig_name = str(dataset['country'].loc[row] + title_str)
                plt.title(title_str + dataset['country'].loc[row])
            elif 'country' not in dataset.columns and 'region' in dataset.columns:
                fig_name = str(dataset['region'].loc[row] + title_str)
                plt.title(title_str + dataset['region'].loc[row])
            elif 'country' not in dataset.columns and 'region' not in dataset.columns:
                fig_name = str('world' + title_str)
                plt.title(title_str + 'world')
        
        else:
            print('broken plotting & title function!')

        plt.legend(loc='center left', bbox_to_anchor=(1, .8), fancybox=True, ncol=1)
        plt.xlabel('Year')
        plt.ylabel('CO2 Emissions (Mt)')
        plt.xlim(2022,2100)
        
        plt.savefig(sub_folder + str.replace(fig_name, ' ','') + '.jpeg', bbox_inches='tight')
        plt.close()

# %%
if __name__ == "__main__":
    plot_data

# %%
# # this to help with debugging
# cntry_rgn_data = pd.read_csv('data/master.csv', index_col = 0)

# # remove the 8 remaining SSP 0 values 
# cntry_rgn_data = cntry_rgn_data.iloc[:-8,:]#.drop(columns = 'cred_scen_match')

# drop_cntry = cntry_rgn_data.drop(columns = 'country')
# rgn_data = drop_cntry.groupby(by = ['SSP', 'RCP', 'region']).sum().reset_index()
# world_totals = rgn_data.drop(columns = 'region').groupby(by = ['SSP', 'RCP']).sum().reset_index()

# # aggregate the data by region and country respectively, forming 2 expectations
# expectation_rgn = make_expectation_over_data(cntry_rgn_data, 'region').drop(columns = ['credence', 'posterior', 'p'])
# expectation_cntry = make_expectation_over_data(cntry_rgn_data, 'country').drop(columns = ['credence', 'posterior', 'p'])
# expectation_world = make_expectation_over_data(cntry_rgn_data, ['SSP', 'RCP']).drop(columns = ['credence', 'posterior', 'p'])

# %%
# create plots of emissions trajectories in each of the corresponding folders

# # plot the raw country and region level data
#plot_data(rgn_data, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', '../data/plots/rgn_emissions_rcp_ssp_plots/')
#plot_data(cntry_rgn_data, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', '../data/plots/cntry_emissions_rcp_ssp_plots/')

# # plot the data aggregated over the entire world, still raw
#plot_data(world_totals, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', '../data/plots/world_ssp_rcp_emissions/')

# # plot the expectation across countries and regions, respectively
#plot_data(expectation_rgn, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', '../data/plots/rgn_exp_plots/')
#plot_data(expectation_cntry, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', '../data/plots/cntry_exp_plots/')


