
import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV
import os
from statsmodels.nonparametric.kernel_density import KDEMultivariate
import joblib
# sakha_json_path = '../regions_fire/Sakha.json'
# with open(sakha_json_path, 'r', encoding='utf-8') as f:
#     data = json.load(f)
# coords = np.vstack([pts for pts in data['fires'].values()])
# sample_size = 5000
# if coords.shape[0] > sample_size:
#     np.random.seed(5230)  # Для воспроизводимости 5230 374
#     idx = np.random.choice(coords.shape[0], size=sample_size, replace=False)
#     coords_sample = coords[idx]
# else:
#     coords_sample = coords
# #
# kde = KDEMultivariate(data=coords_sample, var_type='cc', bw='sj')
# bandwidths = kde.bw
# avg_bandwidth = np.mean(bandwidths)
# # 
# print(f"Шезера-Джонса: lon = {bandwidths[0]:.5f}, lat = {bandwidths[1]:.5f}")
# print(f"Среднее значение h: {avg_bandwidth:.5f}")
# ИТОГО h = 0.07101


sakha_json_path = '../regions_fire/Sakha.json'
with open(sakha_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

coords = []
for pts in data['fires'].values():
    coords.extend(pts)
coords = np.array(coords)

# h = 0.07101
# print(f"Используется bandwidth (h) = {h:.3f}")

# kde = KernelDensity(bandwidth=h, kernel='gaussian')
# kde.fit(coords)


output_dir = '../regions_fire'
# os.makedirs(output_dir, exist_ok=True)
# model_path = os.path.join(output_dir, 'Sakha_kde_model.joblib')
# joblib.dump(kde, model_path)
# print(f"KDE модель сохранена: {model_path}")


kde = joblib.load('../regions_fire/Sakha_kde_model.joblib')


num_pts = 200
lon_min, lat_min = coords.min(axis=0) - 0.5
lon_max, lat_max = coords.max(axis=0) + 0.5
X, Y = np.meshgrid(
    np.linspace(lon_min, lon_max, num_pts),
    np.linspace(lat_min, lat_max, num_pts)
)
grid_pts = np.vstack([X.ravel(), Y.ravel()]).T

Z = np.exp(kde.score_samples(grid_pts)).reshape(X.shape)

colormaps = ['hot', 'magma', 'inferno']

scatter_size = 1.5

# for cmap in colormaps:
#     plt.figure(figsize=(10, 8))
#     levels = np.linspace(Z.min(), Z.max(), 15)
#     cf = plt.contourf(X, Y, Z, levels=levels, alpha=0.7, cmap=cmap)
#     plt.scatter(coords[:, 0], coords[:, 1], s=scatter_size, color='black', alpha=0.15)
#     plt.colorbar(cf, label='Density')
#     plt.title(f'Sakha KDE Heatmap (bandwidth h, cmap="{cmap}")')
#     plt.xlabel('Longitude')
#     plt.ylabel('Latitude')

#     out_path = os.path.join(output_dir, f'Sakha-heatmap-{cmap}.png')
#     plt.savefig(out_path, dpi=300, bbox_inches='tight')
#     plt.close()
#     print(f"Heatmap сохранён: {out_path}")
lon = coords[:, 0]
lat = coords[:, 1]

def plot_1d_kde_hist(data, label, output_dir):
    x_min, x_max = data.min() - 0.5, data.max() + 0.5
    x_grid = np.linspace(x_min, x_max, 1000)[:, None]
    
    kde = KernelDensity(kernel='gaussian', bandwidth=0.1)
    kde.fit(data[:, None])
    log_density = kde.score_samples(x_grid)
    density = np.exp(log_density)
    
    plt.figure(figsize=(8, 4))
    plt.hist(data, bins=50, density=True, alpha=0.4, color='gray', label='Histogram')
    plt.plot(x_grid[:, 0], density, color='blue', lw=2, label='KDE')
    plt.title(f'Distribution of {label}')
    plt.xlabel(label)
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(f"{output_dir}/{label}_distribution.png", dpi=300)
    plt.close()
    print(f"{label} distribution plot saved.")

output_dir = '../regions_fire'
plot_1d_kde_hist(lon, 'Longitude', output_dir)
plot_1d_kde_hist(lat, 'Latitude', output_dir)