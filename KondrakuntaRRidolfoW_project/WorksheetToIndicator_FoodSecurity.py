"""
    This file contains the functions required to analyze dataframes derived via pandas from an
        XLSX workbook with worksheets specific to Food Security indicators.
    Legal worksheet names are as follows (case-sensitive):
        "Wheat Received"
        "Wheat Milled"
        "Flour to Bakeries"
    FS Indicators include the following:
        # MT wheat received - pending
        # MT wheat milled - done
        # MT flour produced - done
        # MT flour dispatched to local bakeries - done
        # distinct bakeries receiving flour  - done
        # beneficiaries (NB - derived from MT flour dispatched to local bakeries)
    All functions herein require a dataframe as an object passed as a parameter.
"""
# IMPORT LIBRARIES
# ANALYSIS LIBRARIES: PANDAS, NUMPY, AND COUNTER
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np

KG_TO_MT = 1000
FAO_ASSUMPTION_WHEAT_FLOUR_KG_PER_PERSON_PER_MONTH = 9.00 # ASSUMPTION FROM:
# https://docs.wfp.org/api/documents/WFP-0000144799/download/?_ga=2.55844651.1499810932.1669028621-1055501472.1562658913
# "REFUGEES WERE PROVIDED WITH ... FORTIFIED WHEAT FLOUR (9 KG PER PERSON PER MONTH)
INDICATOR_TABLE_STRUCTURE = ['indicator', 'facility', 'project', 'start date', 'end date', 'value']


"""
    Function wheatReceived() - utilizes the "Wheat Received" worksheet to create one summary dataframe:
        MT wheat received
    
    Params - df - dataframe contianing wheat received data for a milling facility
        standardized XLSX file based on needs of MLTF
    
    Returns: pandas dataframe object.
"""
def wheatReceived(df):
    print("Calculating indicators for the Wheat Received worksheet.")
    df_wheatReceived = df
    # designate columns to keep
    keepcols_wheatReceived = ['start date','end date','delivery load (metric ton)','recipient mill','project']
    # keep only those columns
    df_wheatReceived = df_wheatReceived[keepcols_wheatReceived]
    # pivot//group-by to prepare datatable for insertion into
    df_wheatReceived = df_wheatReceived.groupby(['start date','end date','recipient mill','project']).agg(
        {'delivery load (metric ton)':np.sum}).reset_index()
    df_wheatReceived["indicator"] = "# mt wheat received"
    df_wheatReceived.rename(columns = {'delivery load (metric ton)':'value',
                                       'recipient mill':'facility'}, inplace = True)
    df_wheatReceived = df_wheatReceived[INDICATOR_TABLE_STRUCTURE]
    return df_wheatReceived

"""
    Function wheatMilled() - utilizes the "Wheat Milled" worksheet to create two summary dataframes:
                one for the indicator # MT wheat milled
                another for the indicator # MT flour produced
    
    Params: df - dataframe containing wheat milling data for a milling facility
            standardized input based on needs of MLTF
    
    Returns: list of pandas dataframe objects
"""
def wheatMilled(df):
    print("Calculating indicators from the Wheat Milled worksheet.")
    # READ "Wheat Milled" WORKSHEET
    df_wheatmilling = df
    df_wheatmilling['facility'] = df_wheatmilling['mill']
    keepcols_wheatmilling = ['start date','end date', 'facility', 'mix during milling - local wheat (mt)',
                             'mix during milling - mltf wheat (mt)', 'total flour produced (mt)','project']
    keepcols_wheatmilled = ['start date','end date','facility','total wheat milled','project']
    keepcols_flourproduced = ['start date', 'end date', 'facility', 'total flour produced (mt)','project']
    # DROP ALL NON-REQUIRED (INESSENTIAL) COLUMNS FOR ANALYSIS
    df_wheatmilling = df_wheatmilling[keepcols_wheatmilling]
    df_wheatmilling['total wheat milled'] = df_wheatmilling.loc[:,['mix during milling - local wheat (mt)',
        'mix during milling - mltf wheat (mt)']].sum(axis=1)
    df_wheatmilling = df_wheatmilling.groupby(['start date','end date','facility','project']).agg(
        {'total wheat milled': np.sum,
         'total flour produced (mt)': np.sum
         })
    # RESET THE INDEX
    df_wheatmilling = df_wheatmilling.reset_index()
    # SEPARATE INTO TWO DATAFRAMES, ONE PER INDICATOR
    df_wheatmilled = df_wheatmilling[keepcols_wheatmilled] # MT WHEAT MILLED
    df_wheatmilled['indicator'] = "# MT wheat milled"
    df_wheatmilled['value'] = df_wheatmilled['total wheat milled']
    df_wheatmilled = df_wheatmilled[INDICATOR_TABLE_STRUCTURE]

    df_flourproduced = df_wheatmilling[keepcols_flourproduced] # MT FLOUR PRODUCED
    df_flourproduced['indicator'] = "# MT wheat milled"
    df_flourproduced['value'] = df_flourproduced['total flour produced (mt)']
    df_flourproduced = df_flourproduced[INDICATOR_TABLE_STRUCTURE]

    datatablesForInsertion = [df_wheatmilled, df_flourproduced]
    return datatablesForInsertion

def flourToBakeries(df):
    print("Calculating indicators from the Flour To Bakeries worksheet.")
    df_flour = df
    df_flour['facility'] = df_flour['mill']
    # DEFINE REQUIRED COLUMNS
    keepcols_flour = ['mon','start date','end date', 'facility', 'mt flour dispatched','recipient bakery','project']
    keepcols_flourdispatched = ['start date','end date','facility','mt flour dispatched','project']
    keepcols_distinctbakeries = ['start date','end date','facility','recipient bakery','project']
    keepcols_beneficiaries = ['start date','end date','facility','beneficiaries','project']
    # DROP ALL NON-REQUIRED (INESSENTIAL) COLUMNS
    df_flour = df_flour[keepcols_flour]
    # Calculate beneficiaries based on FAO assumption of kg flour requirements per person per month.
    df_flour['beneficiaries'] = (df_flour['mt flour dispatched']
        * KG_TO_MT / FAO_ASSUMPTION_WHEAT_FLOUR_KG_PER_PERSON_PER_MONTH)
    # DISPLAY INDICATORS IN TABLE, WITH GROUPING BY DATE & MILL
    #          AGGREGATE ROWS BY 'MT Flour Dispatched'
    df_flour = df_flour.groupby(['start date','end date', 'facility','project']).agg(
        {'mt flour dispatched': np.sum,
         'recipient bakery': lambda x: x.nunique(),
         'beneficiaries': np.sum
         })
    df_flour = df_flour.reset_index()
    # SEPARATE INTO DISTINCT DATATABLES, ONE PER INDICATOR
    # MODIFY DATATABLES FOR SUITABLE UPLOAD TO DATABASE
    # INDICATOR: # MT flour dispatched to bakeries
    df_flourdispatched = df_flour[keepcols_flourdispatched]
    df_flourdispatched['indicator'] = '# MT Flour Dispatched'
    df_flourdispatched['value'] = df_flourdispatched['mt flour dispatched']
    df_flourdispatched = df_flourdispatched[INDICATOR_TABLE_STRUCTURE]
    # INDICATOR: # unique/distinct bakeries supported
    df_distinctbakeries = df_flour[keepcols_distinctbakeries]
    df_distinctbakeries['indicator'] = "# distinct bakeries receiving flour"
    df_distinctbakeries['value'] = df_distinctbakeries['recipient bakery']
    df_distinctbakeries = df_distinctbakeries[INDICATOR_TABLE_STRUCTURE]
    # INDICATOR: # beneficiaries
    df_beneficiaries = df_flour[keepcols_beneficiaries].round({'beneficiaries':0})
    df_beneficiaries['indicator'] = "# beneficiaries"
    df_beneficiaries['value'] = df_beneficiaries['beneficiaries']
    df_beneficiaries = df_beneficiaries[INDICATOR_TABLE_STRUCTURE]
    # COMBINE DATATABLES INTO LIST
    datatablesForInsertion = [df_flourdispatched, df_distinctbakeries, df_beneficiaries]
    return datatablesForInsertion # RETURN LIST OF DATATABELS

def run(dictionary):
    print("Performing calculations. Please wait.")
    indicators = []
    for key, value in dictionary.items():
        if (key == "Wheat Received"):
            wheatReceivedIndicatorsToInsert = wheatReceived(value)
            indicators.append(wheatReceivedIndicatorsToInsert)
        elif (key == "Wheat Milled"):
            wheatmilledIndicatorsToInsert = wheatMilled(value)
            for dataframe in wheatmilledIndicatorsToInsert:
                indicators.append(dataframe)
        elif (key == "Flour To Bakeries"):
            flourtobakeriesIndicatorsToInsert = flourToBakeries(value)
            for dataframe in flourtobakeriesIndicatorsToInsert:
                indicators.append(dataframe)
    return indicators
