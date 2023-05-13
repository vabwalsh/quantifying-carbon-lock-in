# quantifying-carbon-lock-in
This repository stores the code, data, results, and figures used for my MSc thesis in Climate Economics at the University of Bern.

The aim of this project is to aggregate data on global emissions, producing roughly comprehensive country-level emissions trajectories through the end of the century. Overall, it contributes a methodology for quantifying the risks that existing and planned long-lived assets pose to emissions reduction goals by modeling future emissions with an emphasis on carbon lock-in. It accounts for currently existing and planned carbon-intensive infrastructure, respectively, and presents a methodology for roughly quantifying carbon lock-in. My findings align with the existing literature on carbon lock-in, indicating that the greatest threats to overshooting mitigation goals stem from existing and planned coal infrastructure and that emerging economies face the greatest relative risk of carbon lock-in. Estimates of future emissions produced are also compared to downscaled trajectories of emissions under particular Representative Concentration and Shared Socioeconomic Pathways (RCPs and SSPs) to assess their likelihood in light of current global development patterns. 

### Repository Structure
/quantifying-carbon-lock-in
main.py
/src
data_cleaning.py
data_analysis.py
/data
/plots
README.md

### File Descriptions
main.py: Executes the entire analysis pipeline.
src/data_cleaning.py & src/data_analysis.py: Host data processing and analysis functions.
data/: Stores raw and processed data.
plots/: Holds generated plots and figures. Each figure is named according to the analysis.

### Running the code
To generate the results of this analysis yourself, clone the repository, navigate to the project directory, and execute python main.py. This will overwrite the result files already in the directory by the same name. If you'd like to preserve these, make a copy of the /plots and /data directories and store them outside of the repository.

### Output
The analysis generates a series of plots and statistical outputs representing relationships between various factors and country-level carbon emissions. These are stored in the plots/ directory.

### Acknowledgements
The conceptual basis for the modeling of future emissions and initial identification of data sources is credited to Johannes Ackva. All code production and remaining analysis are my own. This thesis was supervised by Prof. Ralph Winkler in the Department of Economics at the University of Bern, Switzerland.

### Licensing
Please do not distribute this material for commercial purposes or profit. Some datasets in this analysis are distributed under a Creative Commons license.
