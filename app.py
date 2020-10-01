import urllib

import pandas as pd
import plotly.express as px
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output

# ----------------- APP INSTANTIATION ---------------------
app = dash.Dash(__name__)
server = app.server
PAGE_SIZE = 20
# ________________________READ DATA_______________________________

data = pd.read_excel("bq_ass.xlsx")
#print(data.head(2))

# ____________________________APP LAYOUT___________________________


app.layout = html.Div([
    # Page heading
    html.H1("Business Quant Data Analytics Assignment", style={'text-align': 'center'}),
    html.Br(),
    html.H4('The filtering function supports eq, <, and >. For example, Enter eq Apple'
            ' in the "continent" column and >50 in the "Sales column"'),
    # Rendering the dataframe

    dash_table.DataTable(
        id='data-table',
        columns=[{"name": i, "id": i} for i in data.columns],
        data=data.to_dict('records'),  # Table content
        # ------------------------- FILTERING ------------------------
        filter_action='custom',        # Allows filtering of the table
        filter_query='',
        # ------------------------- SORTING ------------------------
        sort_action='custom',          # Allows data to be sorted
        sort_mode="multi",             # Allows multi selection mode

        column_selectable="single",
        row_selectable="multi",        # Indices of row selected


        # ------------------------- PAGINATION ------------------------
        page_current=0,
        page_size=PAGE_SIZE,
        page_action='custom',          # size of the page displayed
        # ------------------------ STYLING ----------------------------
        style_table={'height': '300px', 'overflowY': 'scroll'},  # sets the DataTable height
        style_cell={
            'minWidth':95,
            'maxWidth':95,
            'width':95,
        },
        style_cell_conditional=[      # Align text columns to the left
            {
                'if': {'column_id':c},
                'text-align':'left'
            } for c in ['Item Type', 'Item']
        ]
    ),
    html.Br(),
    # ------------------------  DOWNLOAD LINK ----------------------------
    html.A('Download CSV', id='my-link', download="data.csv",
            href="",
            target="_blank", style={'text-align': 'center'}),
    html.Br(),
    html.Br(),
    html.Div(id='data-table-container-bar')


])
# --------------------- FILTERING OPERATOR ----------------------

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

# --------------------- FILTERING FUNCTION ----------------------

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3
# --------------------- FILTERING CALLBACK ----------------------

@app.callback(
    Output(component_id='data-table', component_property="data"),
    [Input(component_id='data-table', component_property="page_current"),
     Input(component_id='data-table', component_property="page_size"),
     Input(component_id='data-table', component_property="filter_query")])
def update_table(page_current,page_size, filter):
    '''

    :param page_current:
    :param page_size:
    :param filter:
    :return: filtered dataTable
    '''
    print(filter)
    filtering_expressions = filter.split(' && ')
    dff = data
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')

#----------------- EXPORT CALLBACK-------------------
@app.callback(Output(component_id='my-link', component_property='href')
            , [Input(component_id='data-table', component_property="page_current"),
     Input(component_id='data-table', component_property="page_size"),
     Input(component_id='data-table', component_property='sort_by'),
     Input(component_id='data-table', component_property='filter_query')])
def update_table2(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = data
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    csv_file = dff.to_csv(index=False, encoding='utf-8')
    csv_file = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(csv_file)
    return csv_file


# ------------------------- GRAPH CALLBACK -----------------------

@app.callback(
    Output(component_id='data-table-container-bar', component_property='children'),
    [Input(component_id='data-table', component_property='derived_virtual_data'),
    Input(component_id='data-table', component_property="derived_virtual_selected_rows")]

)

def update_graph(all_rows_data, selected_row_indices):
    '''

    :param all_rows_data: data across the dataframe pre or post filtering
    :param selected_row_indices: indices of selected rows if part of the table after filtering
    :return: bar graph based on rows and columns selected
    '''
    dff = pd.DataFrame(all_rows_data)

    # used to highlight the color of item selected on the table
    colors = ['#7FDBFF' if i in selected_row_indices else '#0074D9'
              for i in range(len(dff))]

    return [
        dcc.Graph(
            id='column',
            figure={
                "data": [
                    {
                        "x": dff["Item"],
                        "y": dff["Sales"],
                        #"text": dff["Sales"],
                        #"textposition":'auto',
                        "type": "bar",
                        "marker": {"color": colors},
                    }
                ],
                "layout": {"title": {"text": "Item sales"},
                           "xaxis": {"automargin": True,
                                     "title": {"text": "Item"}},
                           "yaxis": {"automargin": True,
                                     "title": {"text": "Sales"}},
                           "height": 450,
                           "width": 1000,
                           #"autosize":True,
                           #"margin": {"t": 7, "l": 10, "r": 10},
                           },


            }
        )
        #for column in ["Item", "Item Type"]
    ]

if __name__ == '__main__':
    app.run_server(debug=True)