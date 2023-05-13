# %%
import pandas as pd

# %%
def clean_tong(tong_cntry_fix):

    # modify the data types so country names can be grouped by, and so years can be numerically filtered
    tong_cntry_fix['country.name.en'] = tong_cntry_fix['country.name.en'].astype(str)
    tong_cntry_fix['Year'] = tong_cntry_fix['Year'].astype(int)
    tong_cntry_fix = tong_cntry_fix[tong_cntry_fix['Year'] > 2020] # filters for 2021 onward, which is when project started. Essentially ignoring historic data from Tong et al
    tong_cntry_fix['Year'] = tong_cntry_fix['Year'].astype(str) # back to strings in order to group in next line
    
    # this data is in Gt, so need to be modified and converted to Mt
    tong_cntry_fix['Yearly Emissions (MtCO2) - derived'] =  tong_cntry_fix['Yearly Emissions (GtCO2) - derived'] * 1000

    # to test: tong_cntry_fix = pd.read_csv('data/tong_cntry_fix.csv')
    df = tong_cntry_fix[['country.name.en', 'Year', 'Sector','Yearly Emissions (MtCO2) - derived']]

    # Pivot the data
    pivoted_data = df.pivot_table(index=["country.name.en"], columns=["Sector", "Year"], values="Yearly Emissions (MtCO2) - derived").reset_index()

    # name the columns properly
    pivoted_data.columns = [".".join(str(level) for level in col).strip() if not isinstance(col, str) else col for col in pivoted_data.columns]

    # rename country column to 'country'
    pivoted_data = pivoted_data.rename(columns = {'country.name.en.':'country'})

    # write the cleaned plotting formatted data to a csv
    pivoted_data.to_csv('data/tong_country_sector_CO2.csv')

    # test that this function worked
    print('Tong data pivoted and written to a panel data CSV <tong_country_sector_CO2>')    
    
    return(pivoted_data)

# %%
if __name__ == "__main__":
    clean_tong


