from math import tanh
import sqlite3

def dtanh(y):
    return 1.0-y*y

class searchnet:
    def __init__(self,dbname):
		self.con=sqlite3.connect(dbname)
		self.c=self.con.cursor()

    def __del__(self):
        self.con.close()

    def make_tables(self):
        self.c.execute("CREATE TABLE hiddennode(create_key)")
        self.c.execute("CREATE TABLE wordhidden(fromid,toid,strength)")
        self.c.execute("CREATE TABLE hiddenurl(fromid,toid,strength)")
        self.con.commit()

    def get_strength(self,fromid,toid,layer):
        if layer==0:
            table='wordhidden'
        else:
            table="hiddenurl"
        res=self.c.execute("SELECT strength FROM %s WHERE fromid=%d AND toid=%d" % (table,fromid,toid)).fetchone()
        if res==None:
            if layer==0:
                return -0.2
            if layer==1:
                return 0
        return res[0]

    def set_strength(self,fromid,toid,layer,strength):
        if layer==0:
            table='wordhidden'
        else:
            table="hiddenurl"
        res=self.c.execute("SELECT rowid FROM %s WHERE fromid=%d AND toid=%d" % (table,fromid,toid)).fetchone()

        if res==None:
            self.c.execute("INSERT INTO %s (fromid,toid,strength) VALUES (%d,%d,%f)" % (table,fromid,toid,strength))
        else:
            rowid=res[0]
            self.c.execute("UPDATE %s SET strength=%f WHERE rowid=%d" % (table,strength,rowid))

    def generate_hidden_node(self,word_ids,urls):
        if len(word_ids)>3:
            return None
        create_key="_".join(sorted([str(wi) for wi in word_ids]))
        res=self.c.execute("SELECT rowid FROM hiddennode WHERE create_key='%s'" % create_key).fetchone()

        if res==None:
            cur=self.c.execute("INSERT INTO hiddennode (create_key) VALUES ('%s')" % create_key)
            hidden_id=cur.lastrowid

            for word_id in word_ids:
                self.set_strength(word_id,hidden_id,0,1.0/len(word_ids))

            for url_id in urls:
                self.set_strength(hidden_id,url_id,1,0.1)
            self.con.commit()

    def get_all_hidden_ids(self,word_ids,url_ids):
        l1={}
        for word_id in word_ids:
            cur=self.c.execute("SELECT toid FROM wordhidden WHERE fromid=%d" % word_id)
            for row in cur:
                l1[row[0]]=1
        for url_id in url_ids:
            cur=self.c.execute("SELECT fromid FROM hiddenurl WHERE toid=%d" % url_id)
            for row in cur:
                l1[row[0]]=1

        return l1.keys()

    def set_up_net_work(self,word_ids,url_ids):
        self.word_ids=word_ids
        self.hidden_ids=self.get_all_hidden_ids(word_ids,url_ids)
        self.url_ids=url_ids

        self.ai=[1.0]*len(self.word_ids)
        self.ah=[1.0]*len(self.hidden_ids)
        self.ao=[1.0]*len(self.url_ids)

        self.wi=[[self.get_strength(word_id,hidden_id,0) for hidden_id in self.hidden_ids] for word_id in self.word_ids]
        self.wo=[[self.get_strength(hidden_id,url_id,1) for url_id in self.url_ids] for hidden_id in self.hidden_ids]

    def feed_forward(self):
        for i in range(len(self.word_ids)):
            self.ai[i]=1.0

        for j in range(len(self.hidden_ids)):
            sum=0.0
            for i in range(len(self.word_ids)):
                sum=sum+self.ai[i]*self.wi[i][j]

            self.ah[j]=tanh(sum)

        for k in range(len(self.url_ids)):
            sum=0.0
            for j in range(len(self.hidden_ids)):
                sum=sum+self.ah[j]*self.wo[j][k]

            self.ao[k]=tanh(sum)

        return self.ao[:]

    def get_result(self,word_ids,url_ids):
        self.set_up_net_work(word_ids,url_ids)
        return self.feed_forward()



    def back_progate(self,targets,N=0.5):
        output_deltas=[0.0]*len(self.url_ids)
        for k in range(len(self.url_ids)):
            error=targets[k]-self.ao[k]
            output_deltas[k]=dtanh(self.ao[k])*error

        hidden_deltas=[0.0]*len(self.hidden_ids)
        for j in range(len(self.hidden_ids)):
            error=0.0
            for k in range(len(self.url_ids)):
                error=error+output_deltas[k]*self.wo[j][k]
            hidden_deltas[j]=dtanh(self.ah[j])*error

        for j in range(len(self.hidden_ids)):
            for k in range(len(self.url_ids)):
                change=output_deltas[k]*self.ah[j]
                self.wo[j][k]=self.wo[j][k]+N*change


        for i in range(len(self.word_ids)):
            for j in range(len(self.hidden_ids)):
                chanege=hidden_deltas[j]*self.ai[i]
                self.wi[i][j]=self.wi[i][j]+N*chanege

    def train_query(self,word_ids,url_ids,selected_url):
        self.generate_hidden_node(word_ids,url_ids)

        self.set_up_net_work(word_ids,url_ids)
        self.feed_forward()
        targets=[0.0]*len(url_ids)
        targets[url_ids.index(selected_url)]=1.0
        self.back_progate(targets)
        self.update_database()

    def update_database(self):
        for i in range(len(self.word_ids)):
            for j in range(len(self.hidden_ids)):
                self.set_strength(self.word_ids[i],self.hidden_ids[j],0,self.wi[i][j])

        for j in range(len(self.hidden_ids)):
            for k in range(len(self.url_ids)):
                self.set_strength(self.hidden_ids[j],self.url_ids[k],1,self.wo[j][k])

        self.con.commit()
