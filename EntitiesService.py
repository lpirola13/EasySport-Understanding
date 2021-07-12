import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import textwrap
from ElasticSearchClient import ElasticSearchClient
from gensim.models import Word2Vec
from Model import Model
from sklearn.decomposition import PCA
from Sport import Sport
from Visualization import Visualization
from wordcloud import WordCloud


def get_embeddings(to_model, most_similars, n_components, from_model=None):
    word_vectors = []
    words = []
    for i, word in enumerate(most_similars):
        words.append(word[0])
        if i == 0 and from_model:
            word_vectors.append(from_model.wv[word[0]])
        else:
            word_vectors.append(to_model.wv[word[0]])
    df = pd.DataFrame(word_vectors, index=words)
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(df)
    return pd.DataFrame(components)


def prepare_template(dataframe):
    for pos, abstract in enumerate(dataframe['abstract']):
        if abstract != 'None':
            wrapped = textwrap.wrap(abstract, 20)
            new = wrapped[0] + '<br>'
            new_wrapped = textwrap.wrap(abstract[len(wrapped[0]) + 1:len(abstract)], 30)
            new = new + "<br>".join(new_wrapped)
            dataframe['abstract'][pos] = new
    return dataframe


def create_empty_fig(title):
    fig = px.scatter()
    fig.update_layout(yaxis_visible=False, xaxis_visible=False)
    fig.add_annotation(
        text=title,
        showarrow=False,
        xref='paper',
        yref='paper',
        font_size=28
    )
    return fig


def create_scatter_fig(dataframe, title, visualization):
    fig = None
    if visualization == Visualization.D3:
        fig = px.scatter_3d(
            dataframe, x=0, y=1, z=2,
            text='name',
            title=title,
            range_x=[min(dataframe[0]) * 1.5, max(dataframe[0]) * 1.5],
            range_y=[min(dataframe[1]) * 1.5, max(dataframe[1]) * 1.5],
            range_z=[min(dataframe[2]) * 1.5, max(dataframe[2]) * 1.5],
            color='type',
            symbol='sport',
            labels={'type': 'Type', 'sport': 'Sport'},
            custom_data=['name', 'type', 'sport', 'abstract', 'similarity']
        )
        fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
    elif visualization == Visualization.D2:
        fig = px.scatter(
            dataframe, x=0, y=1,
            text='name',
            title=title,
            range_x=[min(dataframe[0]) * 1.5, max(dataframe[0]) * 1.5],
            range_y=[min(dataframe[1]) * 1.5, max(dataframe[1]) * 1.5],
            color='type',
            symbol='sport',
            labels={'0': 'PCA 1', '1': 'PCA 2', 'sport': 'Sport', 'type': 'Type'},
            custom_data=['name', 'type', 'sport', 'abstract', 'similarity']
        )
    fig.update_traces(
        textposition='top center',
        hovertemplate="<br>".join([
            "<b>Name</b>: %{customdata[0]}",
            "<b>Type</b>: %{customdata[1]}",
            "<b>Sport</b>: %{customdata[2]}",
            "<b>Abstract</b>: %{customdata[3]}",
            "<b>Similarity</b>: %{customdata[4]}"
        ])
    )
    return fig


class EntitiesService:
    def __init__(self):
        self.es = ElasticSearchClient('')
        self.soccer = Word2Vec.load("model/soccer.model")
        self.soccer2016 = Word2Vec.load("model/soccer16.model")
        self.soccer2018 = Word2Vec.load("model/soccer18.model")
        self.soccer2020 = Word2Vec.load("model/soccer20.model")
        self.basketball = Word2Vec.load("model/basket.model")
        self.basketball2016 = Word2Vec.load("model/basket16.model")
        self.basketball2018 = Word2Vec.load("model/basket18.model")
        self.basketball2020 = Word2Vec.load("model/basket20.model")
        pd.options.mode.chained_assignment = None

    def get_model_and_sport_and_year(self, model):
        sport = None
        year = None
        if model == Model.SOCCER:
            model = self.soccer
            sport = Sport.SOCCER
        elif model == Model.SOCCER2016:
            model = self.soccer2016
            sport = Sport.SOCCER
            year = '2016'
        elif model == Model.SOCCER2018:
            model = self.soccer2018
            sport = Sport.SOCCER
            year = '2018'
        elif model == Model.SOCCER2020:
            model = self.soccer2020
            sport = Sport.SOCCER
            year = '2020'
        elif model == Model.BASKETBALL:
            model = self.basketball
            sport = Sport.BASKETBALL
        elif model == Model.BASKETBALL2016:
            model = self.basketball2016
            sport = Sport.BASKETBALL
            year = '2016'
        elif model == Model.BASKETBALL2018:
            model = self.basketball2018
            sport = Sport.BASKETBALL
            year = '2018'
        elif model == Model.BASKETBALL2020:
            model = self.basketball2020
            sport = Sport.BASKETBALL
            year = '2020'
        return model, sport, year

    def get_entities_by_sport_and_query(self, sport, query):
        return self.es.get_entities_by_sport_and_query(sport, query)

    def get_similar_from_model(self, model, word, n_results, visualization, positive=None, negative=None):
        embeddings, fig = None, None
        model_name = model.value
        model, sport, year = self.get_model_and_sport_and_year(model)
        entity = self.es.get_entity(sport, (word, 1))
        try:
            if positive and not negative:
                positive_entity = self.es.get_entity(sport, (positive, 1))
                title = 'Più simili a ' + entity['name'] + ' + ' + positive_entity['name'] + ' (' + model_name + ')'
                most_similars = model.wv.most_similar(topn=n_results, positive=[word, positive])
            elif not positive and negative:
                negative_entity = self.es.get_entity(sport, (negative, 1))
                title = 'Più simili a ' + entity['name'] + ' - ' + negative_entity['name'] + ' (' + model_name + ')'
                most_similars = model.wv.most_similar(topn=n_results, positive=[word], negative=[negative])
            elif positive and negative:
                positive_entity = self.es.get_entity(sport, (positive, 1))
                negative_entity = self.es.get_entity(sport, (negative, 1))
                title = 'Più simili a ' + entity['name'] + ' - ' + negative_entity['name'] + ' + ' + positive_entity[
                    'name'] + ' (' + model_name + ')'
                most_similars = model.wv.most_similar(topn=n_results, positive=[word, positive],
                                                      negative=[negative])
            else:
                title = 'Più simili a ' + entity['name'] + ' (' + model_name + ')'
                most_similars = model.wv.most_similar(topn=n_results, positive=[word])
            most_similars.insert(0, (word, 1))
            results_dataframe = self.es.get_names(sport, year, most_similars)
            if visualization == Visualization.D2:
                embeddings = get_embeddings(model, most_similars, 2)
            elif visualization == Visualization.D3:
                embeddings = get_embeddings(model, most_similars, 3)
            results_dataframe = pd.concat([embeddings, results_dataframe], axis=1)
            dataframe = prepare_template(results_dataframe.copy())
            return results_dataframe, create_scatter_fig(dataframe, title, visualization)
        except KeyError:
            return pd.DataFrame(), create_empty_fig('Entity or word not found in ' + model_name)

    def get_analogies_between_models(self, from_model, to_model, word, n_results, visualization):
        embeddings, fig = None, None
        from_model_name = from_model.value
        from_model, from_sport, from_year = self.get_model_and_sport_and_year(from_model)
        to_model_name = to_model.value
        to_model, to_sport, to_year = self.get_model_and_sport_and_year(to_model)
        entity = self.es.get_entity(from_sport, (word, 1))
        try:
            most_similars = to_model.wv.most_similar(topn=n_results, positive=[from_model.wv[word]])
            most_similars.insert(0, (word, 1))
            results_dataframe = self.es.get_names(to_sport, to_year, most_similars, from_sport, from_year)
            if visualization == Visualization.D2:
                embeddings = get_embeddings(to_model, most_similars, 2, from_model)
            elif visualization == Visualization.D3:
                embeddings = get_embeddings(to_model, most_similars, 3, from_model)
            results_dataframe = pd.concat([embeddings, results_dataframe], axis=1)
            dataframe = prepare_template(results_dataframe.copy())
            title = entity['name'] + ' (' + from_model_name + ') in ' + to_model_name
            return results_dataframe, create_scatter_fig(dataframe, title, visualization)
        except KeyError:
            return pd.DataFrame(), create_empty_fig('Entity or word not found in ' + from_model_name)

    def get_temporal_shift(self, sport, word, n_results, visualization):
        entity = self.es.get_entity(sport, (word, 1))
        if 'name' in entity:
            name = entity['name']
        else:
            name = word
        if visualization == Visualization.D2:
            result2016, result2018, result2020 = None, None, None
            if sport == Sport.BASKETBALL:
                result2016, _ = self.get_similar_from_model(Model.BASKETBALL2016, word, n_results, Visualization.D2)
                result2018, _ = self.get_similar_from_model(Model.BASKETBALL2018, word, n_results, Visualization.D2)
                result2020, _ = self.get_similar_from_model(Model.BASKETBALL2020, word, n_results, Visualization.D2)
            elif sport == Sport.SOCCER:
                result2016, _ = self.get_similar_from_model(Model.SOCCER2016, word, n_results, Visualization.D2)
                result2018, _ = self.get_similar_from_model(Model.SOCCER2018, word, n_results, Visualization.D2)
                result2020, _ = self.get_similar_from_model(Model.SOCCER2020, word, n_results, Visualization.D2)
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3))
            ax1.axis("off")
            ax2.axis("off")
            ax3.axis("off")
            if not result2016.empty:
                ax1.title.set_text(name + ' in ' + sport.value + ' 2016')
                dict2016 = result2016.groupby('name').similarity.apply(lambda x: int(x * 100)).to_dict()
                wordcloud2016 = WordCloud(background_color='white').generate_from_frequencies(dict2016)
                ax1.imshow(wordcloud2016)
            else:
                ax1.text(0.5, 0.5, 'Not found in ' + sport.value + ' 2016')
            if not result2018.empty:
                ax2.title.set_text(name + ' in ' + sport.value + ' 2018')
                dict2018 = result2018.groupby('name').similarity.apply(lambda x: int(x * 100)).to_dict()
                wordcloud2018 = WordCloud(background_color='white').generate_from_frequencies(dict2018)
                ax2.imshow(wordcloud2018)
            else:
                ax2.text(0.5, 0.5, 'Not found in ' + sport.value + ' 2018')
            if not result2020.empty:
                ax3.title.set_text(name + ' in ' + sport.value + ' 2020')
                dict2020 = result2020.groupby('name').similarity.apply(lambda x: int(x * 100)).to_dict()
                wordcloud2020 = WordCloud(background_color='white').generate_from_frequencies(dict2020)
                ax3.imshow(wordcloud2020)
            else:
                ax3.text(0.5, 0.5, 'Not found in ' + sport.value + ' 2020')
            if result2016.empty and result2018.empty and result2020.empty:
                fig = plt.figure(figsize=(10, 3))
                fig.text(0.15, 0.5, 'Entity or word not found in ' + sport.value, fontsize=28)
                fig.tight_layout()
                return fig
            else:
                fig.tight_layout()
                return fig
        elif visualization == Visualization.D3:
            dataframe, result2016, result2018, result2020 = None, None, None, None
            if sport == Sport.BASKETBALL:
                result2016, _ = self.get_similar_from_model(Model.BASKETBALL2016, word, n_results, Visualization.D3)
                result2018, _ = self.get_similar_from_model(Model.BASKETBALL2018, word, n_results, Visualization.D3)
                result2020, _ = self.get_similar_from_model(Model.BASKETBALL2020, word, n_results, Visualization.D3)
            elif sport == Sport.SOCCER:
                result2016, _ = self.get_similar_from_model(Model.SOCCER2016, word, n_results, Visualization.D3)
                result2018, _ = self.get_similar_from_model(Model.SOCCER2018, word, n_results, Visualization.D3)
                result2020, _ = self.get_similar_from_model(Model.SOCCER2020, word, n_results, Visualization.D3)
            for dataframe in [result2016, result2018, result2020]:
                for i in dataframe.index:
                    if i == 0:
                        dataframe.at[i, 'symbol'] = 'Word'
                    else:
                        dataframe.at[i, 'symbol'] = 'Context'
            dataframe = pd.concat([result2016, result2018, result2020], axis=0)
            if not dataframe.empty:
                dataframe = prepare_template(dataframe)
                fig = px.scatter_3d(
                    dataframe, x=0, y=1, z=2,
                    text='name',
                    title=name + "'s temporal shift",
                    range_x=[min(dataframe[0]) * 1.5, max(dataframe[0]) * 1.5],
                    range_y=[min(dataframe[1]) * 1.5, max(dataframe[1]) * 1.5],
                    range_z=[min(dataframe[2]) * 1.5, max(dataframe[2]) * 1.5],
                    color='year',
                    symbol='symbol',
                    labels={'symbol': 'Type', 'year': 'Year'},
                    custom_data=['name', 'type', 'sport', 'abstract', 'similarity']
                )
                fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
                fig.update_traces(
                    hovertemplate="<br>".join([
                        "<b>Name</b>: %{customdata[0]}",
                        "<b>Type</b>: %{customdata[1]}",
                        "<b>Sport</b>: %{customdata[2]}",
                        "<b>Abstract</b>: %{customdata[3]}",
                        "<b>Similarity</b>: %{customdata[4]}"
                    ])
                )
                fig.update_layout(height=600)
                return fig
            else:
                return create_empty_fig('Entity or word not found in ' + sport.value)
