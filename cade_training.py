from EntitiesService import EntitiesService
from Model import Model
from Sport import Sport
from Visualization import Visualization
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

es = EntitiesService()


def test(number):
    if number == 1:
        # Query nel db per cercare un'entità, se non esiste ritorna lista vuota
        entities = es.get_entities_by_sport_and_query(Sport.SOCCER, 'messi')
        print(entities)
        entities = es.get_entities_by_sport_and_query(Sport.SOCCER, 'evefeefvev')
        print(entities)
    elif number == 2:
        # Solo entità
        dataframe, fig = es.get_similar_from_model(Model.BASKETBALL, 'chicago_bulls', 10, Visualization.D3)
        print(dataframe)
        fig.show()
    elif number == 3:
        # Con positivo
        dataframe, fig = es.get_similar_from_model(Model.BASKETBALL, 'chicago_bulls', 10, Visualization.D3,
                                                   positive="michael_jordan")
        print(dataframe)
        fig.show()
    elif number == 4:
        # Con negativo
        dataframe, fig = es.get_similar_from_model(Model.BASKETBALL, 'chicago_bulls', 10, Visualization.D3,
                                                   negative="michael_jordan")
        print(dataframe)
        fig.show()
    elif number == 5:
        # Con positivo e negativo
        dataframe, fig = es.get_similar_from_model(Model.BASKETBALL, 'michael_jordan', 10, Visualization.D3,
                                                   positive="los_angeles_lakers", negative="chicago_bulls")
        print(dataframe)
        fig.show()
    elif number == 6:
        # Se l'entità o la parola non esiste
        dataframe, fig = es.get_similar_from_model(Model.BASKETBALL2020, 'evevevf', 10, Visualization.D3)
        print(dataframe)
        fig.show()
    elif number == 7:
        # Analogie tra più modelli (senza il ragionamento
        dataframe, fig = es.get_analogies_between_models(Model.SOCCER2016, Model.BASKETBALL2016, 'cristiano_ronaldo',
                                                         10,
                                                         Visualization.D3)
        print(dataframe)
        fig.show()
    elif number == 8:
        # Se l'entità o la parola non esiste
        dataframe, fig = es.get_analogies_between_models(Model.SOCCER2016, Model.BASKETBALL2016, 'cefevrgbr', 10,
                                                         Visualization.D3)
        print(dataframe)
        fig.show()
    elif number == 9:
        # Temporal shift di un concetto
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'michael_jordan', 10, Visualization.D2)
        fig.show()
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'michael_jordan', 10, Visualization.D3)
        fig.show()
    elif number == 10:
        # Temporal shift di un concetto che non esiste sempre
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'coronavirus', 10, Visualization.D2)
        fig.show()
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'coronavirus', 10, Visualization.D3)
        fig.show()
    elif number == 11:
        # Temporal shift di un concetto che non esiste
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'cecfef', 10, Visualization.D2)
        fig.show()
        fig = es.get_temporal_shift(Sport.BASKETBALL, 'cecfef', 10, Visualization.D3)
        fig.show()

#Andrea bocelli errore

# Errore da sistemare
dataframe, fig = es.get_similar_from_model(Model.SOCCER, 'andrea_bocelli', 10, Visualization.D3)
print(dataframe)
fig.show()

# aggiungere type quando non ce
# togli valori pca
# posiotivi e negativi per wordcloud
# Bordo grafico
# cancellare anno






