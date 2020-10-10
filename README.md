# homework-system

一.环境介绍
1.运行环境 Python3.6
2.后台框架：Tornado
3.前端ui框架：妹子UI


二.目录介绍
  -static
  -template
  app.py
  compat.py
  qiniuyun.py
  utils.py
  requestments.txt
  
static为静态资源目录，存放css.js等资源；
template为前端html文件；
app.py为后台项目的主要文件，包含路由配置，项目运行配置，后台API接口逻辑处理；
compat.py,utils.py,qiniuyun.py是七牛云提供的python上传文件的Demo。


二.项目环境配置
基于Python3.6，安装项目运行环境：pip install -r requirements.txt


三.项目运行配置
要使该项目运行起来主要需要配置你的数据库：在app.py文件中，第16行处配置你的数据库信息；
另外由于上传的文件被存储在第三方资源服务器（七牛云），所以你需要创建属于自己的七牛云账号（创建教程：https://blog.yellow948.cn/article/49/) 在app.py第254行处填写你的七牛云的授权码；
其他配置：在项目全局搜索"fix me"是项目运行必须的配置，"start fix"主要是数据库语句的修改，若你的数据库表设计与项目不符合，你可以修改相应的数据库语句已让后台业务逻辑能够正常运行。


四.项目运行
进入项目根目录，执行 python app.py，访问 http://127.0.0.1:5003 进入学生端，http://127.0.0.1:5003/admin 进入管理员端


五.其他
数据库表的字段展示：
students: id,stu_name,stu_num_gdit
homework: id,title,status,describe,create_time,deadline,addtional_name
upload_list: id,stu_name,stu_num,is_upload,upload_time,homework_id,url
