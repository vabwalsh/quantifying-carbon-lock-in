#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# import libraries used in in this file, specialized libraries are included in functions
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# import the data operations from their respective files
from countrynamefix import countrynamefix
from rcp_ssp import clean_scen_CO2
from tong import clean_tong
from clean_gem import format_GEM
from aggregate import aggregate_to_master
from affectability import make_affectability_data
from expectations import make_expectation_over_data
from plotting import plot_data


# In[ ]:


tong_cntry_fix, scen_cntry_fix, coal_cntry_fix, gas_cntry_fix, steel_cntry_fix = countrynamefix()
scen_clean = clean_scen_CO2(scen_cntry_fix)
tong_clean = clean_tong(tong_cntry_fix)
coal_plants_clean, gas_plants_clean, steel_plants_clean = format_GEM(coal_cntry_fix, gas_cntry_fix, steel_cntry_fix)
cntry_rgn_data = aggregate_to_master(coal_plants_clean, gas_plants_clean, steel_plants_clean, tong_clean, scen_clean)


# In[ ]:


# remove the 8 remaining SSP 0 values 
# don't remove cred_scen_match, this is necessary for calculating the expectation
cntry_rgn_data = cntry_rgn_data.iloc[:-8,:]#.drop(columns = 'cred_scen_match')

# make the rgn and world versions
drop_cntry = cntry_rgn_data.drop(columns = 'country')
rgn_data = drop_cntry.groupby(by = ['SSP', 'RCP', 'region']).sum().reset_index()
world_totals = rgn_data.drop(columns = 'region').groupby(by = ['SSP', 'RCP']).sum().reset_index()

# aggregate the data by region and country respectively, forming 2 expectations
expectation_rgn = make_expectation_over_data(cntry_rgn_data, 'region').drop(columns = ['credence', 'posterior', 'p'])
expectation_cntry = make_expectation_over_data(cntry_rgn_data, 'country').drop(columns = ['credence', 'posterior', 'p'])
expectation_world = make_expectation_over_data(cntry_rgn_data, ['SSP', 'RCP']).drop(columns = ['credence', 'posterior', 'p'])


# In[ ]:


# make the "affectable" version of the emissions, and fix formatting 
aff_emits = make_affectability_data(cntry_rgn_data)

# make the rgn and world versions
aff_drop_cntry = aff_emits.drop(columns = 'country')
aff_rgn_data = aff_drop_cntry.groupby(by = ['SSP', 'RCP', 'region']).sum().reset_index()
aff_world_totals = aff_rgn_data.drop(columns = 'region').groupby(by = ['SSP', 'RCP']).sum().reset_index()

# as before, aggregate the data by region and country respectively, forming 2 expectations
aff_expectation_rgn = make_expectation_over_data(aff_emits, 'region')
aff_expectation_cntry = make_expectation_over_data(aff_emits, 'country')
aff_expectation_world = make_expectation_over_data(aff_emits, ['SSP', 'RCP']).drop(columns = ['credence', 'posterior', 'p'])


# In[ ]:


cntry_rgn_data[['country','region','SSP','RCP']] = cntry_rgn_data[['country','region','SSP','RCP']].astype(str)
rgn_data[['SSP','RCP','region']] = rgn_data[['SSP','RCP','region']].astype(str)
world_totals[['SSP','RCP']] = world_totals[['SSP','RCP']].astype(str)


# In[ ]:


aff_emits[['country','region','SSP','RCP']] = aff_emits[['country','region','SSP','RCP']].astype(str)
aff_rgn_data[['SSP','RCP','region']] = aff_rgn_data[['SSP','RCP','region']].astype(str)
aff_world_totals[['SSP','RCP']] = aff_world_totals[['SSP','RCP']].astype(str)


# In[ ]:


# create plots of emissions trajectories in each of the corresponding folders

# plot the raw country and region level data
plot_data(rgn_data, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', 'data/plots/rgn_emissions_rcp_ssp_plots/')
plot_data(cntry_rgn_data, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', 'data/plots/cntry_emissions_rcp_ssp_plots/')

# # plot the data aggregated over the entire world, still raw
plot_data(world_totals, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_', 'data/plots/world_ssp_rcp_emissions/')

# # plot the expectation across countries and regions, respectively
plot_data(expectation_rgn, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', 'data/plots/rgn_exp_plots/')
plot_data(expectation_cntry, 'raw', 'Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', 'data/plots/cntry_exp_plots/')


# In[ ]:


# # plot the raw country and region level data
plot_data(aff_rgn_data, 'affectable', 'Affectable_Planned_Committed_and_Considered_Emissions_till_2100_', 'data/plots/aff_rgn_emissions_rcp_ssp_plots/')
plot_data(aff_emits, 'affectable', 'Affectable_Planned_Committed_and_Considered_Emissions_till_2100_', 'data/plots/aff_cntry_emissions_rcp_ssp_plots/')

# plot the data aggregated over the entire world, still raw
plot_data(aff_world_totals, 'affectable', 'Planned, Committed, and Considered Emissions till 2100 ', 'data/plots/aff_world_ssp_rcp_emissions/')

# plot the expectation across countries and regions, respectively
plot_data(aff_expectation_rgn, 'affectable', 'Affectable_Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', 'data/plots/aff_rgn_exp_plots/')
plot_data(aff_expectation_cntry, 'affectable', 'Affectable_Planned_Committed_and_Considered_Emissions_till_2100_in_expectation', 'data/plots/aff_cntry_exp_plots/')


# In[ ]:


# from output_analysis import check_emits_in_yr
# check_emits_in_yr(2021, coal_plants_clean, gas_plants_clean, steel_plants_clean, regions)

