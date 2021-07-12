import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, QueryString
from Sport import Sport


class ElasticSearchClient:
    def __init__(self, url):
        self.es = Elasticsearch([url])

    def get_entities_by_sport_and_query(self, sport, query):
        search = Search(using=self.es)
        search = search[0:5]
        if sport == Sport.SOCCER:
            search = search.index('soccer-entity')
        elif sport == Sport.BASKETBALL:
            search = search.index('basketball-entity')
        if query:
            query = '*{}*'.format(query)
            search = search.query(QueryString(query=query, fields=['name^5', 'abstract']))
        hits = []
        for hit in search.execute():
            id = hit.meta['id']
            hit = hit.to_dict()
            entity = {'id': id, 'name': hit['name']}
            if 'abstract' in hit:
                entity['abstract'] = hit['abstract']
            else:
                entity['abstract'] = 'None'
            if 'type' in hit:
                entity['type'] = hit['type']
            else:
                entity['abstract'] = 'None'
            hits.append(entity)
        return hits

    def get_entity(self, sport, element):
        search = Search(using=self.es)
        if sport == Sport.SOCCER:
            search = search.index('soccer-entity')
        if sport == Sport.BASKETBALL:
            search = search.index('basketball-entity')
        search = search.query(Match(_id=element[0]))
        response = search.execute()
        if len(response) > 0:
            entity = {'name': response[0]['name']}
            if 'abstract' in response[0]:
                entity['abstract'] = response[0]['abstract']
            else:
                entity['abstract'] = 'None'
            if 'type' in response[0]:
                entity['type'] = response[0]['type']
            else:
                entity['type'] = 'None'
        else:
            entity = {'name': element[0], 'abstract': 'None', 'type': 'None'}
        entity['similarity'] = round(element[1], 2)
        entity['sport'] = sport.value
        return entity

    def get_names(self, to_sport, to_year, entity_list, from_sport=None, from_year=None):
        annotated_list = []
        for i, element in enumerate(entity_list):
            if from_sport and i == 0:
                entity = self.get_entity(from_sport, element)
                entity['year'] = from_year
                annotated_list.append(entity)
            else:
                entity = self.get_entity(to_sport, element)
                entity['year'] = to_year
                annotated_list.append(entity)
        return pd.DataFrame(annotated_list)
