import pandas as pd
import plotly.graph_objects as go

# 1. Load the exported CSV and set the date as the index for time-series operations
# Force pandas to assign these column names, ignoring whatever is (or isn't) in row 1
df = pd.read_csv('data_pipeline/tmp/Result_2.csv', header=None, names=['date', 'non_null_count'])

# If your CSV actually did have a header row but it was named something else,
# you'll want to drop that first row so it doesn't break the datetime conversion:
# df = df.iloc[1:]

df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# 2. Pre-calculate the different resolutions
# We use .max() here. If a column has non-null data at any point during the
# month/year, it counts as "active" for that entire period.
res_raw = df['non_null_count']
res_monthly = df['non_null_count'].resample('ME').max()
res_quarterly = df['non_null_count'].resample('QE').max()
res_yearly = df['non_null_count'].resample('YE').max()

# 3. Initialize the Plotly Figure
fig = go.Figure()

# 4. Add a trace for each resolution
# Only the 'Raw' trace is set to visible by default
fig.add_trace(go.Scatter(x=res_raw.index, y=res_raw, mode='lines', name='Raw (Daily)', visible=True))
fig.add_trace(go.Scatter(x=res_monthly.index, y=res_monthly, mode='lines', name='Monthly', visible=False))
fig.add_trace(go.Scatter(x=res_quarterly.index, y=res_quarterly, mode='lines', name='Quarterly', visible=False))
fig.add_trace(go.Scatter(x=res_yearly.index, y=res_yearly, mode='lines', name='Yearly', visible=False))

# 5. Add the interactive resolution dropdown and time slider
fig.update_layout(
    title='Data Sparsity over Time (Resolution Control)',
    xaxis_title='Date',
    yaxis_title='Max Active Columns in Period',
    # Dropdown menu configuration
    updatemenus=[
        dict(
            active=0,
            buttons=list([
                dict(label="Raw (Daily)", method="update", args=[{"visible": [True, False, False, False]}]),
                dict(label="Monthly", method="update", args=[{"visible": [False, True, False, False]}]),
                dict(label="Quarterly", method="update", args=[{"visible": [False, False, True, False]}]),
                dict(label="Yearly", method="update", args=[{"visible": [False, False, False, True]}]),
            ]),
            direction="down",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )
    ],
    # Time slider and range selectors
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=5, label="Last 5y", step="year", stepmode="backward"),
                dict(count=10, label="Last 10y", step="year", stepmode="backward"),
                dict(count=20, label="Last 20y", step="year", stepmode="backward"),
                dict(step="all", label="All Data")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    ),
    template="plotly_dark"
)

# 6. Render the graph in your browser
fig.show()
