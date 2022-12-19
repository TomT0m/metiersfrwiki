
"""Imports"""
import urllib.parse
from IPython.display import IFrame

from SPARQLWrapper import SPARQLWrapper, JSON, XML

baseurl='https://query.wikidata.org/embed.html#'

def wdq(query='', width=800, height=500):
  """Runs Wikidata query in an iFrame and shows the results."""
  return IFrame(baseurl + urllib.parse.quote(query), width=width, height=height)

def human_sample(seed, var, count="1000"):
    return """
      service bd:sample {{
   {personne} wdt:P31 wd:Q5 .
   bd:serviceParam bd:sample.limit {count} .
   bd:serviceParam bd:sample.seed  {seed} . 
   bd:serviceParam bd:sample.sampleType "RANDOM" .
  }}
  """.format(seed=seed, personne=var, count=count)

def has_an_article(var):
    return """
    [] schema:about {var};
       schema:isPartOf <https://fr.wikipedia.org/> .
    """.replace("{var}", var)

import re


                             

def labels():
    return """SERVICE wikibase:label { bd:serviceParam wikibase:language "fr, [AUTO_LANGUAGE], en" . }"""

CONSTRAINTS={
    "human_sample":human_sample,
    "has_an_article":has_an_article,
    "label_service":labels
}

def subst_at_index(chaine, min, max, replace):
    return chaine[:min] + replace + chaine[max:]

def preprocess(query):
    parser = re.compile("c:[a-z_]+\( *([a-z_0-9?]+(,[ ]*[a-z_0-9?][a-z_0-9]*)*)? *\)")
    while constraintm := parser.search(query):
        constraint = constraintm[0]
        name = constraint.split("(")[0][2:]
        param_str = (constraint.split("(")[1])[:-1]
        if not re.fullmatch(" *",param_str):
            params = param_str.split(",")
        else:
            params = []
        if name not in CONSTRAINTS:
            raise Exception("Contrainte '{}' pas reconnue".format(name))
        query = subst_at_index(query, constraintm.start(), constraintm.end(), CONSTRAINTS[name](*params))
    return query


import pandas as pd

def value(res_row):
    if res_row["type"] == "literal" and "datatype" in res_row:
        
        match res_row["datatype"]:
            case "http://www.w3.org/2001/XMLSchema#integer":
                return int(res_row["value"])
            case "http://www.w3.org/2001/XMLSchema#decimal":
                return float(res_row["value"])
            case _:
                return res_row["value"]
    else:
        return res_row["value"]

def result_to_dataframe(result, index=None):
    return pd.DataFrame([
        {
            k:value(row[k]) for k in row
        } 
        for row in result
    ], index=index)


def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']
