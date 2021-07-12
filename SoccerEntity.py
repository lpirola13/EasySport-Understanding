from elasticsearch_dsl import Document, Keyword, Text, connections

connections.create_connection(hosts=[])


class SoccerEntity(Document):
    abstract = Text()
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
