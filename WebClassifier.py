# -*- coding: utf-8 -*-
"""
@author: Andrea Mattera
"""

import urllib2
from bs4 import BeautifulSoup
import string
import pandas as pd
from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import TreebankWordTokenizer
from urlparse import urlparse


class WebClassifier(object):
    def __init__(self,url):
        self.stop_words=stopwords.words("english")
        self.error=[]
        self.url=url
        parsed_uri = urlparse( url )
        self.baseurl = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        try:
            html_handle = urllib2.urlopen(url).read()
        except Exception :
            raise Exception('Service temporarily unavailable, try again later')
            
        self.soup=BeautifulSoup(html_handle) #instantiates a BeatifulSoup Object
        
    def findKeywords(self,keywords_nr=10):
        '''Creates a dictionary containing all the words present and the relative occurrences
        
        In addition the stop_words are removed, the synonimous are found and just the nouns are considered
        '''
        
        #Another approach is to use FreqDist in the nltk.probability module but creating a dictionary in this way
        #allows to remove non nouns, catch exceptions of bad formattation (mixes of unicode and string) and 
        #find synonimous
        words_count={} #creates a dictionary containing all the words present and the relative occurrences
        #text=cleaned_text.lower()
        lemmatizer=WordNetLemmatizer()
        for word in self.words:
            if word in self.stop_words: continue


            try:
                word=lemmatizer.lemmatize(word) #it helps to recognize words that are basically the same, i.e. 
                                                    #"video" is considered the same as "videos" 
            except Exception:
                self.error.append('Problem with formattation')
                #print word
            try:
                tag=pos_tag([word])[0][1] #the word should be contained in a list, the result is [('shop','NN')], I take the tag
                #print tag
            except Exception:
                self.error.append('Error with the tagging')
            if tag!='NN' and tag!='NNS':
                continue 
            if word in words_count.keys():
                words_count[word]+=1
            else:
                words_count[word]=1
        
        df=pd.DataFrame.from_dict(words_count,orient='index')
        df.columns=['Count']
        df=df.sort('Count',ascending=False)
        values=df.index[:keywords_nr]
        self.keywords=[ind for ind in values if len(ind)>2] #len>2 to drop dummy characters that were not dropped before
        return self.keywords
                
    def getLinks(self):
        '''Extracts all the links present in the web page
        
        The links could be used to obtain further details about the website considered
        '''
        links=[link.get('href') for link in self.soup.findAll('a') if len(link)>3]
        relative_links=[self.baseurl + link for link in links if not(self.baseurl in link)]
        absolute_links=[link for link in links if self.baseurl in link]
        self.links=absolute_links+relative_links
        return self.links
    
    def getKeywords(self):
        d=self.soup.findAll(attrs={"name":"keywords"})
        try:
            self.content=d[0]['content'].encode('utf-8')
        except IndexError:
            self.error.append('The keyword tag is not present in this webpage')
            self.content=None
        return self.content
    
    def getText(self):
        '''Extracts the whole text from a webpage
        
        Useless sections as script and style are removed        
        '''
        [s.extract() for s in self.soup(['style', 'script', '[document]', 'head'])] #I remove head, style,... from my object
        self.text=self.soup.getText()
        return self.text
        
    def getTitle(self):
        '''Extracts the title of the web page
        
        '''
        self.title=self.soup.find('title').getText()
        return self.title
    
    def getWords(self):
        '''Extracts all the words from the text
        
        Moreover the punctuation is removed, the leading and trailing space are removed
        '''
        text=self.text.lower()
        replace_punctuation = string.maketrans(string.punctuation,' '*len(string.punctuation))
        words=TreebankWordTokenizer().tokenize(text)
        self.words=[st.encode('utf-8').translate(replace_punctuation).strip() for st in words]
        self.stop_words.append('') #the null character '' is added to stop_words 
        
        return self.words
    
    

if __name__ == "__main__":
    #url='http://www.amazon.com/Cuisinart-CPT-122-Compact-2-Slice-Toaster/dp/B009GQ034C/ref=sr_1_1?s=kitchen&ie=UTF8&qid=1431620315&sr=1-1&keywords=toaster'
    url='http://www.cnn.com/2013/06/10/politics/edward-snowden-profile/'
    #url='http://blog.rei.com/camp/how-to-introduce-your-indoorsy-friend-to-the-outdoors/'
    web=WebClassifier(url)
    web.getKeywords()
    web.getTitle()
    web.getText()
    web.getWords()
    keys=web.findKeywords()
    print 'Input url : ' + url
    print 'Title of the webpage: ' + web.title
    if web.content:
        print 'The keywords are  : ' + web.content
    print 'The following keywords are found in the text and are ordered by relevance:'
    for i,key in enumerate(keys):
        print '\t' + str(i+1) + ' : ' + key