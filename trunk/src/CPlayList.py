#############################################################################
#
# Navi-X Playlist browser
# by rodejo (rodejo16@gmail.com)
#############################################################################

#############################################################################
#
# CPlaylist:
# Playlist class. Supports loading of Navi-X PLX files, RSS2.0 files, 
# flick feed files and html files.
#############################################################################

from string import *
import sys, os.path
import urllib
import re, random, string
import xbmc, xbmcgui
import re, os, time, datetime, traceback
import Image, ImageFile
import shutil
import zipfile
from libs2 import *
from settings import *
from CFileLoader import *

try: Emulating = xbmcgui.Emulating
except: Emulating = False

RootDir = os.getcwd()
if RootDir[-1]==';': RootDir=RootDir[0:-1]
if RootDir[-1]!='\\': RootDir=RootDir+'\\'
imageDir = RootDir + "\\images\\"
cacheDir = RootDir + "\\cache\\"
imageCacheDir = RootDir + "\\cache\\imageview\\"
scriptDir = "Q:\\scripts\\"
myDownloadsDir = RootDir + "My Downloads\\"
initDir = RootDir + "\\init\\"

######################################################################
# Description: Playlist class. Contains CMediaItem objects
######################################################################
class CPlayList:
    def __init__(self):
        self.version = '0'
        self.background = 'default'
        self.title = ''
        self.URL = ''
        self.player = 'default'
        self.list = []
    
    ######################################################################
    # Description: Adds a item to playlist.
    # Parameters : item = CMediaItem obect
    # Return     : -
    ######################################################################
    def add(self, item):
        self.list.append(item)

    ######################################################################
    # Description: clears the complete playlist.
    # Parameters : -
    # Return     : -
    ######################################################################
    def clear(self):
        del self.list[:]
    
    ######################################################################
    # Description: removes a single entry from the playlist.
    # Parameters : index=index of entry to remove
    # Return     : -
    ######################################################################
    def remove(self, index):
        del self.list[index]

    ######################################################################
    # Description: Returns the number of playlist entries.
    # Parameters : -
    # Return     : number of playlist entries.
    ######################################################################
    def size(self):
        return len(self.list)

    ######################################################################
    # Description: Loads a playlist .plx file. File source is indicated by
    #              the 'filename' parameter or the 'mediaitem' parameter.
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_plx(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'playlist.plx')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            data = data.split('\n')
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = '0'
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = ''
        self.player = mediaitem.player
        #clear the list
#        del self.list[:]

        #parse playlist entries 
        counter = 0
        state = 0
        for m in data:
            if m and m[0] != '#':
                index = m.find('=')
                if index != -1:
                    key = m[:index]
                    value = m[index+1:]
                    if key == 'version' and state == 0:
                        self.version = value
                        #check the playlist version
                        if int(self.version) > int(plxVersion):
                            return -1
                    elif key == 'background' and state == 0:
                        self.background=value
                    elif key == 'player' and state == 0:
                        self.player=value
                    elif key == 'logo':
                        self.logo=value
                    elif key == 'title':
                            self.title=value
                    elif key == 'type':
                        if state == 1:
                            self.list.append(tmp)
                        else: #state=0
                            del self.list[:]
                        tmp = CMediaItem() #create new item
                        tmp.type = value
                        if tmp.type == 'video' or tmp.type == 'audio':
                            tmp.player = self.player

                        counter = counter+1
                        state = 1
                    elif key == 'version' and state == 1:
                        tmp.version=value
                    elif key == 'name':
                        tmp.name=value
                    elif key == 'thumb':
                        tmp.thumb=value
                    elif key == 'URL':
                        tmp.URL=value
                    elif key == 'DLloc':
                        tmp.DLloc=value
                    elif key == 'player':
                        tmp.player=value 
                    elif key == 'background':
                        tmp.background=value 
                        
                    
        if state == 1:
            self.list.append(tmp)
            
        return 0
        
    ######################################################################
    # Description: Loads a RSS2.0 feed xml file.
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_rss_20(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL

        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'feed.xml')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            data = data.split('<item>')
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = ''
        self.player = mediaitem.player
        #clear the list
        del self.list[:]
        
        counter=0
        #parse playlist entries 
        for m in data:
            if counter == 0:
                #fill the title
                index = m.find('<title>')
                if index != -1:
                    index2 = m.find('</title>')
                    if index != -1:
                        value = m[index+7:index2]
                        self.title = value
                
                #fill the logo
                index = m.find('<image>')
                if index != -1:
                    index2 = m.find('</image>')
                    if index != -1:
                        index3 = m.find('<url>', index, index2)
                        if index != -1:
                            index4 = m.find('</url>', index, index2)
                            if index != -1:
                                value = m[index3+5:index4]
                                self.logo = value
                else: #try if itunes image
                    index = m.find('<itunes:image href="')
                    if index != -1:
                        index2 = m.find('"', index+20)
                        if index != -1:
                            value = m[index+20:index2]
                            self.logo = value
       
                counter = counter + 1
            else:
                tmp = CMediaItem() #create new item
                tmp.player = self.player

                #get the publication date.
                index = m.find('<pubDate')
                if index != -1:
                    index2 = m.find('>', index)
                    if index2 != -1:
                        index3 = m.find('</pubDate')
                        if index3 != -1:
                            index4 = m.find(':', index2, index3)
                            if index4 != -1:
                                value = m[index2+1:index4-2]
                                tmp.name = value

                #get the title.
                index = m.find('<title')
                if index != -1:
                    index2 = m.find('>', index)
                    if index2 != -1:
                        index3 = m.find('</title>')
                        if index3 != -1:
                            index4 = m.find('![CDATA[', index2, index3)
                            if index4 != -1:
                                value = m[index2+10:index3-3]
                            else:
                                value = m[index2+1:index3]
                            tmp.name = tmp.name + value

                #get the enclosed content.
                index = m.find('enclosure')
                if index != -1:
                    index = m.find('url=',index)
                    if index != -1:
                        index2 = m.find('"', index+5)
                        if index2 != -1:
                            value = m[index+5:index2]
                            tmp.URL = value
                
                if tmp.URL != '':
                    #validate the type based on file extension
                    ext_pos = tmp.URL.rfind('.') #find last '.' in the string
                    if ext_pos != -1:
                        ext = tmp.URL[ext_pos+1:]
                        if ext == 'jpg' or ext == 'gif' or ext == 'png':
                            tmp.type = 'image'
                        elif ext == 'mp3':
                            tmp.type = 'audio'
                        else:
                            tmp.type = 'video'
                
                    self.list.append(tmp)
                    counter = counter + 1
                    
        return 0

    ######################################################################
    # Description: Loads a Flickr Daily feed xml file.
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_rss_flickr_daily(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL

        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'feed.xml')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            data = data.split('<item ')
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = ''
        self.player = mediaitem.player
        #clear the list
        del self.list[:]
        
        counter=0
        #parse playlist entries 
        for m in data:
            if counter == 0:
                #fill the title
                index = m.find('<title>')
                if index != -1:
                    index2 = m.find('</title>')
                    if index != -1:
                        value = m[index+7:index2]
                        self.title = value
                
                counter = counter + 1
            else:
                #get the title.
                index = m.find('<title>')
                if index != -1:
                    index2 = m.find('</title>', index)
                    if index2 != -1:
                        value = m[index+7:index2]
                        name = value

                #get the enclosed content.
                items = 0
                index = m.find('<description>')
                if index != -1:
                    index2 = m.find('</description>', index)
                    if index2 != -1:
                        index3 = m.find('src=', index)
                        while index3 != -1:
                            index4 = m.find('"', index3+5)
                            if index4 != -1:
                                tmp = CMediaItem() #create new item
                                tmp.type = 'image'
                                if items > 0:
                                    tmp.name = name + " " + str(items+1)
                                else:
                                    tmp.name = name
                            
                                value = m[index3+5:index4-4]
                                if value[-6] == '_':
                                    value = value[:-6] + ".jpg"
                                tmp.URL = value
                                tmp.thumb = tmp.URL[:-4] + "_m" + ".jpg"
                                
                                self.list.append(tmp)
                                counter = counter + 1

                                items= items + 1
                                index3 = m.find('src=', index4)
                
        return 0


    ######################################################################
    # Description: Loads html elements from stage6 website. 
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_html(self, filename='', mediaitem=CMediaItem(), type='html_body_sidebar'):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader2()
        loader.load(self.URL, cacheDir + 'page.html')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            data = data.split('\n')
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = 'Stage6' + ' - ' + mediaitem.name
        self.player = mediaitem.player
        #clear the list
        del self.list[:]
        
        if type == 'html_body_sidebar':
            string = 'body-sidebar'
        else:
            string = 'body-content'
        
        counter=0
        #parse playlist entries 
        for m in data:
            if counter == 0:
                index = m.find(string)
                if index != -1:
                    counter=1 #string was found
            else:
                #fill the title
                index1 = m.find('href="./cat')
                index2 = m.find('href="./id')
                index3 = m.find('</a><br')
                index4 = m.find('id/')
                index5 = m.find('">')
                index6 = m.find('"',index4)
                if index1 != -1 or index2 != -1:
                    if index3 != -1:
                        tmp = CMediaItem() #create new item
                        tmp.player = self.player
                        
                        if index4 != -1:
                            value = m[index4+3:index6]
                            tmp.URL = 'http://video.stage6.com/' + value + '/.divx'
                            tmp.thumb = 'http://images.stage6.com/video_images/' + value + 't.jpg'

                            value = m[index5+2:index3]
                            tmp.name = value

                            counter = counter + 1
                            tmp.type = 'video'

                        else:
                            value = m[index1+7:index5]
                            index7 = self.URL.find('/', 7)
                            tmp.URL = self.URL[:index7] + value

                            value = m[index5+2:index3]
                            tmp.name = value                            

                            counter = counter + 1
                            tmp.type = 'html_body_sidebar'
                   
                        self.list.append(tmp)
                        counter = counter + 1
                elif counter > 1:
                    index = m.find('</div>')
                    if index != -1:
                        return 0 #we are done

        return 0

    ######################################################################
    # Description: Loads html elements from the Youtube website
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_html_youtube(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader2()
        loader.load(self.URL, cacheDir + 'page.html')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            entries = data.split('<!-- end vEntry -->')
            lines = data.split('\n')
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = 'Youtube' + ' - ' + mediaitem.name
        self.player = mediaitem.player
        #clear the list
#        if mediaitem.name != 'Next page':
        del self.list[:]
        
        #parse playlist entries 
        for m in entries:
            index1= m.find('class="vtitle marT5"')
            if index1 == -1:
                index1= m.find('class="vlshortTitle"')
            if index1 == -1:
                index1= m.find('class="vSnippetTitle"')
            if index1 != -1:
                tmp = CMediaItem() #create new item
                tmp.type = 'video'
 
                index2 = m.find('</div>', index1)
                index3 = m.find('watch?v=', index1, index2)
                index4 = m.find('"', index3, index2)
                value = m[index3+8:index4]
                tmp.URL = 'http://youtube.com/v/' + value + '.swf'
                tmp.thumb = 'http://img.youtube.com/vi/' + value + '/default.jpg'

                #now get the title
                index5 = m.find('">', index4+1, index2)
                index6 = m.find('</a>', index5, index2)
                value = m[index5+2:index6]
                value = value.replace('<b>',"")
                value = value.replace('</b>',"")
                value = value.replace('&quot;',"")
                value = value.replace('&#39;',"\'")
                tmp.name = value
                
                tmp.player = self.player
                self.list.append(tmp)                

        #check if there is a next page in the html
        for m in lines:
            index1 = m.find('class="pagerNotCurrent">Next</a>')
            if index1 != -1:
                index2=m.find('<a href="')
                if index2 != -1:
                    index3 = m.find('"',index2+9)
                    if index3 != -1:
                        value = m[index2+9:index3]
                        tmp = CMediaItem() #create new item
                        tmp.type = 'html_youtube'
                        tmp.name = 'Next page'
                        tmp.player = self.player
                    
                        #create the next page URL
                        index4 = self.URL.find("?")
                        url = self.URL[:index4]
                        index5 = value.find("?")
                        value = value[index5:]
                        tmp.URL= url+ value
                    
                        self.list.append(tmp)                

        return 0

    ######################################################################
    # Description: Loads html elements from the Stage6 website
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_html_stage6(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'page.html')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = 'Stage6' + ' - ' + mediaitem.name
        self.player = mediaitem.player
        #clear the list
        del self.list[:]
        
        #parse playlist entries
        index1 = 0
        while index1 != -1:
            index1 = data.find('class=\'video\'',index1+1)
            if index1 != -1:
                time=''
                title=''
                id=''
                index2 = data.find('class=\'video-overlay\'', index1) #time indication
                if index2 != -1:
                    index3 = data.find('</div>',index2)
                    if index3 != -1:
                        index4 = data.rfind('</acronym>', index2, index3)                    
                        if index4 == -1:
                            time = data[index2+22:index3]
                        else:
                            time = data[index4+10:index3]

                #Get the movie title and ID
                index2 = data.find('class=\'video-title\'', index1) #title
                if index2 != -1:
                    index3 = data.find('</div>',index2)
                    if index3 != -1:
                        index4 = data.find('title=',index2, index3)
                        if index4 != -1:
                            index5 = data.find('\'',index4+7, index3)
                            if index5 != -1:
                                title = data[index4+7:index5]
                                title = title.replace('&#39;',"\'")

                        #Get the movie ID
                        index4 = data.find('/video/',index2, index3)
                        if index4 != -1:
                            index5 = data.find('/',index4+7, index3)
                            if index5 != -1:
                                id = data[index4+7:index5]
                if id != '': #add only if valid ID found
                    tmp = CMediaItem() #create new item
                    tmp.type = 'video'
                    tmp.name = title + ' ' + '(' + time + ')'
                    tmp.URL = 'http://video.stage6.com/' + id + '/.divx'
                    tmp.thumb = 'http://images.stage6.com/video_images/' + id + 't.jpg'
                    tmp.player = self.player
                    self.list.append(tmp)

        #check if there is a next page in the html
        index1 = data.find('class=\'pagination-number pagination-right\'')
        if index1 != -1:
            index2 = data.find('</div>',index1)
            if index2 != -1:
                index3 = data.find('href=', index1, index2)
                if index3 != -1:
                    index4 = data.find('\'',index3+6, index2)
                    if index4 != -1:
                        value = data[index3+6:index4]
                        tmp = CMediaItem() #create new item
                        tmp.type = 'html_stage6'
                        tmp.name = 'Next page'
                        tmp.player = self.player
                        tmp.URL = 'http://www.stage6.com' + value
                    
                        self.list.append(tmp)                

        return 0

    ######################################################################
    # Description: Loads shoutcast XML file.
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_xml_shoutcast(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'shoutcast.xml')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()

            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = 'Shoutcast' + ' - ' + mediaitem.name
        self.player = mediaitem.player
        #clear the list
        del self.list[:]

        if data.find('<stationlist>') != -1:
            #parse playlist entries
            entries = data.split('</station>')            
            for m in entries:
                tmp = CMediaItem() #create new item
                tmp.type = 'audio'
                tmp.player = self.player

                index1 = m.find('station name=')
                if index1 != -1: #valid entry
                    index2= m.find('"', index1+14)
                    tmp.name = m[index1+14:index2]
                
                index1 = m.find('br=')
                if index1 != -1:
                    index2= m.find('"', index1+4)
                    bitrate = m[index1+4:index2]
                    tmp.name = tmp.name + " (" + bitrate + "kbps) "
                    tmp.URL = ''

                index1 = m.find('ct=')
                if index1 != -1:
                    index2= m.find('"', index1+4)
                    np = m[index1+4:index2]
                    tmp.name = tmp.name + "- Now Playing: " + np
                    tmp.URL = ''

                index1 = m.find('br=')
                if index1 != -1:
                    index2= m.find('"', index1+4)
                    bitrate = m[index1+4:index2]
                    tmp.name = tmp.name + " (" + bitrate + "kbps) "
                    tmp.URL = ''
   
                index1 = m.find('genre=')
                if index1 != -1: #valid entry
                    index2= m.find('"', index1+7)
                    genre = m[index1+7:index2]
                    tmp.name = tmp.name + '[' + genre + ']'

                index1 = m.find('id=')
                if index1 != -1:
                    index2= m.find('"', index1+4)
                    id = m[index1+4:index2]
                    tmp.URL = "http://www.shoutcast.com/sbin/shoutcast-playlist.pls?rn=" + id + "&file=filename.pls"

                    self.list.append(tmp)
                
        else: #<genrelist>
            #parse playlist entries
            entries = data.split('</genre>')
            for m in entries:
                tmp = CMediaItem() #create new item
                tmp.type='xml_shoutcast'
                tmp.player = self.player
                
                index1 = m.find('name=')
                if index1 != -1:
                    index2= m.find('"', index1+6)
                    genre = m[index1+6:index2]
                    tmp.name = genre
                    tmp.URL = "http://www.shoutcast.com/sbin/newxml.phtml?genre=" + genre
                    self.list.append(tmp)
                
        return 0

    ######################################################################
    # Description: Loads Quicksilverscreen HTML.
    # Parameters : filename=URL or local file
    #              mediaitem=CMediaItem object to load    
    # Return     : 0=succes, 
    #              -1=invalid playlist version, 
    #              -2=could not open playlist
    ######################################################################
    def load_html_QSScreen(self, filename='', mediaitem=CMediaItem()):
        if filename != '':
            self.URL = filename
        else:
            self.URL = mediaitem.URL
        
        loader = CFileLoader()
        loader.load(self.URL, cacheDir + 'page.html')
        if loader.state != 0:
            return -2
        filename = loader.localfile
        
        try:
            f = open(filename, 'r')
            data = f.read()
            f.close()
        except IOError:
            return -2
        
        #defaults
        self.version = plxVersion
        self.background = mediaitem.background
        self.logo = 'none'
        self.title = 'QuickSilverScreen' + ' - ' + mediaitem.name
        self.player = mediaitem.player
        #clear the list
        del self.list[:]

        if mediaitem.type == 'html_qsscreen_thumb':
            #parse playlist entries from page containing thumb images
            entries = data.split('</table>')
            for m in entries:
                index1 = m.find("src=\"http://images.stage6.com/video_images/")
                if index1 != -1: #valid entry
                    index2 = m.find(".", index1+43)
                    index3 = m.find("\"", index1+43)
                    if index2 != -1 and index3 != -1:
                        tmp = CMediaItem() #create new item
                        tmp.type = 'video'
                        tmp.player = self.player
                    
                        tmp.thumb = "http://images.stage6.com/video_images/" + m[index1+43:index3]
                        tmp.URL= "http://video.stage6.com/" + m[index1+43:index2-1] + "/.divx"
                    
                        #Find the name
                        index4 = m.rfind("href=\"watch?video=")
                        if index4 != -1:
                            index5 = m.find("\">", index4)
                            index6 = m.find("</a>", index4)
                            if index5 != -1 and index6 != -1:
                                tmp.name = m[index5+2:index6]
                    
                        self.list.append(tmp)
                    
            #check if there is a next page in the html
            index1 = data.rfind('class=\"nextpage\"')
            if index1 != -1:
                index2 = data.find('>></a></li>',index1)
                if index2 != -1:
                    index3 = data.find('href=', index1, index2)
                    if index3 != -1:
                        index4 = data.find('\"',index3+6, index2)
                        if index4 != -1:
                            value = data[index3+6:index4]
                            tmp = CMediaItem() #create new item
                            tmp.type = 'html_qsscreen_thumb'
                            tmp.name = 'Next page'
                            tmp.player = self.player
                            tmp.URL = 'http://quicksilverscreen.com/' + value
                    
                            self.list.append(tmp)
                            
        else: #must be 'html_qsscreen_list'
            lines = data.split('\n')   
            for m in lines:
                if m.find("<td class=\"communityColumn videoInfoContainer\">") != -1:
                    break
                index1 = m.find("href=\"videos?c=")
                if index1 != -1:
                    index2 = m.find("\"",index1+15)
                    index3 = m.find("</a><br/>", index1+15)
                    if index2 != -1 and index3 != -1:
                        tmp = CMediaItem() #create new item
                        tmp.type = 'html_qsscreen_thumb'
                        tmp.player = self.player
                        tmp.URL = "http://quicksilverscreen.com/videos?c=" + m[index1+15:index2]
                        #Find the name
                        tmp.name = m[index2+2:index3]
                        
                        self.list.append(tmp)                                                      
        return 0

    ######################################################################
    # Description: Saves a playlist .plx file to disk.
    # Parameters : filename=local path + file name
    # Return     : -
    ######################################################################
    def save(self, filename):
        f = open(filename, 'w')
        f.write('version=' + self.version + '\n')
        f.write('background=' + self.background + '\n')
        f.write('logo=' + self.logo + '\n')
        f.write('title=' + self.title + '\n')
        f.write('player=' + self.player + '\n')
        f.write('#\n')

        for i in range(len(self.list)):
            f.write('type=' + self.list[i].type + '\n')
            f.write('name=' + self.list[i].name + '\n')
            if self.list[i].thumb != 'default':
                f.write('thumb=' + self.list[i].thumb + '\n')
            f.write('URL=' + self.list[i].URL + '\n')
            if self.list[i].player != 'default':
                f.write('player=' + self.list[i].player + '\n')
            if len(self.list[i].DLloc) > 0:
                f.write('DLloc=' + self.list[i].DLloc + '\n')
            f.write('#\n')
        f.close()
        
        