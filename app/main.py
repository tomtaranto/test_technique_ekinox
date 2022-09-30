import os.path

import numpy as np
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import numpy as np

import plotly.graph_objects as go
import base64, io
import plotly.express as px

app = Dash(__name__)


def init_app():
    app.layout = html.Div([
        html.H3("Dashboard analyse", style={'textAlign': 'center'}),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Glisser Déposer ou ", html.A("Choisir un fichier"), " pour une école"]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),

        html.Div(id='output-data-upload'),
        html.H6("Importance consommation alcool", style={'textAlign': 'center'}),
        dcc.Slider(0, 1, 0.1,
                   value=0.5,
                   id='slider-coef-alcool'
                   ),

        html.H6("Importance absenteisme", style={'textAlign': 'center'}),
        dcc.Slider(0, 1, 0.1,
                   value=0.5,
                   id='slider-coef-absence'
                   ),
        html.H6("Importance durée d'étude", style={'textAlign': 'center'}),
        dcc.Slider(0, 1, 0.1,
                   value=0.5,
                   id='slider-coef-study'
                   ),

        html.H6("Ecole", style={'textAlign': 'center'}),
        dcc.Dropdown(['all', 'GP', 'MS'], 'all', id='dropdown-school'),

        html.H6("Genre", style={'textAlign': 'center'}),
        dcc.Dropdown(['all', 'M', 'F'], 'all', id='dropdown-sex'),

        html.H6("Internet", style={'textAlign': 'center'}),
        dcc.Dropdown(['all', 'yes', 'no'], 'all', id='dropdown-internet'),
    ])


# Parse un csv depuis le menu drop et renvoie un graphe avec les conditions passées
def parse_contents(contents, filename, date, coefalcool, coefabsence, coefstudy, school, sex, internet):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), sep=",", header=0)
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    # Selection des etudiants d'interet
    df = select_students(df, school, sex, internet)
    # Calcul de leur score d'amélioration
    y = compute_score(df, coefalcool, coefabsence, coefstudy)
    # Création du graph
    fig = go.Figure(
        go.Scatter(x=df["FinalGrade"], y=y, text=df["FirstName"]+" "+df["FamilyName"], mode="markers"))
    fig.update_layout(xaxis_title="Final Grade",
                      yaxis_title="Improvability Score")
    return html.Div([
        dcc.Graph(figure=fig),
    ])


# Permet de selection les étudiants suivant des critères (menus dropdown)
def select_students(dataframe, schoolname="all", sex="all", internet="all"):
    if schoolname != "all":
        dataframe = dataframe[dataframe["school"] == schoolname]
    if sex != "all":
        dataframe = dataframe[dataframe["sex"] == sex]
    if internet != "all":
        dataframe = dataframe[dataframe["internet"] == internet]
    return dataframe


# Calcule le score d'amélioration des eleves suivant dse coefficients arbitraires (sliders)
def compute_score(df, coefalcool, coefabsence, coefstudy):
    y = coefstudy * df["studytime"].max() / df["studytime"].max() + \
        coefalcool * df["Dalc"] / df["Dalc"].max() + \
        coefabsence * df["absences"] // 5
    return y


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents'), Input('slider-coef-alcool', 'value'),
               Input('slider-coef-absence', 'value'), Input('slider-coef-study', 'value'),
               Input('dropdown-school', 'value'), Input('dropdown-sex', 'value'), Input('dropdown-internet', 'value')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')],
              )
def update_output(content, coefalcool, coefabsence, coefstudy, school, sex, internet, names, dates):
    # Permet l'actualisation du plot lors de la modification de n'importe quel champ
    if content is not None:
        children = parse_contents(content, names, dates, coefalcool, coefabsence, coefstudy, school, sex, internet)
        return children


# Fonction principale
def main():
    init_app()
    app.run_server(host="0.0.0.0", port="8050", debug=True)


if __name__ == '__main__':
    main()
