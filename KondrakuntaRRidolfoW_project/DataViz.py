# DATA VIZ LIBRARIES: MATPLOTLIB AND SEABORN
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb
import matplotlib.dates as mdates
from datetime import datetime

# COLOR LIBRARY
import colorama
from colorama import Fore, Style
import matplotlib.colors as mcolors

COLUMNS_FOR_DV = ["Facility","EndDate","Value"]


def makeLineChart(df):
    # PLOT THE CHART
    title = ""
    df = df[COLUMNS_FOR_DV]
    df = df.pivot(index="EndDate", columns="Facility", values="Value")
    print(df)
    ax = df.plot.bar(rot=0)

    fig = ax.get_figure()
    fig.savefig('myplot.png')
    print(df)
    # return fig

    # ax = df.sort_index().plot()
    # legend_content = df['Facility'].unique().tolist()
    # # GET USER INPUT FOR CHART TITLE AND AXES LABELS
    # title = input("Please enter a title for your chart: ")
    # xlabel = input("Please write a label for the x-axis: ")
    # ylabel = input("Please write a label for the y-axis: ")
    # # STYLE THE CHART USING USER INPUT
    # ax.set_title(title, loc='left', fontsize=12
    #              , fontweight=0, color='orange')
    # ax.set_xlabel(xlabel)
    # ax.set_ylabel(ylabel)
    # # ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    # ax.legend(legend_content, bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)




def getSQLResultsAsPrintedString(cursor, procedureName, listOfParams):
    try:
        # Convert paramList to Strings separated by commas
        params = "("
        for i in range(len(listOfParams)):
            if i != max(range(len(listOfParams))):
                # separate params with commas
                params = params + "'" + listOfParams[i] + "'" + ","
            # for final param in paramList, end char is )
            else:
                params = params + "'" + listOfParams[i] + "')"
        # add params to procedure name
        procedure = "CALL " + procedureName + params
        # execute procedure w/ params
        printTableRowByRow(cursor, procedure)
    except Exception as e:
        print("Exception occurred: {}".format(e))
    return

def getSQLResultsAsDataFrame(cursor, procedureName, listOfParams):
    try:
        # Convert paramList to Strings separated by commas
        params = "("
        for i in range(len(listOfParams)):
            if i != max(range(len(listOfParams))):
                # separate params with commas
                params = params + "'" + listOfParams[i] + "'" + ","
            # for final param in paramList, end char is )
            else:
                params = params + "'" + listOfParams[i] + "')"
        # add params to procedure name
        procedure = "CALL " + procedureName + params
        # execute procedure w/ params
        cursor.execute(procedure)
        results = cursor.fetchall()
        return pd.DataFrame(results)
    except Exception as e:
        print("Exception occurred: {}".format(e))
    return





def printTableRowByRow(cursor, sqlstmt):
    """
        FUNCTION: printTableRowByRow()
        Given two parameters - a cursor and a string that is a SQL statement,
            prints each row in the resulting table from the SQL statement

        :param :
            cursor - a Cursor object
            sqlstmt - a String of a SQL statement, e.g.,
                    "SELECT * FROM table WHERE condition = value;" or
                    "CALL PROCEDURE procedure_name()"
    """
    cursor.execute(sqlstmt)
    results = cursor.fetchall()
    header = tuple(i[0] for i in cursor.description)
    resultsList = []
    for row in results:
        values = list(row.values())
        resultsList.append(values)
    data = [header] + resultsList
    width = max((len(str(x)) for d in data for x in d))
    config = [{'width': 0} for _ in range(len(data[0]))]
    for rec in data:
        for c, value in enumerate(rec):
            config[c]['width'] = max(config[c]['width'], len(str(value)))
    format_ = []
    for f in config:
        format_.append('{:<' + str(f['width']) + '}')
    format_ = ' | '.join(format_)
    for rec in data:
        rec = [str(x) for x in rec]
        line = format_.format(*rec)
        print(line)

def run(cursor, procedureName, listOfParams):
    df = getSQLResultsAsDataFrame(cursor, procedureName, listOfParams)
    if df.empty:
        return
    else:
        makeLineChart(df)
