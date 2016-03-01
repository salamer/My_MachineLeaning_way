import urllib2
from BeautifulSoup import *
from urlparse import urljoin
import sqlite3
#import MySQLdb

import nn
mynet=nn.searchnet("nn.db")


ignore_words=set(['the','of','to','and','a','in','is','it'])

class crawler(object):

	def __init__(self,dbname):
#		self.con=MySQLdb.connect(host="localhost",user="root",passwd="960219",db=dbname,charset='utf8')
		self.con=sqlite3.connect(dbname)
		self.c=self.con.cursor()

	def __del__(self):
		self.con.close()

	def dbcommit(self):
		self.con.commit()

	def get_entry_id(self,table,field,value,create_new=True):
		cur=self.c.execute("SELECT ROWID FROM %s WHERE %s='%s'" % (table,field,value))
		res=cur.fetchone()
		if res==None:
			cur=self.c.execute("INSERT INTO %s (%s) VALUES ('%s')" % (table,field,value))
			return cur.lastrowid
		else:
			return res[0]

	def add_to_index(self,url,soup):
#		print "Indexing %s" % url
		if self.is_indexed(url):
			return
		print "Indexing "+url

		text=self.get_text_only(soup)
		words=self.separate_words(text)

		urlid=self.get_entry_id('urllist','url',url)

		for i in range(len(words)):
			word=words[i]
			if word in ignore_words:
				continue
			wordid=self.get_entry_id('wordlist','word',word)
			self.c.execute("INSERT INTO wordlocation(urlid,wordid,location) VALUES (%d,%d,%d)" % (urlid,wordid,i))

	def get_text_only(self,soup):
		v=soup.string
		if v==None:
			c=soup.contents
			result_text=''
			for t in c:
				sub_text=self.get_text_only(t)
				result_text+=sub_text+'\n'
				print result_text.strip()
			return result_text
		else:
			return v.strip()

	def separate_words(self,text):
		split_ter=re.compile("\\W*")
		return [s.lower() for s in split_ter.split(text) if s!='']

	def is_indexed(self,url):
		u=self.c.execute("SELECT ROWID FROM urllist WHERE url='%s'" % url).fetchone()
		if u!=None:
			v=self.c.execute("SELECT * FROM wordlocation WHERE urlid=%d" % u[0]).fetchone()
			if v!=None:
				return True
		return False

	def add_link_ref(self,url_form,url_to,link_text):
		pass

	def crawl(self,pages,depth=2):
		for i in range(depth):
			new_pages=set()
			for page in pages:
				try:
					c=urllib2.urlopen(page)
				except:
					print "could not open %s" % page
					continue

				soup=BeautifulSoup(c.read())
				self.add_to_index(page,soup)

				links=soup("a")
				for link in links:
					if ('href' in dict(link.attrs)):
						url=urljoin(page,link['href'])

						if url.find("'")!=-1:
							continue
						url=url.split("#")[0]
						if url[0:4]=='http' and not self.is_indexed(url):
							new_pages.add(url)
						linkText=self.get_text_only(link)
						self.add_link_ref(page,url,linkText)

				self.dbcommit()

			pages=new_pages

	def create_index_tables(self):
		self.c.execute("CREATE TABLE urllist(url  CHAR(50))")
		self.c.execute("CREATE TABLE wordlist(word  CHAR(50))")
		self.c.execute("CREATE TABLE wordlocation(urlid INT(50),wordid INT(50),location CHAR(50))")
		self.c.execute("CREATE TABLE link(fromid INTEGER(50),toid INTEGER(50))")
		self.c.execute("CREATE TABLE linkwords(wordid INT(50),linkid INT(50))")
		self.c.execute("CREATE INDEX wordidx ON wordlist(word)")
		self.c.execute("CREATE INDEX urlidx ON urllist(url)")
		self.c.execute("CREATE INDEX wordurlidx ON wordlocation(wordid)")
		self.c.execute("CREATE INDEX urltoidx ON link(toid)")
		self.c.execute("CREATE INDEX urlfromidx ON link(fromid)")
		self.dbcommit()

	def calculate_pagerank(self,iterations=20):
		self.c.execute("DROP TABLE IF EXISTS pagerank")
		self.c.execute("CREATE TABLE pagerank(urlid primary key,score)")

		self.c.execute("INSERT INTO pagerank SELECT rowid,1.0 from urllist")
		self.dbcommit()

		for i in range(iterations):
			print "Interation %d" % (i)
			for (urlid,) in self.c.execute("SELECT rowid FROM urllist"):
				pr=0.15

				for(linker,) in self.c.execute("SELECT DISTINCT fromid FROM link WHERE toid=%d" % urlid):
					linking_pr=self.c.execute("SELECT score FROM pagerank WHERE urlid=%d" % linker).fetchone()[0]

					linking_count=self.c.execute("SELECT COUNT(*) FROM link WHERE fromid=%d" % linker).fetchone()[0]
					pr+=0.85*(linking_pr/linking_count)
				self.c.execute("UPDATE pagerank SET score=%f WHERE urlid=%d" % (pr,urlid))
			self.dbcommit()



class searcher:
	def __init__(self,dbname):
		self.con=sqlite3.connect(dbname)
		self.c=self.con.cursor()

	def __del__(self):
		self.con.close()
	def get_match_rows(self,q):
		field_list='w0.urlid'
		table_list=''
		clause_list=''
		word_ids=[]

		words=q.split(' ')
		table_number=0

		for word in words:
#			print word
			word_row=self.c.execute("SELECT ROWID FROM wordlist WHERE word='%s'" % word).fetchone()

#			print word_row

			if word_row!=None:
				word_id=word_row[0]
				word_ids.append(word_id)
				if table_number>0:
					table_list+=','
					clause_list+=' and '
					clause_list+='w%d.urlid=w%d.urlid and ' % (table_number-1,table_number)
				field_list+=',w%d.location' % table_number
				table_list+='wordlocation w%d' % table_number
				clause_list='w%d.wordid=%d' % (table_number,word_id)
				table_number+=1

		print (field_list,table_list,clause_list)

		full_query="SELECT %s FROM %s WHERE %s" % (field_list,table_list,clause_list)
		cur=self.c.execute(full_query)
		rows=[row for row in cur]

		return rows,word_ids

	def get_scored_list(self,rows,word_ids):
		total_scores=dict([(row[0],0) for row in rows])

#		weights=[(1.0,self.frequency_score(rows))]

#		weights=[(1.0,self.location_score(rows))]

		weights=[(1.0,self.frequency_score(rows)),
				(1.0,self.location_score(rows)),
				(1.0,self.pagerank_score(rows)),
				(1.0,self.link_text_score(rows,word_ids))]

		for (weight,scores) in weights:
			for url in total_scores:
				total_scores[url]+=weight*scores[url]

		return total_scores

	def get_url_name(self,id):
		return self.c.execute("SELECT url FROM urllist WHERE rowid=%d" % id).fetchone()[0]

	def query(self,q):
		rows,word_ids=self.get_match_rows(q)
		scores=self.get_scored_list(rows,word_ids)
		ranked_scores=sorted([(score,url) for (url,score) in scores.items()],reverse=1)
		for (score,url_id) in ranked_scores[0:10]:
			print "%f\t%s" % (score,self.get_url_name(url_id))

		return word_ids,[r[1] for r in ranked_scores[0:10]]

	def normalize_scores(self,scores,small_is_better=0):
		v_small=0.00001
		if small_is_better:
			min_score=min(scores.values())
			return dict([(u,float(min_score)/max(v_small,l)) for (u,l) in scores.items()])
		else:
			max_score=max(scores.values())
			if max_score==0:
				max_score=v_small
			return dict([(u,float(c)/max_score) for (u,c) in scores.items()])

	def frequency_score(self,rows):
		counts=dict([(row[0],0) for row in rows])
		for row in rows:
			counts[row[0]]+=1
		return self.normalize_scores(counts)

	def location_score(self,rows):
		locations=dict([(row[0],1000000) for row in rows])
		for row in rows:
#			print "~~~\n"
#			print row
			loc=sum([int(i) for i in row[1:]])
#			print "loc:",loc
			if loc<locations[row[0]]:
				locations[row[0]]=loc
#			print locations
		return self.normalize_scores(locations,small_is_better=1)

	def distance_score(self,rows):
		if len(rows[0])<=2:
			return dict([(row[0],1.0) for row in rows])

		min_distance=dict([(row[0],10000000) for row in rows])

		for row in rows:
			dist=sum([abs(row[i]-row[i-1]) for i in range(2,len(row))])
			if dist<min_distance[row[0]]:
				min_distance[row[0]]=dist
		return self.normalize_scores(min_distance,small_is_better=1)

	def in_bound_link_score(self,rows):
		unique_urls=set([row[0] for row in rows])
		in_bound_count=dict([(u,self.c.execute("SELECT COUNT(*) FROM link WHERE toid=%d" % u).fetchone()[0]) for u in unique_urls])

		return self.normalize_scores(in_bound_count)

	def pagerank_score(self,rows):
		pageranks=dict([(row[0],self.c.execute("SELECT score FROM pagerank WHERE urldid=%d" % row[0]).fetchone()[0]) for row in rows])

		max_rank=max(pageranks.values())
		normalized_scores=dict([(u,float(l)/max_rank) for (u,l) in pageranks.items()])

		return normalized_scores

	def link_text_score(self,rows,word_ids):
		link_scores=dict([(row[0],0) for row in rows])
		for word_id in word_ids:
			cur=self.c.execute("SELECT link.fromid,link.toid FROM linkwords,link WHERE wordid=%d AND linkwords.linkid=link.rowid" % wordid)
			for (fromid,toid) in cur:
				if toid in link_scores:
					pr=self.c.execute("SELECT score FROM pagerank WHERE urlid=%d" % fromid).fetchone()[0]
					link_scores[toid]+=pr

		max_score=max(link_scores.values())
		normalized_scores=dict([(u,float(1)/max_score) for (u,l) in link_scores.items()])
		return normalized_scores

	def nn_score(self,rows,word_ids):
		url_ids=[urld_id for url_id in set([row[0] for row in rows])]
		nn_res=mynet.get_result(word_ids,url_ids)
		scores=dict([(url_ids[i],nn_res[i]) for i in range(len(url_ids))])

		return self.normalize_scores(scores)
