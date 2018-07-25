



#执行原生sql
from django.db import connections

class db:
    def __init__(self,db='default'):
        self.cursor = connections[db].cursor()

    def query_todict(self,sql):
        self.cursor.execute(sql)
        desc = self.cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in self.cursor.fetchall()]

    def query(self, sql):
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        return results


    # This function is a database modify
    # update,insert,update
    def modi(self, sql):
        self.cursor.execute(sql)















