#### generate interactive plots of 2D and 3D embeddings highlighting categorical and numerical metadata ####

#### libraries
# general
import os
import numpy as np
import pandas as pd
# plotting
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# helper function for button to determine colors of categorical metadata
def config_button_cat(fig, data, cat_var):
    
    unique_vals = data[cat_var].unique()
    unique_vals = unique_vals[pd.notna(unique_vals)]
    
    if len(unique_vals)<10:
        cm = plt.get_cmap('tab10')
    elif len(unique_vals)<20:
        cm = plt.get_cmap('tab20')
    else:
        cm = plt.get_cmap('gist_ncar')

#     cm = plt.get_cmap('gist_ncar')
    colors = [cm(1.*i/(len(unique_vals)+1)) for i in range(len(unique_vals)+1)]
#     colors = [cm(1.*i/(len(unique_vals))) for i in range(len(unique_vals))]
    color_map = dict(zip(unique_vals, colors))
    
    tmp_idx = list(data.columns).index(cat_var)-dimensions
    data_colors = [color_map[datapoint[tmp_idx]] for datapoint in fig["data"][0]["customdata"]]
    return [data_colors]

# helper function to put both plotly figures into the same HTML next to each other (independently)
def figures_to_html(figs, filename="dashboard.html"):
    with open(filename, 'w') as dashboard:
        dashboard.write("<html><head></head><body>" + "\n")
        dashboard.write("<div style='overflow:auto;'>" + "\n")
        for fig in figs:
            dashboard.write("<div style='float:left;'>" + "\n")
            inner_html = fig.to_html().split('<body>')[1].split('</body>')[0]
            dashboard.write(inner_html)
            dashboard.write("</div>" + "\n")
        dashboard.write("</div>" + "\n")
        dashboard.write("</body></html>" + "\n")

#### configurations

# inputs
data_path = snakemake.input["dimred_data"]
metadata_path = snakemake.input["metadata"]
metadata_features_path = snakemake.input["metadata_features"]

if "metadata_clusterings" in snakemake.input.keys():
    metadata_clusterings_path = snakemake.input["metadata_clusterings"]
else:
    metadata_clusterings_path = ""

# outputs
plot_path = snakemake.output["plot"]

# parameters
dimensions = int(snakemake.params["n_components"]) #2 
point_size = 2*snakemake.params["size"] if dimensions==3 else 5*snakemake.params["size"] # 2
point_alpha = snakemake.params["alpha"] #1

width = 750
height = 750

### load data
data = pd.read_csv(data_path, index_col=0)
metadata = pd.read_csv(metadata_path, index_col=0)

# fix metadata indices if they do not agree with data as they come from outside the workflow (e.g., R)
if not(all(data.index==metadata.index)):
    #metadata.index = metadata.index.map(str)
    if metadata.index.inferred_type=='string':
        metadata.index = [idx.replace('-','.') for idx in metadata.index]

metadata_features = pd.read_csv(metadata_features_path, index_col=0)

data_all = pd.concat([data.iloc[:,:dimensions], metadata, metadata_features], axis=1)
data_all = data_all.fillna('')

# sort metadata by data type 
meta_num = list()
meta_cat = list()
for variable in data_all.columns[dimensions:]:
    unique_vals = list(data_all[variable].unique())
    #unique_vals = unique_vals[~np.isnan(unique_vals)] #unique_vals[pd.notna(unique_vals)]
    
    # check if integer AND less than 25 unique values -> categorical metadata
    if all([isinstance(i, (int, np.int64)) for i in unique_vals]) and len(unique_vals)<25:
        #data_all[variable] = data_all[variable].values.astype(str)
        meta_cat.append(variable)
        continue
    
    if all([isinstance(i, (str, bool, np.bool_)) for i in unique_vals]):
#         print('discrete variable ', variable)
        meta_cat.append(variable)
    
    elif all([isinstance(i, (int, float, np.int64)) for i in unique_vals]):
#         print('continous variable ', variable)
        meta_num.append(variable)
        
    else:
        print("variable type not-detected for {}".format(variable))

# if clustering results are provided add them as categorical data
if metadata_clusterings_path!="":
    metadata_clusterings = pd.read_csv(metadata_clusterings_path, index_col=0)
    data_all = pd.concat([data_all, metadata_clusterings], axis=1)
    meta_cat = meta_cat + metadata_clusterings.columns.tolist()
        
# plotting the interactive scatter plot
#in 2D
if dimensions==2:
    fig_num = px.scatter(data_all,
                     x=data_all.columns[0],
                     y=data_all.columns[1],
                     hover_data=meta_cat,
                     custom_data=list(data_all.columns)[dimensions:],
                     width=width,
                     height=height,
                         opacity=point_alpha,
                         title="Numerical Metadata",
                    )
    fig_cat = px.scatter(data_all,
                     x=data_all.columns[0],
                     y=data_all.columns[1],
                     hover_data=meta_cat,
                     custom_data=list(data_all.columns)[dimensions:],
                     width=width,
                     height=height,
                         opacity=point_alpha,
                         title="Categorical Metadata",
                         render_mode = "webgl" # required for less than 1000 datapoints, otherwise metadata selection does not work
                    )
# in 3D
elif dimensions==3:
    fig_num = px.scatter_3d(data_all,
                        x=data_all.columns[0],
                        y=data_all.columns[1],
                        z=data_all.columns[2],
                        hover_data=meta_cat,
                        custom_data=list(data_all.columns)[dimensions:],
                        width=width,
                        height=height,
                        opacity=point_alpha,
                            title="Numerical Metadata",
                       )
    fig_cat = px.scatter_3d(data_all,
                        x=data_all.columns[0],
                        y=data_all.columns[1],
                        z=data_all.columns[2],
                        hover_data=meta_cat,
                        custom_data=list(data_all.columns)[dimensions:],
                        width=width,
                        height=height,
                        opacity=point_alpha,
                            title="Categorical Metadata",
                       )

# set point size 
fig_num.update_traces(marker=dict(size=point_size))
fig_cat.update_traces(marker=dict(size=point_size))

# save the plot wihtout buttons or metadata
# fig.write_html(plot_path)

# save the plot
# fig.write_html(plot_path)


# button for numerical metadata
fig_num.update_layout(
    updatemenus=[
        {
            "buttons": [
                {
                    "label": variable,
                    "method": "update",
                    "args": [
                        {'legendgroup': '',
                         'marker': {'color': data_all[variable].to_numpy(),
                                    'coloraxis': 'coloraxis',
                                    'symbol': 'circle',
                                    'size':point_size},
                         'mode': 'markers',
                         'name': '',
                         'showlegend': False,
                        } 
                    ],
                } for variable in meta_num
            ],
            "direction": "down",
            "showactive": True,
            "x": 1,
            "xanchor": "right",
            "y": 1,
            "yanchor": "top"
        },
    ],
)

# save the plot
# fig.write_html(plot_path)

# button for catergorical metadata
fig_cat.update_layout(
    updatemenus=[
        {
            "buttons": [
                {
                    "label": variable,
                    "method": "update",
                    "args": [
                        {"marker.color": config_button_cat(fig_cat, data_all, variable),
                        'showlegend': False, #[data_all.shape[0]*[True]],
                        'legendgroup': '',#data_all[variable],
                        'name': '',#data_all[variable]
                        }
                    ],
                } for variable in meta_cat
            ],
            "direction": "down",
            "showactive": True,
            "x": 1,
            "xanchor": "right",
            "y": 1,
            "yanchor": "top"
        },
    ],
)

# save the plot
# fig.write_html(plot_path)

# save both figures in one HTML file
figures_to_html([fig_cat, fig_num], plot_path)
