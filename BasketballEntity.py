from elasticsearch_dsl import Document, Keyword, Text, connections

connections.create_connection(hosts=[])


class BasketballEntity(Document):
    abstract = Text()
    name = Text()
    type = Keyword()

    class Index:
        name = 'basketball-entity'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

    def save(self, **kwargs):
        return super(BasketballEntity, self).save(**kwargs)
