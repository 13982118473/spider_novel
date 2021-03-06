#coding=utf-8
import requests,time,json,pymysql,random,re,os,hashlib,urllib3
from lxml import etree
from config import sql_config,path_config
from xpinyin import Pinyin
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
'''
本代码作用于小说更新,换源更新,自动判断是否连载功能
建议:每天运行1次
'''
class find_err():
    def __init__(self):
        self.s = requests.Session()
        sql_date = sql_config()
        self.conn = pymysql.Connect(
            host=sql_date["host"],
            port=sql_date["port"],
            # 数据库名：
            db=sql_date["db"],
            user=sql_date["user"],
            passwd=sql_date["passwd"],
            charset=sql_date["charset"])
        self.cur = self.conn.cursor()
    def set_is_lianzai(self):
        # -------------100天不更新判断为完本---------------
        self.cur.execute("select max(id) from b_novel")
        max_id=self.cur.fetchone()[0]
        if max_id<5000:max_id=5000
        num=5000
        last_time = int(time.time() - 8640000)
        for start_id in range(0,max_id,num):
            end_id=start_id+num
            up="update b_novel set serialize = 1 where serialize = 0 and id > %s and id <= %s and update_time < %s"
            self.cur.execute(up,(start_id,end_id,last_time))
            self.conn.commit()
        print('判断完本小说成功')

class Update_chapter(object):
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36"}
        self.s=requests.Session()
        sql_date = sql_config()
        self.conn = pymysql.Connect(
            host=sql_date["host"],
            port=sql_date["port"],
            #数据库名：
            db=sql_date["db"],
            user=sql_date["user"],
            passwd=sql_date["passwd"],
            charset=sql_date["charset"])
        self.cur = self.conn.cursor()
        path=path_config()
        self.txt_path=path[1]
        f_m_i = "select max(id) from b_novel"
        self.cur.execute(f_m_i)
        self.max_id = self.cur.fetchone()[0]
    def find_link(self,novel_id):
        ##########################################
        for index_name in [{"index_name":"顶点小说","index_url":"https://www.dingdiann.com"},
                           {"index_name":"奇快中文","index_url":"https://www.7kzw.com"},
                           {"index_name":"新笔趣阁","index_url":"http://www.xbiquge.la"},
                           {"index_name":"爱豆看书","index_url":"https://www.a6ksw.com"},
                           {"index_name":"棉花糖小说网","index_url":"http://www.mhtwx.la"},
                           {"index_name":"笔糗阁","index_url":"https://www.biqiuge.com"},
                           {"index_name":"顶点中文","index_url":"http://www.ddsk.la"},
                           {"index_name":"全本小说网","index_url":"https://www.qb5.tw"},
                           {"index_name":"顶点book","index_url":"https://www.booktxt.com"}]:
            find_link="select url,id from b_source where novel_id = %s and reurl = %s"
            self.cur.execute(find_link,(novel_id,index_name["index_name"]))
            link=self.cur.fetchone()
            if link:return link[0],index_name["index_url"],link[1]
            else:continue
    #获取网页列表
    def index_url_list(self,type3_dict):
        ###############################################################################
        if 'mianhuatang.cc' in type3_dict['link'] or 'mhtwx.la' in type3_dict['link']:
            title_list_xpath = "//div[@class='novel_list']/dl/dd/a/text()"
            url_list_xpath = "//div[@class='novel_list']/dl/dd/a/@href"
            pinjie_url = type3_dict['link']
        elif 'xbiquge.la' in type3_dict['link'] or 'booktxt.com' in type3_dict['link']:
            title_list_xpath = "//div[@id='list']//dd/a/text()"
            url_list_xpath = "//div[@id='list']//dd/a/@href"
            pinjie_url = type3_dict['index_url']
        elif 'biqiuge.com' in type3_dict['link']:
            title_list_xpath = "//div[@class='listmain']//dd[position()>6]/a/text()"
            url_list_xpath = "//div[@class='listmain']//dd[position()>6]/a/@href"
            pinjie_url = type3_dict['index_url']
        elif 'ddsk.la' in type3_dict['link']:
            title_list_xpath = "//table[@id='bgdiv']//div[@class='dccss']/a/text()"
            url_list_xpath = "//table[@id='bgdiv']//div[@class='dccss']/a/@href"
            pinjie_url = type3_dict['index_url']
        elif 'qb5.tw' in type3_dict['link']:
            title_list_xpath = "//div[@class='zjbox']/dl/dd/a/text()"
            url_list_xpath = "//div[@class='zjbox']/dl/dd/a/@href"
            pinjie_url = type3_dict['index_url']
        else:  # 顶点nn,奇快7k,爱豆a6
            title_list_xpath = "//div[@id='list']//dd[position()>12]/a/text()"
            url_list_xpath = "//div[@id='list']//dd[position()>12]/a/@href"
            pinjie_url = type3_dict["index_url"]

        if 'biqiuge.com' in type3_dict['link'] or 'booktxt.com' in type3_dict['link']:charset='gbk'
        elif 'qb5.tw' in type3_dict['link']:charset='gbk'
        else:charset='utf-8'
        if 'a6ksw.com' in type3_dict['link']:time.sleep(random.uniform(0.5,1.2))
        else:time.sleep(random.uniform(0.1,0.2))
        ###############################################################################
        get_list=[]
        type3_res=self.s.get(type3_dict['link'],headers=self.headers,timeout=10,verify=False).content.decode(charset)
        type3_date=etree.HTML(type3_res)
        title_list=type3_date.xpath(title_list_xpath)
        url_list=type3_date.xpath(url_list_xpath)
        try:
            seat=len(title_list)-title_list[::-1].index(type3_dict["new_name"])-1
        except Exception:
            open('update_novel.log', 'a', encoding='utf-8').write('** 更新未匹配到小说:  ' + type3_dict["title"] + '  章节名:{' + type3_dict["new_name"] +'}链接:  '+type3_dict['link']+' 网站获取个数:'+str(len(title_list))+'\n')
            return get_list
        new_num=type3_dict["new_num"]
        if len(title_list) > seat+1:
            for num in range(seat+1,len(title_list)):
                new_num+=1
                title=title_list[num]
                if title[-2:] ==' 新':title = title.replace(' 新','')
                title=title.replace('\n', '').replace('\\','').replace('SM','').replace('AV','').replace('GV','')
                get_dict={"chapter_num":new_num,
                          "chapter_name":title,
                          "chapter_url":pinjie_url+url_list[num]}
                get_list.append(get_dict)
            return get_list
        else:return get_list
        # if len(title_list) == type3_dict["new_num"]:
        #     return get_list
        # else:
        #     #up_num=title_list.index(type3_dict["new_name"])
        #     for num in range(type3_dict["new_num"],len(title_list)):
        #         get_dict={"chapter_num":num+1,
        #                   "chapter_name":title_list[num].replace("'","").replace('"', '').replace('\n', '').replace('\\','').replace('	', '').replace('SM','').replace('AV','').replace('GV',''),
        #                   "chapter_url":pinjie_url+url_list[num],}
        #         get_list.append(get_dict)
        #     return get_list
    #章节ID及本地
    def b_chapter_parse(self, cha_title, cha_content):
        # id处理
        id = str(time.time()) + cha_title + str(random.randint(10000, 100000))
        m = hashlib.md5(id.encode('utf-8'))
        chapter_id_md5 = m.hexdigest()
        # content存text
        base_txt_name = cha_title + str(time.time()) + str(random.randint(10000, 100000))
        m = hashlib.md5()
        m.update(base_txt_name.encode('utf-8'))
        base_txtname_md5 = m.hexdigest() + '.txt'
        cha_time_name = time.strftime("%Y-%m-%d", time.localtime(time.time())).replace('-', '')
        base_txt_path = self.txt_path + cha_time_name
        if not os.path.exists(base_txt_path):
            os.mkdir(base_txt_path)
        open(base_txt_path + '/' + base_txtname_md5, 'w', encoding='utf-8').write(cha_content)
        content_txt_path = '/upload/chapter_txt/'+cha_time_name + '/' + base_txtname_md5
        return chapter_id_md5,content_txt_path
    def header(self):
        UA_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            "Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident / 5.0",
            "Mozilla/4.0(compatible;MSIE8.0;WindowsNT6.0;Trident/4.0)",
            "Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;360SE)",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
            "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36",
            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0(Macintosh;IntelMacOSX10.6;rv:2.0.1)Gecko/20100101Firefox/4.0.1"]
        UA = random.choice(UA_list)
        return UA
    def parse_type3(self,sql_list,position):
        for type3_dict in sql_list:
            if type3_dict['link'] ==None or type3_dict['source_id'] == None:
                continue
            try:
                get_list=self.index_url_list(type3_dict)
            except Exception as e:
                print('**提取错误: id:',type3_dict['id'],' 小说名: ',type3_dict['title'],type3_dict['link'],e)
                open('update_novel.log','a', encoding='utf-8').write('**提取错误: id:'+str(type3_dict['id'])+'  小说名: '+type3_dict['title']+'  链接:'+type3_dict['link']+position+str(e)+'\n')
                continue
            if len(get_list)==0:
                print(type3_dict['title'],'无更新章节')
                continue
            print('获取到小说:',type3_dict['title'],len(get_list),'章更新....')
            new_novel_word=0 #更新章节总字数
            weigh=type3_dict["new_num"]  #  更新前总章节数
            try:
                #抓取更新章节
                for get_dict in get_list:
                    ###################################################################
                    if 'mianhuatang.cc' in type3_dict['link'] or 'mhtwx.la' in type3_dict['link']:
                        content_xpath ="//div[@class='content']/text()"
                    else:content_xpath ="//div[@id='content']/text()"
                    if 'biqiuge.com' in type3_dict['link'] :charset = 'GB18030'
                    elif 'qb5.tw' in type3_dict['link'] or 'booktxt.com' in type3_dict['link'] :charset='gbk'
                    else:charset='utf-8'
                    ###################################################################
                    headers = {"User-Agent": self.header()}
                    cha_url = get_dict['chapter_url']
                    if 'a6ksw.com' in cha_url:time.sleep(random.uniform(0.4,0.6))
                    else:time.sleep(random.uniform(0.09,0.29))
                    type4_res=self.s.get(cha_url,headers=headers,timeout=10,verify=False).content.decode(charset)
                    type4_date=etree.HTML(type4_res)
                    chapter_title=get_dict["chapter_name"]
                    for weigui in ["军婚", "军嫂", "军政", "高干", "党中央", "黑道", "黑帮", "校霸", "做爱", "爱爱", "很疼", "打炮", "约炮",
                               "野合", "口交", "乳交", "肛交", "爆菊花","手淫", "打飞机", "一夜情", "女上男下", "身下承欢", "胯下承欢",
                               "活在裆下", "轻点喘", "师生恋", "兄妹恋", "掰弯", "同性恋", "搞基", "妓院", "嫖客", "处女", "强奸", "乱伦", "迷奸", "艹我",
                               "老公我还要", "睡服你", "狗日", "皇权富贵", "农坤", "杰佣", "凯源", "凯千", "勋鹿", "张云雷杨九郎", "魔道祖师", "天官赐福",
                               "自杀", "共产党", "血腥", "你妈","尼玛","草泥马","曹尼玛"]:
                        if weigui in chapter_title:
                            chapter_title=chapter_title.replace(weigui,Pinyin().get_pinyin(weigui, ''))
                    chapter_content = type4_date.xpath(content_xpath)
                    # 处理章节内容
                    content=''
                    weigh+=1
                    print(weigh,'正在更新:',chapter_title,cha_url)
                    for br in chapter_content:
                        content+=' '+br.strip().replace('\n','')+'\n'
                    for delete in ['\'','"','小美~正在手打中，请稍等片刻，','内容更新后，需要重新刷新页面，才能获取最新更新！', '纯文字在线阅读本站域名','手机同步阅读请访问',
                                   '章节错误,点此举报(免注册)', ',举报后维护人员会在两分钟内校正章节内容,请耐心等待,并刷新页面。', '|　|　　->　->',
                                   '最新网址：www.ddxsku.com', 'Ｅ』┡　小说Ｗｗ', '看完记得：方便下次看，或者。', '最新全本：、、、、、、、、、、', '：。：',
                                   '天才一秒记住本站地址:(顶点中文)www.ddsk.la,最快更新!无广告!', '看完记得：方便下次看，或者。',
                                   '天才一秒记住本站地址[奇快中文网]', 'https://www.7kzw.com/最快更新！无广告！',
                                   'xbiquge.la', ' 新笔趣阁','内容更新后，请重新刷新页面，即可获取最新更新！','正在手打中，请稍等片刻，','高速全文字在线阅读！',
                                   '最新网址：www.mhtwx.la','c_t();','一秒记住【棉花糖小说网www.mhtwx.la】，为您提供精彩小说阅读。','手机用户可访问wap.mhtwx.la观看小说，跟官网同步更新．',
                                   '天才一秒记住本站地址：[爱豆看书]','https://www.a6ksw.com/最快更新！无广告！','正在手打更新中，敬请期待。','章节错误,点此报送(免注册)','报送后维护人员会在两分钟内校正章节内容,请耐心等待。',
                                    cha_url,'请记住本书首发域名：biqiuge.com。笔趣阁手机版阅读网址：wap.biqiuge.com',
                                   '顶点中文全文字更新,牢记网址:www.ddsk.la', '顶点中文', 'www.ddsk.la', '手机用户请浏览阅读，更优质的阅读体验。',
                                   '全本小说网 WWW.QB5.TW，最快更新', '最新章节！', '一秒记住【??】，為您提供精彩小说阅读。',type3_dict['title'],'天才一秒记住本站地址：','推荐都市大神老施新书:'
                                   ]:
                        content=content.replace(delete,'')
                    content = re.compile('<[^>]+>', re.S).sub('', content)
                    # print(content)
                    word = len(content)  # 章节字数
                    #文本存本地,返回ID,path
                    chapter_date=self.b_chapter_parse(get_dict["chapter_name"],content)
                    # 状态
                    status = 1
                    if word < 15:
                        status = 0
                        open('update_novel.log','a',encoding='utf-8').write(str({"字数错误ID":type3_dict["id"],"错误小说名":type3_dict["title"],"错误章节名":get_dict["chapter_name"],"链接":cha_url,"hot":position})+'\n')
                    chapter_l_num = type3_dict["id"] // 1000 + 1
                    chapter_dbname='b_chapter_{}'.format(str(chapter_l_num))
                    # b_chapter入库
                    insert_chapter = "insert into {}(id,novel_id,title,content,status,update_time,weigh,word) values(%s,%s,%s,%s,%s,%s,%s,%s)".format(chapter_dbname)
                    self.cur.execute(insert_chapter, (
                                     chapter_date[0], type3_dict["id"], get_dict["chapter_name"], chapter_date[1], status, time.time(),get_dict["chapter_num"], word))
                    # source分表更新入库
                    source_dbname = 'b_source_list_{}'.format(str(type3_dict["source_id"]//500+1))
                    source_l_id=chapter_title+str(time.time())+str(random.randint(10000,100000))
                    m = hashlib.md5(source_l_id.encode('utf-8'))
                    source_id_md5 = m.hexdigest()
                    insert_source_l = "insert into %s(id,chapter_num,chapter_name,chapter_url,source_id) values('%s',%s,'%s','%s',%s)" % (
                                       source_dbname, str(source_id_md5), get_dict["chapter_num"],chapter_title ,cha_url,type3_dict["source_id"])
                    self.cur.execute(insert_source_l)
                    #add总字数
                    new_novel_word += word
                #source更新入库
                update_source="update b_source set chapter_sum = %s , update_time =%s , chapter_name =%s where novel_id =%s and id =%s "
                self.cur.execute(update_source,(
                               get_dict["chapter_num"],time.time(),get_dict["chapter_name"],type3_dict["id"],type3_dict["source_id"]))
                #b_novel更新入库
                new_word=new_novel_word+type3_dict['word']
                update_novel="update b_novel set update_time = %s , word=%s , new_name=%s ,new_num=%s where id= %s"
                self.cur.execute(update_novel,(time.time(),new_word,get_dict["chapter_name"],get_dict["chapter_num"],type3_dict['id']))
                self.conn.commit()
                # #type3本地
                # #self.type3_save_local(add_title,add_url,type3_dict)
            except Exception as e:
                print('**更新错误',type3_dict['title'],get_dict['chapter_url'],e)
                open('update_novel.log', 'a', encoding='utf-8').write('**更新错误'+type3_dict['title']+get_dict['chapter_url']+position+str(e)+'\n')
                continue
    def run(self,max_num):
        t1 = time.time()
        open('update_novel.log','a',encoding='utf-8').write('-------------'+str(datetime.now())[0:19]+'  执行小说更新任务--------\n')
        end_num=self.max_id//max_num+1
        update_novel_num = 0
        for number in range(0,max_num+1):
            # 取数据库信息[{id:1,title:XXX},...]
            try:
                if number ==0:
                    f_novel = "select id,title,word,new_num,new_name from b_novel where serialize = 0 and status = 1 and position = 1"
                    self.cur.execute(f_novel)
                    date_t = self.cur.fetchall()
                    position='热门小说'
                else:
                    f_novel = "select id,title,word,new_num,new_name from b_novel where serialize = 0 and status = 1 and position = 0 and id > %s and id <= %s" % ((number-1)*end_num,number*end_num)  # and id <10"
                    self.cur.execute(f_novel)
                    date_t = self.cur.fetchall()
                    position=' '
                    #date_t=random.sample(date_t,len(date_t)//10*8+1)
            except Exception:continue
            sql_list = []
            for t in date_t:#tuple:
                sql_dict = {}
                sql_dict["id"] = t[0]
                sql_dict["title"] = t[1]
                sql_dict["word"] = t[2]
                sql_dict["new_num"] = t[3]
                sql_dict["new_name"] = t[4]
                try:
                    source_date = self.find_link(t[0])
                    sql_dict["link"] = source_date[0]
                    sql_dict["index_url"] = source_date[1]
                    sql_dict["source_id"] = source_date[2]
                except Exception:
                    sql_dict["link"] = None
                    sql_dict["index_url"] = None
                    sql_dict["source_id"] = None
                sql_list.append(sql_dict)
            sql_list_num=len(sql_list)
            print('-------------------第',number+1,'次更新:',sql_list_num,'本小说-------------------------------')
            self.parse_type3(sql_list,position)
            update_novel_num += sql_list_num
            if time.time()-t1 > 9000:
                break
        when_time = (time.time()-t1)/60
        open('update_novel.log','a', encoding='utf-8').write('-------------'+str(datetime.now())[0:19]+'  更新结束,共更新:'+str(number+1)+'次'+ str(update_novel_num) +'本小说,耗时:'+str(float('%.2f' %when_time)) +'分钟--------\n')
        print('-------------'+str(datetime.now())+'更新结束,共更新:'+str(number+1)+'次'+ str(update_novel_num) +'本小说,耗时:'+str(float('%.2f' %when_time)) +'分钟--------')

class Update_source(object):
    def __init__(self):
        sql_date = sql_config()
        self.conn = pymysql.Connect(
            host=sql_date["host"],
            port=sql_date["port"],
            #数据库名：
            db=sql_date["db"],
            user=sql_date["user"],
            passwd=sql_date["passwd"],
            charset=sql_date["charset"])
        self.cur = self.conn.cursor()
        f_m_i = "select max(id) from b_novel"
        self.cur.execute(f_m_i)
        self.max_id = self.cur.fetchone()[0]
    def sql_date(self,max_num):
        open('update_novel.log','a',encoding='utf-8').write('#########'+str(datetime.now())[0:19]+'  执行换源更新任务########\n')
        end_num = self.max_id // max_num + 1
        t1=time.time()
        for number in range(0,max_num):
            sql_date="select id,title from b_novel where status=1 and serialize = 0 and id >%s and id <=%s" %(number*end_num,(number+1)*end_num)
            self.cur.execute(sql_date)
            sql_novel=self.cur.fetchall()
            for id_title in sql_novel:
                find_sql_url="select id,url,chapter_sum,chapter_name from b_source where novel_id= %s "
                self.cur.execute(find_sql_url,id_title[0])
                id_url_t =self.cur.fetchall()
                if len(id_url_t)>1:
                    #print(1, id_url_t)
                    try:
                        self.source_parse(id_url_t,id_title[1])
                    except Exception as e:
                        open('update_novel.log', 'a', encoding='utf-8').write('**换源更新失败'+str(id_title[0])+id_title[1]+str(e)+'\n')
                        print('**换源更新失败,id:',id_title[0],'小说名:',id_title[1],e)
                        continue
            if time.time()-t1 > 9000:break
        when_time = (time.time() - t1) / 60
        open('update_novel.log', 'a', encoding='utf-8').write('#########'+str(datetime.now())[0:19]+'  结束换源更新任务,耗时:'+str(float('%.2f' %when_time))+'分钟########\n')


    def source_parse(self,id_url_t,novel_name):
        for id_url in id_url_t:
            source_id,url,last_chapter_sum,last_chapter_name = id_url[0],id_url[1],id_url[2],id_url[3]
            if 'boquge.com' in url:
                pinjie_url,title_xpath, url_xpath, charset ,index_name = 'https://www.boquge.com','//ul[@id="chapters-list"]//a/text()','//ul[@id="chapters-list"]//a/@href','gbk','笔趣阁2'
            elif 'pingshuku.com' in url:
                pinjie_url,title_xpath, url_xpath, charset ,index_name= url,'//div[@class="dccss"]/a/text()','//div[@class="dccss"]/a/@href','utf-8','56书库'
            else:continue
            try:
                if 'boquge.com' in url:random.uniform(0.5,1.2)
                else:time.sleep(random.uniform(0.09,0.2))
                res=requests.get(url,headers=self.header(),verify=False,timeout=10).content.decode(charset)
            except Exception as e:
                open('update_novel.log', 'a', encoding='utf-8').write('**换源更新失败,小说名:' + novel_name + '  '+ url+ str(e) + '\n')
                print('**换源更新失败,小说名:',index_name,url,e)
                continue
            date=etree.HTML(res)
            title_list= date.xpath(title_xpath)
            url_list  = date.xpath(url_xpath)
            try:
                seat=len(title_list)-title_list[::-1].index(last_chapter_name)-1
            except Exception :
                open('update_novel.log','a', encoding='utf-8').write('**换源未匹配到小说:{'+novel_name+'}章节名:{'+last_chapter_name+'}链接: '+url+' 网站获取个数:'+str(len(title_list))+'\n')
                self.repair_source_last_cha(source_id,last_chapter_sum)
                continue
            if len(title_list) > seat+1:
                for num in range(seat+1,len(title_list)):
                    last_chapter_sum+=1
                    title = title_list[num]
                    if title[-2:] == ' 新': title = title.replace(' 新','')
                    title = title.replace('\n', '').replace('\\', '').replace('\'', '')
                    get_dict={"chapter_num":last_chapter_sum,
                              "chapter_name":title,
                              "chapter_url":pinjie_url+url_list[num]}
                    self.source_in_sql(source_id,get_dict)
                update_source="update b_source set update_time = %s,chapter_sum = %s, chapter_name= %s where id = %s"
                self.cur.execute(update_source,(time.time(),get_dict["chapter_num"],get_dict["chapter_name"],source_id))
                self.conn.commit()
                print(novel_name,index_name,'换源更新成功')
            # if len(title_list) > last_chapter_sum:
            #     for num in range(last_chapter_sum,len(title_list)):
            #         get_dict={"chapter_num":num+1,
            #                   "chapter_name":title_list[num].replace("'","").replace('"', '').replace('\n', '').replace('\\','').replace('	', ''),
            #                   "chapter_url":pinjie_url+url_list[num],}
            #         self.source_in_sql(source_id,get_dict)
            #     update_source="update b_source set update_time = %s,chapter_sum = %s, chapter_name= %s where id = %s"
            #     self.cur.execute(update_source,(time.time(),get_dict["chapter_num"],get_dict["chapter_name"],source_id))
            #     #self.conn.commit()
            #     print(novel_name,index_name,'换源更新成功')
            elif len(title_list) == seat+1:
                print(novel_name,index_name,'换源无更新')
            else:
                print('***err',novel_name,index_name,'网站个数:',len(title_list),'数据库个数:',last_chapter_sum,url)
                open('update_novel.log','a', encoding='utf-8').write('***err小说名:  '+novel_name+'  网站获取个数:'+str(len(title_list))+'  数据库个数:'+str(last_chapter_sum)+'  错误网址:'+url+'\n')

    def repair_source_last_cha(self,source_id, last_chapter_sum):
        try:
            source_l_name = 'b_source_list_{}'.format(str(source_id // 500 + 1))
            delete_last_cha = "delete from {} where chapter_num= %s and source_id = %s".format(source_l_name)
            self.cur.execute(delete_last_cha, (last_chapter_sum, source_id))
            find_last_date = "select chapter_num,chapter_name from {} where source_id=%s ORDER BY chapter_num desc LIMIT 1".format(source_l_name)
            self.cur.execute(find_last_date, (source_id,))
            max_num_name = self.cur.fetchone()
            update_source = "update b_source set chapter_sum=%s,chapter_name=%s where id = %s"
            self.cur.execute(update_source, (max_num_name[0], max_num_name[1], source_id))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
    def source_in_sql(self,source_id,get_dict):
        source_l_name='b_source_list_{}'.format(str(source_id//500+1))
        source_l_id = get_dict["chapter_name"] + str(time.time()) + str(random.randint(1000, 10000))
        m = hashlib.md5(source_l_id.encode('utf-8'))
        source_id_md5 = m.hexdigest()
        insert_source_l = "insert into %s(id,chapter_num,chapter_name,chapter_url,source_id) values('%s',%s,'%s','%s',%s)" % (
            source_l_name, str(source_id_md5), get_dict["chapter_num"], get_dict["chapter_name"],get_dict["chapter_url"], source_id)
        self.cur.execute(insert_source_l)
        #print(222,source_l_name, str(source_id_md5), get_dict["chapter_num"], get_dict["chapter_name"],get_dict["chapter_url"], source_id)
    def header(self):
        UA_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            "Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident / 5.0",
            "Mozilla/4.0(compatible;MSIE8.0;WindowsNT6.0;Trident/4.0)",
            "Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;360SE)",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
            "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36",
            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0(Macintosh;IntelMacOSX10.6;rv:2.0.1)Gecko/20100101Firefox/4.0.1"]
        UA={ "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language":"zh-CN,zh;q=0.9",
             "User_Agent":random.choice(UA_list)}
        return UA

# find_err().set_is_lianzai()
#Update_chapter().run(8)
#Update_source().sql_date(8)
