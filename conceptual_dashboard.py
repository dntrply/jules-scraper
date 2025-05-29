import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import os

# --- App Initialization ---
app = dash.Dash(__name__)
app.title = "Indian Government Event Dashboard"

# --- Data Loading ---
EXPECTED_COLUMNS = [
    'event_title', 'event_date_iso', 'event_date_str', 
    'is_attendable_event_llm', 'cost_status_llm',
    'is_free_indicator_present', 
    'detailed_text', 'pdf_extracted_text',
    'source_url', 'primary_pdf_url_on_detail_page',
    'site_scraped_from'
]

def load_data(csv_path="data/visualization_events_data.csv") -> pd.DataFrame:
    print(f"Attempting to load data from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file not found at {csv_path}. Returning empty DataFrame.")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded {len(df)} records from {csv_path}.")
        # Ensure all expected columns are present, add if missing (with None or default)
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = None 
        return df
    except Exception as e:
        print(f"Error loading data from {csv_path}: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

df = load_data()

# --- Direct Global Stats Calculation ---
total_items = len(df)
attendable_events_df = df[df['is_attendable_event_llm'] == 'YES']
attendable_count = len(attendable_events_df)
free_attendable_count = len(attendable_events_df[attendable_events_df['cost_status_llm'] == 'FREE'])
uncertain_cost_attendable_count = len(attendable_events_df[attendable_events_df['cost_status_llm'] == 'UNCERTAIN_COST'])

# --- App Layout ---
app.layout = html.Div(children=[
    html.H1(children="Indian Government Event Dashboard"),

    html.Div(className="global-stats-container", children=[
        html.H2("Global Statistics"),
        html.P(f"Total Items Analyzed: {total_items}"),
        html.P(f"Attendable Events ('YES' by LLM): {attendable_count}"),
        html.P(f"Free Attendable Events ('FREE' by LLM): {free_attendable_count}"),
        html.P(f"Attendable Events with Uncertain Cost ('UNCERTAIN_COST' by LLM): {uncertain_cost_attendable_count}")
    ]),

    html.Hr(),

    html.Div(className="filter-container", children=[
        html.Label("Filter by Attendability (LLM Classification):"),
        dcc.Dropdown(
            id='attendability-filter-dropdown',
            options=[
                {'label': 'All Events', 'value': 'ALL'},
                {'label': 'Attendable (YES)', 'value': 'YES'},
                {'label': 'Not Attendable (NO)', 'value': 'NO'},
                {'label': 'Uncertain Attendability', 'value': 'UNCERTAIN'}
            ],
            value='ALL', # Default value
            clearable=False
        ),
    ]),
    
    html.Hr(),

    html.Div(className="charts-container", children=[
        html.Div(className="chart-item", children=[
            dcc.Graph(id='attendability-chart')
        ]),
        html.Div(className="chart-item", children=[
            dcc.Graph(id='cost-profile-chart')
        ]),
        html.Div(className="chart-item", children=[
            dcc.Graph(id='top-sources-chart')
        ]),
    ]),

    html.Hr(),
    
    html.H2("Events Data Table"),
    dash_table.DataTable(
        id='events-data-table',
        columns=[
            {"name": "Title", "id": "event_title"},
            {"name": "Date (ISO)", "id": "event_date_iso"},
            {"name": "Attendable (LLM)", "id": "is_attendable_event_llm"},
            {"name": "Cost (LLM)", "id": "cost_status_llm"},
            {"name": "Source Site", "id": "site_scraped_from"},
            {"name": "Source URL", "id": "source_url"},
        ],
        page_size=10,
        style_cell={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 0},
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('records') # Initial tooltip data
        ],
        tooltip_duration=None 
    )
])

# --- Callbacks ---

@app.callback(
    Output('attendability-chart', 'figure'),
    [Input('attendability-filter-dropdown', 'value')]
)
def update_attendability_chart(selected_filter_value):
    print(f"DEBUG: attendability-chart callback triggered with filter: {selected_filter_value}")
    # This chart shows overall distribution, so filter is not applied here directly on data source for counts
    # but it could be used to highlight a section if desired. For now, always show all.
    if df.empty or 'is_attendable_event_llm' not in df.columns:
        return px.bar(title="Attendability Classification (LLM)")
        
    counts = df['is_attendable_event_llm'].value_counts().reset_index()
    counts.columns = ['Attendability Status (LLM)', 'Count']
    fig = px.bar(counts, x='Attendability Status (LLM)', y='Count', title="Event Attendability (LLM Classification)")
    return fig

@app.callback(
    Output('cost-profile-chart', 'figure'),
    [Input('attendability-filter-dropdown', 'value')] # Filter by attendability for cost profile
)
def update_cost_profile_chart(selected_filter_value):
    print(f"DEBUG: cost-profile-chart callback triggered with filter: {selected_filter_value}")
    
    filtered_df = df.copy()
    if selected_filter_value and selected_filter_value != 'ALL':
        filtered_df = filtered_df[filtered_df['is_attendable_event_llm'] == selected_filter_value]
    
    # Cost profile is most relevant for 'YES' attendable events
    attendable_yes_df = filtered_df[filtered_df['is_attendable_event_llm'] == 'YES']
    
    if attendable_yes_df.empty or 'cost_status_llm' not in attendable_yes_df.columns:
        return px.bar(title="Cost Profile of Attendable Events (LLM)")
        
    cost_counts = attendable_yes_df['cost_status_llm'].value_counts().reset_index()
    cost_counts.columns = ['Cost Status (LLM)', 'Count']
    fig = px.bar(cost_counts, x='Cost Status (LLM)', y='Count', title="Cost Profile of 'YES' Attendable Events (LLM)")
    return fig

@app.callback(
    Output('top-sources-chart', 'figure'),
    [Input('attendability-filter-dropdown', 'value')]
)
def update_top_sources_chart(selected_filter_value):
    print(f"DEBUG: top-sources-chart callback triggered with filter: {selected_filter_value}")
    
    filtered_df = df.copy()
    if selected_filter_value and selected_filter_value != 'ALL':
        filtered_df = filtered_df[filtered_df['is_attendable_event_llm'] == selected_filter_value]

    if filtered_df.empty or 'site_scraped_from' not in filtered_df.columns:
        return px.bar(title="Top Event Source Websites")

    source_counts = filtered_df['site_scraped_from'].value_counts().nlargest(10).reset_index()
    source_counts.columns = ['Source Website', 'Count']
    fig = px.bar(source_counts, x='Source Website', y='Count', title="Top 10 Event Source Websites")
    fig.update_xaxes(tickangle=45)
    return fig

@app.callback(
    [Output('events-data-table', 'data'),
     Output('events-data-table', 'tooltip_data')],
    [Input('attendability-filter-dropdown', 'value')]
)
def update_events_table(selected_filter_value):
    print(f"DEBUG: events-data-table callback triggered with filter: {selected_filter_value}")
    
    if df.empty:
        return [], []

    filtered_df = df.copy()
    if selected_filter_value and selected_filter_value != 'ALL':
        filtered_df = filtered_df[filtered_df['is_attendable_event_llm'] == selected_filter_value]
    
    table_data = filtered_df.to_dict('records')
    tooltip_data = [
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in table_data
    ]
    return table_data, tooltip_data

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) # Make it accessible (run_server is obsolete)
