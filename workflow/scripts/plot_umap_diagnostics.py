#### generate diagnostic plots for Uniform Manifold Approximation and Projection (UMAP) ####

#### libraries
# general
import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
# dimensionality reduction
import umap
import umap.plot

#### configurations

# ipnuts
object_path = snakemake.input["umap_object"]

# outputs
plot_diagnostics_path = snakemake.output["diagnostics_plot"]

### load data
with open(object_path, 'rb') as f:
    umap_obj = pickle.load(f)
    
### generate & save UMAP specific diagnostic plots

fig_diag, ax_diag = umap.plot.plt.subplots(2, 2, figsize=(12,12))
umap.plot.diagnostic(umap_obj, diagnostic_type='pca', ax=ax_diag[0,0])
umap.plot.diagnostic(umap_obj, diagnostic_type='vq', ax=ax_diag[0,1])
umap.plot.diagnostic(umap_obj, diagnostic_type='local_dim', ax=ax_diag[1,0])
umap.plot.diagnostic(umap_obj, diagnostic_type='neighborhood', nhood_size=min(umap_obj.n_neighbors, 15), ax=ax_diag[1,1])
fig_diag.savefig(plot_diagnostics_path)
