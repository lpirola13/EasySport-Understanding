from elasticsearch_dsl import Document, Keyword, Text, connections

connections.create_connection(hosts=['https://32paxsax03:k8hpoejxnp@box-625417194.eu-west-1.bonsaisearch.net:443'])


class SoccerEntity(Document):
    abstract = Text(index=False)
    name = Text()
    type = Keyword()

    class Index:
        name = 'soccer-entity'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

    def save(self, **kwargs):
        return super(SoccerEntity, self).save(**kwargs)
