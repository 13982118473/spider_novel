运行环境:
    Python3.7   
    pip3    (python包管理工具)

安装包(pip3 install 包名):
    requests
    lxml
    pymysql
    scrapy   如安装scrapy 出现错误请参照: (一般会报错,需安装 Twisted 和 VS ++)
	 https://blog.csdn.net/chitian6393/article/details/100726695
	 或者百度自行更改!!!

文件说明:
	xs1t
	       项目文件 
		config.py
			配置文件,数据库配置,路径配置
			数据库配置:在5-10行设置数据库参数 
				host       (域名)
				db          (表名)
				user        (用户名)
				passwd   (密码)
			路径配置:
				在15行配置封面路径  结尾必须为:/upload/novel_img/
				在16行配置章节路径  结尾必须为:/upload/chapter_txt/
			url_txt配置
			    在20行配置要爬取的txt文件名,目前有2个,见下面
		run.py
			****执行脚本,进入python环境直接运行此脚本

		new_book.sql 
			新版数据库文件,需运行此文件到数据库
		
        upload
			小说封面及章节存放文件夹,里面的内容需要给安卓端及后台访问权限
                                                注:(1):API接口远程访问格式:API接口域名+文件路径
                                                    (2):后端操作默认该文件夹为项目运行目录根目录  
		xs1t
			爬虫框架代码
		all.log       
			爬虫日志文件,存储报错信息,请求异常存储文件
		err.txt
			存储断章或者小说内容为空时存储文件
		url.txt	
			存放6万条爬取的URL
		add_url.txt
		    存放新增的URL
		start_num.txt
			记录已经爬取的小说数量(****爬虫开始的起始值****)
			


'''
小说爬虫:
一.小说新增主框架
    采用python-scrapy异步框架获取目标小说网站,挑选无版权小说单独获取入库,并与有版权小说区分
    
二.新增实现功能
    1.自动去重功能:⑴在URL传递进scrapy框架时去重,使得同一时间不会执行同一小说
                  ⑵在小说入库时,自动判断小说名与作者名不得与数据库已有小说重复(同小说名不同作者名允许入库)
                  ⑶在章节入库时,自动判断章节数,同一小说同一章节数不得入库
    2.封面获取功能:自动获取小说封面,如获取失败将为空
    3.自动去除广告功能:手动获取目标网站同一广告、相似广告,代码自动去除
    4.自动去除违规字符:手动获取违规/违章字符,如小说名出现该字符直接不获取当前小说,如章节名出现该字符,以字符拼音替换掉
    5.自动替换格式:获取的小说章节名/小说章节内容的格式自动替换成前端需要的格式,并删除多余格式,如:换行符,缩进符....
    6.状态判断:⑴根据章节内容/章节数自动判断小说状态是否正常
              ⑵根据章节内容/章节名自动判断章节状态是否正常
    7.连载判断:根据最后更新时间自动判断该小说是否为连载
    8.获取最新信息:代码将自动在目标页head标签里获取该小说的最新章节,最新更新时间,并对比最新章节数
    9.随机评分:小说在入库时会自动设置该小说的评分随机数
   10.随机收藏数:小说在入库时会自动设置该小说的收藏随机数(20-100)
   11.自动判断章节内容字数:在爬取过程中,如果发现章节字数不合理,将记录在日志里,并且当前章节状态为禁用
   12.网络监测:在每一本小说爬取开始前,将测试网络状态,如断网或者网络异常,爬虫程序将等待网络恢复后自动开始
   13.断点修复:如爬虫程序在运行过程中突发断网或者终止,那么下次运行时会自动重新修复上次未完成的小说章节
   14.反爬机制:⑴每次请求时自动带上请求头
              ⑵创建User-Agent池,使每次请求时不会出现同一请求头
              ⑶时间间隔,每次请求时间随机间隔在0.1-1.2秒之间
              ⑷建立IP代理池,使每次请求时的IP不一样
   15.请求超时处理:如发现某一页面请求超时,将在3分钟内重新请求3次,如未成功将记录在日志
   16.请求异常处理:如发现某一页面请求异常或拒绝访问,将网址和状态码、异常记录在日志
   
   **因部分小说目标网站出现章节内容不全/无章节/部分广告现象,代码会自动记录,需编辑人员手动修复
        **建议:实现用户举报章节错误功能
   
三.小说更新机制
    采用python-requests分布式更新连载小说,并优先更新热门小说

四.小说更新功能
    1.优先执行热门小说更新,再分批次取出普通小说更新,内存占用小
    2.设置定时功能:每天凌晨3点开始更新计划任务,并且更新不超过3个小时
    3.对比源网址功能:依次将小说最新章节名与源网址小说章节名进行对比,如发现有新的章节则获取,否则显示无更新
    4.章节内容状态判断:自动获取章节字数,如发现字数异常将记录日志并且状态为异常
    5.自动去除违规字符:如章节名出现违规字符,以字符拼音替换掉
    6.自动去除广告功能:手动获取目标网站同一广告、相似广告,代码自动去除
    7.自动替换格式:获取到小说章节内容格式自动替换成前端需要的格式,并删除多余格式,如:换行符,缩进符....
    8.章节数自增长功能:每次检测出小说有更新时,将在数据库原最新章节数的基础上更新章节数
    9.小说总字数自增长:次检测出小说有更新时,将在数据库原总字数数的基础上更新总章节字数
   10.主页换源更新功能:当检测到小说有章节更新时,同时会自动更新源网站换源数据并分表入库 
   11.请求超时处理:如发现某一页面请求超时,将在3分钟内重新请求3次,如未成功将记录在日志
   12.请求异常处理:如发现某一页面请求异常或拒绝访问,将网址和状态码、异常记录在日志
   
    **无版权小说每日更新,因考虑到目标网站后台会改变小说章节名或禁用某章节,导致无法及时更新,代码会自动记录下状态,需要编辑人员每日进行后台手动检查(工作量:1-2小时)
五.其他换源功能:
    针对性分类APP(盗版)是否实现换源功能?
    当前小说宝功能已有其他换源功能,机制与需求和小说更新类似
'''