from pymongo import *
from tqdm import tqdm

class Collection:
    client = MongoClient('mongodb://localhost:27017/')
    nonQuerable = ["apiMethod","collection","attrs"]

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.__dict__['attrs'] = {}
        instance.__dict__['_id'] = None
        excluded = ["apiMethod","collection"]
        for i in cls.__dict__:
            if "__" not in i and i not in excluded and not callable(cls.__dict__[i]):
                instance.attrs[i] = None
                instance.__dict__[i] = None
            if i in excluded:
                instance.apiMethod = cls.__dict__[i]

        return instance

    def getClient(self):
        collections = Collection.client[self.collection].list_collection_names()
        if self.__class__.__name__ in [i for i in collections]:
            return Collection.client[self.collection][self.__class__.__name__]
        else:
            return None

    def get(self,query = {}):
        client = self.getClient()
        if client != None:
            toRetNonFiltered = [i for i in client.find(query)]
            toRet = []
            for i in toRetNonFiltered:
                toAdd = self.__class__.__new__(self.__class__)
                toAdd.__dict__["_id"] = i["_id"]
                for k in i:
                    if k in toAdd.__dict__["attrs"]:
                        toAdd.__dict__["attrs"][k] = i[k]
                toRet.append(toAdd)
            return toRet
        return []


    def getQuery(self):
        query = {}


        for i in self.__dict__:
            if "__" not in i and i not in Collection.nonQuerable and self.__dict__[i] != None:
                query[i] = self.__dict__[i]
        return query

    def insert(self):
        client = self.getClient()
        query = self.getQuery()
        search = []
        if len(query) != 0:
            search = self.get(query)

        if len(search) == 0:
            if client != None:
                self._id = client.insert_one(self.attrs)

    def update(self):
        client = self.getClient()
        if client != None:
            client.update({"_id":self._id},self.attrs)




    def init(self,update = False):
            query = self.getQuery()
            search = []
            if len(query) != 0:
                search = self.get(query)

            if len(search) == 0 or update:
                mapping = self.apiMethod.doLocalMapping()[0]
                for i in mapping:
                    if i in self.__dict__["attrs"]:
                        self.attrs[i] = mapping[i]
                        self.__dict__[i] = mapping[i]
                if len(search) == 0:
                    self.insert()
                elif update:
                    self.update()

            else:
                for k in search[0].attrs:
                    if k in self.__dict__["attrs"]:
                        self.attrs[k] = search[0].attrs[k]
                        self.__dict__[k] = search[0].attrs[k]
                self._id = search[0]._id

