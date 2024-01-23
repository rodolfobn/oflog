import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
from flask import Flask
from dash.exceptions import PreventUpdate
import plotly.express as px

# Load data
df = pd.read_csv('adult_social_care.csv')

# Initialize the Dash app and Server
server = Flask(__name__)
app = dash.Dash(__name__, server=server)


    
# Define the app layout with navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link('Go to Regional Data', href='/'),
        html.Br(),
        dcc.Link('Go to Local Authority Lookup', href='/local-authority'),
        html.Br(),
        dcc.Link('Go to Regional Analysis', href='/regional-analysis')
    ]),
    html.Div(id='page-content')
])

# Define the index page layout
index_page = html.Div([
    dcc.Dropdown(
        id='region-dropdown',
        options=[{'label': i, 'value': i} for i in df['Region'].unique()],
        value=df['Region'].unique()[0]
    ),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
    )
])


# Define the local authority lookup page layout with additional options
local_authority_page = html.Div([
    html.H3("Local Authority Comparison"),
    dcc.Dropdown(
        id='local-authority-dropdown',
        options=[{'label': i, 'value': i} for i in df['Local authority name'].unique()],
        value=[df['Local authority name'].unique()[0]],
        multi=True  # Allow multiple selections
    ),
    dcc.Dropdown(
        id='measure-dropdown',
        options=[{'label': i, 'value': i} for i in df['Measure'].unique()],
        value=df['Measure'].unique()[0]
    ),
    dcc.Graph(id='comparison-chart')
])



# Callback to update regional table
@app.callback(
    Output('table', 'data'),
    [Input('region-dropdown', 'value')]
)
def update_table(selected_region):
    if selected_region is None:
        raise PreventUpdate
    filtered_df = df[df['Region'] == selected_region]
    return filtered_df.to_dict('records')

# Callback to update local authority information
@app.callback(
    Output('local-authority-info', 'children'),
    [Input('local-authority-dropdown', 'value')]
)
def update_local_authority_info(selected_local_authority):
    if selected_local_authority is None:
        raise PreventUpdate
    filtered_df = df[df['Local authority name'] == selected_local_authority]
    return html.Div([
        html.H4(f"Data for {selected_local_authority}"),
        dash_table.DataTable(
            data=filtered_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in filtered_df.columns]
        )
    ])

@app.callback(
    Output('comparison-chart', 'figure'),
    [Input('local-authority-dropdown', 'value'),
     Input('measure-dropdown', 'value')]
)
def update_comparison_chart(selected_local_authorities, selected_measure):
    if not selected_local_authorities or not selected_measure:
        raise PreventUpdate

    # Filter the DataFrame based on selections and explicitly copy it
    filtered_df = df[(df['Local authority name'].isin(selected_local_authorities)) & 
                     (df['Measure'] == selected_measure)].copy()

    # Convert 'Value' to numeric, coerce errors to NaN
    filtered_df['Value'] = pd.to_numeric(filtered_df['Value'], errors='coerce')

    # Drop rows where 'Value' or 'Financial year' is NaN after coercion
    filtered_df.dropna(subset=['Value', 'Financial year'], inplace=True)

    # Create a Plotly time-series chart
    fig = px.line(
        filtered_df,
        x='Financial year',
        y='Value',
        color='Local authority name',
        title=f"Comparison of {selected_measure} Over Time",
        labels={'Value': selected_measure}  # Update y-axis label
    )

    # Update layout
    fig.update_layout(
        xaxis_title="Financial Year", 
        yaxis_title=selected_measure,
        xaxis=dict(autorange='reversed')  # Reverse the x-axis
    )

    return fig

# Callback to update page content based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/local-authority':
        return local_authority_page
    elif pathname == '/regional-analysis':
        return regional_analysis_page
    else:
        return index_page

# Define the regional analysis page layout with additional year selection
regional_analysis_page = html.Div([
    html.H3("Regional Analysis"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': i, 'value': i} for i in df['Financial year'].unique()],
        value=df['Financial year'].unique()[0]
    ),
    dcc.Dropdown(
        id='metric-dropdown',
        options=[{'label': i, 'value': i} for i in df['Measure'].unique()],
        value=df['Measure'].unique()[0]
    ),
    dcc.Graph(id='regional-bar-chart')
])

# Callback to update the regional bar chart based on selected year and metric
@app.callback(
    Output('regional-bar-chart', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_regional_bar_chart(selected_year, selected_metric):
    if not selected_year or not selected_metric:
        raise PreventUpdate

    # Filter the DataFrame based on the selected year and metric
    filtered_df = df[(df['Financial year'] == selected_year) & (df['Measure'] == selected_metric)]

    # Convert 'Value' to numeric, if not already
    filtered_df['Value'] = pd.to_numeric(filtered_df['Value'], errors='coerce')

    # Group by region and calculate average
    avg_df = filtered_df.groupby('Region')['Value'].mean().reset_index()

    # Create a Plotly bar chart
    fig = px.bar(
        avg_df,
        x='Region',
        y='Value',
        title=f"Average {selected_metric} in {selected_year} by Region"
    )

    return fig









# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
