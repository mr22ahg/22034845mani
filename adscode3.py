import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

renewable_electricity_output = pd.read_csv('API_EG.ELC.RNEW.ZS_DS2_en_csv_v2_5359597.csv', skiprows=4)
access_to_electricity = pd.read_csv('API_EG.ELC.ACCS.ZS_DS2_en_csv_v2_5358776.csv', skiprows=4)

def power_function(x, a, b):
    return a * x**b

def sigmoid_function(x, a, b):
    return a / (1 + np.exp(-b * x))

"""the code below wa predefined in errors.py and clustertools.py as provided"""

def map_corr(df, size=6):
    """Function creates heatmap of correlation matrix for each pair of 
    columns in the dataframe.

    Input:
        df: pandas DataFrame
        size: vertical and horizontal size of the plot (in inch)
        
    The function does not have a plt.show() at the end so that the user 
    can save the figure.
    """

    import matplotlib.pyplot as plt  # ensure pyplot imported

    corr = df.corr()
    plt.figure(figsize=(size, size))
    plt.matshow(corr, cmap='coolwarm')
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
    plt.yticks(range(len(corr.columns)), corr.columns)
    plt.colorbar()


def scaler(df):
    """ Expects a dataframe and normalises all 
        columns to the 0-1 range. It also returns 
        dataframes with minimum and maximum for
        transforming the cluster centres"""

    df_min = df.min()
    df_max = df.max()
    df_normalized = (df - df_min) / (df_max - df_min)

    return (df_normalized), df_min, df_max


def backscale(arr, df_min, df_max):
    """ Expects an array of normalised cluster centres and scales
        it back. Returns numpy array.  """

    minima = df_min.to_numpy()
    maxima = df_max.to_numpy()

    for i in range(len(minima)):
        arr[:, i] = arr[:, i] * (maxima[i] - minima[i]) + minima[i]

    return arr


def get_diff_entries(df1, df2, column):
    """ Compares the values of column in df1 and the column with the same 
    name in df2. A list of mismatching entries is returned. The list will be
    empty if all entries match. """

    df_out = pd.merge(df1, df2, on=column, how="outer")
    print("total entries", len(df_out))
    df_in = pd.merge(df1, df2, on=column, how="inner")
    print("entries in common", len(df_in))
    df_in["exists"] = "Y"

    df_merge = pd.merge(df_out, df_in, on=column, how="outer")
    df_diff = df_merge[(df_merge["exists"] != "Y")]
    diff_list = df_diff[column].to_list()

    return diff_list


""" Module errors. It provides the function err_ranges which calculates upper
and lower limits of the confidence interval. """

import numpy as np


def err_ranges(x, func, param, sigma):
    """
    Calculates the upper and lower limits for the function, parameters and
    sigmas for single value or array x. Functions values are calculated for 
    all combinations of +/- sigma and the minimum and maximum is determined.
    Can be used for all number of parameters and sigmas >=1.
    
    This routine can be used in assignment programs.
    """

    import itertools as iter
    
    # initiate arrays for lower and upper limits
    lower = func(x, *param)
    upper = lower
    
    uplow = []   # list to hold upper and lower limits for parameters
    for p, s in zip(param, sigma):
        pmin = p - s
        pmax = p + s
        uplow.append((pmin, pmax))
        
    pmix = list(iter.product(*uplow))
    
    for p in pmix:
        y = func(x, *p)
        lower = np.minimum(lower, y)
        upper = np.maximum(upper, y)
        
    return lower, upper

# Rename the dataframes
renewable_electricity_output.rename(columns={'Country Name': 'Country'}, inplace=True)
access_to_electricity.rename(columns={'Country Name': 'Country'}, inplace=True)

# Select relevant columns for clustering
renewable_electricity_data = renewable_electricity_output[['Country', '2018']]
access_to_electricity_data = access_to_electricity[['Country', '2018']]

# Merge the dataframes
merged_data = pd.merge(renewable_electricity_data, access_to_electricity_data, on='Country', suffixes=('_renewable', '_access'))
# Fill NaN values with zeros
merged_data.fillna(0, inplace=True)

# Calculate column means
column_means = merged_data.mean()

# Fill remaining NaN values with column means
merged_data.fillna(column_means, inplace=True)


# Normalize the data for clustering
normalized_data, min_values, max_values = scaler(merged_data[['2018_renewable', '2018_access']])

# Perform clustering
kmeans = KMeans(n_clusters=3, random_state=42)
cluster_labels = kmeans.fit_predict(normalized_data)

# Add cluster labels to the dataframe
merged_data['Cluster'] = cluster_labels

# Plot the clusters
#plt.scatter(merged_data['2018_renewable'], merged_data['2018_access'], c=merged_data['Cluster'])
plt.scatter(x, y, c=merged_data['Cluster'])
plt.xlabel('Renewable Electricity Output (% of total electricity output)')
plt.ylabel('Access to Electricity (% of population)')
plt.title('Clustering of Countries')
plt.show()

# Extract the relevant columns
x = merged_data['2018_renewable']
y = merged_data['2018_access']

# Generate correlation heatmap
map_corr(merged_data[['2018_renewable','2018_access']])

# Fit the power function
params_power, _ = curve_fit(power_function, x, y)

# Generate predictions for power function
x_pred_power = np.linspace(min(x), max(x), 100)
y_pred_power = power_function(x_pred_power, *params_power)

# Calculate confidence intervals for power function
lower_power, upper_power = err_ranges(x_pred_power, power_function, params_power, [0.1, 0.2])

# Plot the power function with confidence intervals
plt.scatter(x, y, label='Data')
plt.plot(x_pred_power, y_pred_power, color='red', label='Power Function')
plt.fill_between(x_pred_power, lower_power, upper_power, color='lightgray', alpha=0.3, label='Confidence Interval')
plt.xlabel('Renewable Electricity Output (% of total electricity output)')
plt.ylabel('Access to Electricity (% of population)')
plt.title('Power Function Fit with Confidence Interval')
plt.legend()
plt.show()

# Fit the sigmoid function
params_sigmoid, _ = curve_fit(sigmoid_function, x, y)

# Generate predictions for sigmoid function
x_pred_sigmoid = np.linspace(min(x), max(x), 100)
y_pred_sigmoid = sigmoid_function(x_pred_sigmoid, *params_sigmoid)

# Calculate confidence intervals for sigmoid function
lower_sigmoid, upper_sigmoid = err_ranges(x_pred_sigmoid, sigmoid_function, params_sigmoid, [0.1, 0.2])

# Plot the sigmoid function with confidence intervals
plt.scatter(x, y, label='Data')
plt.plot(x_pred_sigmoid, y_pred_sigmoid, color='blue', label='Sigmoid Function')
plt.fill_between(x_pred_sigmoid, lower_sigmoid, upper_sigmoid, color='lightgray', alpha=0.3, label='Confidence Interval')
plt.xlabel('Renewable Electricity Output (% of total electricity output)')
plt.ylabel('Access to Electricity (% of population)')
plt.title('Sigmoid Function Fit with Confidence Interval')
plt.legend()
plt.show()

# Backscale cluster centers
cluster_centers = backscale(kmeans.cluster_centers_, min_values, max_values)
print("Cluster Centers (Original Scale):\n", cluster_centers)

# Check for mismatching entries
diff_list = get_diff_entries(renewable_electricity_output, access_to_electricity, 'Country')
print("Mismatching Entries:\n", diff_list)