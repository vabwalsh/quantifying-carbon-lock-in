#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd


# In[ ]:


def clean_scen_CO2(scenario):
    
    # See data docs for Gütschow et al. 2020 here: https://zenodo.org/record/3638137#.Y-6V6OzMLdr
    # scenario should be the downscaled RCP/SSP data with standardized country names

    # The "source" column results in only using source values for 'SSPIAMBIE', meaning:
        # 1) "PMSSP" --> downscaled SSP IAM scenarios harmonized to and combined with historical data
        # 2) "B" --> emissions from bunkers have been removed before downscaling
        # 3) "IE" --> Convergence downscaling w/ exponential convergence of emissions intensities before becoming negative

    # The "entity" column describes different socioeconomic and demographic criteria, and different baskets of GHGs
    # I want to use the most comprehensive basket available, which is all the gases covered in the  Kyoto Protocol and AR4

    # Filter the scenario data for a single source and GHG basket
    # All units here are in GgCO2eq
    scen_subset = scenario[(scenario['entity'] == 'KYOTOGHGAR4') & (scenario['source'] == 'PMSSPBIE')]

    # To simplify the data calculate the cross-model mean for each country/RCP/SSP by averaging the 5 model values given
    # First separate the "scenario" column into it's component SSP, RCP, and model values
    scen_subset[['SSP','RCP','model']] = scen_subset.scenario.str.extract('(?P<ssp>.{4})(?P<rcp>.{2})(?P<model>.{5,})')

    # Then group the data by country/SSP/RCP values and calculate the mean for each of these groups across the models
    # & reset the index to convert the multi-index object to a regular df
    scen_model_means = scen_subset.groupby(by = ['country.name.en', 'SSP', 'RCP']).mean().reset_index()
    
    # Convert the data from GgCO2eq to MtCO2eq, (Megatonnes == Mt == million metric tons)
    scen_model_means.iloc[:,3:] = scen_model_means.iloc[:,3:] * .001

    # Put the correct decimal place in the RCP values (e.g. change from "19" to "1.9")
    scen_model_means["RCP"] = pd.to_numeric(scen_model_means["RCP"], errors='coerce') / 10
    scen_model_means["RCP"] = scen_model_means["RCP"].fillna('BL')
    
    # renaming the first col to country
    scen_model_means = scen_model_means.rename(columns={'country.name.en':'country'})
    
    scen_model_means.to_csv('data/scen_CO2_cntry.csv')
    
    return(scen_model_means)


# In[ ]:


if __name__ == "__main__":
    clean_scen_CO2()

