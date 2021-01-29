from datetime import datetime
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, connections

# Define a default Elasticsearch client
connections.create_connection(hosts=['https://32paxsax03:k8hpoejxnp@box-625417194.eu-west-1.bonsaisearch.net:443'])

class Entity(Document):
    url = Keyword()
    name = Keyword()
    type = Keyword()

    class Index:
        name = 'entity'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

    def save(self, ** kwargs):
        return super(Entity, self).save(** kwargs)

    def is_published(self):
        return datetime.now() > self.published_from


