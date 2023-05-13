# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D

# %%
# import plottable version of the data
master = pd.read_csv('../data/master.csv', index_col= 0)
master = master[(master['RCP'] != str(0)) & (master['SSP'] != str(0))]

years = np.arange(2021, 2101)

# %%
# find the average distance between the scenario and the consid+commit lines (this is expectable)
# discount this distance by the discount rate
# make a column w one value per row that holds the "average distance" between the scenario and the consid+commit lines

def find_closest_scen(df):
    def calc_scen_distance(row):
        differences = []

        for yr in range(2021,2101):
            expectable = row[f"expectable.{yr}"]
            differences.append(np.abs(expectable))

        # may want to adapt discount array to be stepwise
        rho = 0.99
        discount_arr = np.array([rho**i for i in np.arange(80)])
        # print(discount_arr)
        distance = np.sum(discount_arr * np.sqrt(np.array(differences) ** 2))
        # print(distance)
        return distance

    # Calculate the distance for the current year and store it in a new column
    df['distance'] = df.apply(calc_scen_distance, axis=1)

    return df

# %%
def select_min_rtp_distance_rows(df):
    # Find the index of the row with the smallest avg.rtp.distance for each country
    min_rtp_distance_idx = df.groupby('country')['distance'].idxmin()

    # Select the rows with the smallest avg.rtp.distance for each country
    min_rtp_distance_df = df.loc[min_rtp_distance_idx]

    return min_rtp_distance_df

# %%
def create_shaded_region(ax, lines, facecolor='lightgrey', alpha=0.5):
    if len(lines) < 2:
        return

    min_y = np.min([line.get_ydata() for line in lines], axis=0)
    max_y = np.max([line.get_ydata() for line in lines], axis=0)

    ax.fill_between(years, min_y, max_y, facecolor=facecolor, alpha=alpha)

# %%
# def find_line(lines, rcp, ssp, country_df, scenario_cols):
#     rcp_ssp_emissions = country_df[(country_df['RCP'] == rcp) & (country_df['SSP'] == ssp)][scenario_cols].values.flatten()
#     for line in lines:
#         if np.all(line.get_ydata() == rcp_ssp_emissions):
#             return line
#     return None

# %%
def label_line(ax, line, label, x_pos, y_offset=0, x_offset=0, fontsize=9, color=None):
    if color is None:
        color = line.get_color()

    y_pos = np.interp(x_pos, years, line.get_ydata())
    ax.annotate(label, xy=(x_pos, y_pos), xytext=(x_pos + x_offset, y_pos + y_offset), annotation_clip=False,
                fontsize=fontsize, color=color,
                bbox=dict(boxstyle="round,pad=0.3", edgecolor=color, facecolor=(1, 1, 1, 0.7)),
                arrowprops=dict(arrowstyle="wedge,tail_width=0.7", alpha=0.7, edgecolor=color, facecolor=color))

# %%
def plot_possible_emits(master, closest_ssp_rcp):

    # for unique country in the data
    for country in master['country'].unique():
        # make a df from that country subset
        country_df = master[master['country'] == country]
        # extract the scenario columns 
        scenario_cols = [col for col in master if len(col) == 4]

        # define the unique scenarios to plot over, do this per country so that ..?
        scenarios = master[['RCP', 'SSP']].drop_duplicates()
        
        # define a figure with three subplots for each country, give the names and shading color for each subplot
        fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(10, 12), sharex=True)
        titles = ['Emissions Trajectories by SSP-RCP Permutation', 'Emissions Trajectories by SSP', 'Emissions Trajectories by RCP']
        facecolors = ['grey', 'red', 'blue']

        # create a list of lists to hold the lines for each subplot
        lines_list = [[], [], []]
        
        for i, ax in enumerate(axs):
            ax.set_title(titles[i])
            ax.set_ylabel('MtCO2')
            ax.set_xlabel('Year')
            
            if i == 0:
                for rcp, ssp in scenarios[['RCP', 'SSP']].values:
                    scenario_df = country_df[(country_df['RCP'] == rcp) & (country_df['SSP'] == ssp)]
                    scenario_name = f'{rcp}, {ssp}'
                    scenario_emissions = scenario_df[scenario_cols].values.flatten()
                    line, = ax.plot(years, scenario_emissions, color='grey', label=scenario_name)
                    lines_list[i].append(line)

            elif i == 1:
                ssp_emissions_dict = {ssp: country_df[country_df['SSP'] == ssp][scenario_cols].mean(axis=0) for ssp in scenarios['SSP'].values}
                for ssp, ssp_emissions in ssp_emissions_dict.items():
                    line, = ax.plot(years, ssp_emissions, color='grey', label=ssp, marker='None')
                    lines_list[i].append(line)

            else:
                rcp_emissions_dict = {rcp: country_df[country_df['RCP'] == rcp][scenario_cols].mean(axis=0) for rcp in scenarios['RCP'].values}
                for rcp, rcp_emissions in rcp_emissions_dict.items():
                    line, = ax.plot(years, rcp_emissions, color='grey', label=rcp, marker='None')
                    lines_list[i].append(line) 

            create_shaded_region(ax, lines_list[i], facecolor=facecolors[i])

            # Assuming highlight_df contains the RCP and SSP combination you want to highlight
            highlight_rcp = closest_ssp_rcp[closest_ssp_rcp['country'] == country]['RCP'].values[0]
            highlight_ssp = closest_ssp_rcp[closest_ssp_rcp['country'] == country]['SSP'].values[0]

            # Use the find_line function to find the line corresponding to the RCP and SSP combination
            highlight_line = find_line(lines_list[i], highlight_rcp, highlight_ssp, country_df, scenario_cols)

            label_text = f'Closest RCP-SSP: {highlight_rcp}-{highlight_ssp}'
            x_pos = 2100  # You can adjust this value to place the label at a different position on the x-axis
            y_offset = 1  # Adjust the y_offset value to control the vertical position of the label relative to the line
            x_offset = 1  # Adjust the x_offset value to control the horizontal position of the label relative to the line
            label_line(ax, highlight_line, label_text, x_pos, y_offset, x_offset)


        plt.xlim(2021, 2100)
        axs[0].legend(labels=['considered+committed emissions'], loc = 2)
        axs[1].legend(labels=['considered+committed emissions'], loc = 2)
        axs[2].legend(labels=['considered+committed emissions'], loc = 2)
        fig.suptitle(country)
        plt.tight_layout()
        fig.savefig('../output_analysis/scen_comp_w_rtp/' + country + '.png')
        plt.close(fig)

# %%
master_w_distance = find_closest_scen(master)
closest_ssp_rcp = select_min_rtp_distance_rows(master_w_distance).reset_index().drop(columns = 'index')#[['country', 'region', 'RCP', 'SSP', 'distance']]

# %%
plot_possible_emits(master, closest_ssp_rcp)

# %%
closest_ssp_rcp

# %%


# %%



