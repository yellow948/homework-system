# -*- coding:utf8 -*-
import tornado.ioloop
import tornado.web

from tornado.web import StaticFileHandler
import os
import json
import pymysql
from pymysql.cursors import DictCursor                
import time

import qiniuyun

# mysql connect
# fix me
conn = pymysql.connect(host="", user="", password="", database="", charset="utf8")

# session obj
container = {} 


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        ''' 获取前端cookie，若session obj存在则直接跳转上传页面 '''
        hq_cookie = self.get_cookie('student_cookie', None)
        session = container.get(hq_cookie, None)
        if session is None:
            self.render("template/login.html")
        else:
            self.render("template/student.html")


class GetUploadStatus(tornado.web.RequestHandler):
    def get(self):
        hid = self.get_query_argument("hid", "")
        hq_cookie = self.get_cookie('student_cookie', None)
        session = container.get(hq_cookie, None) 
        # start fix
        cursor = conn.cursor(DictCursor)
        sql = '''
            SELECT is_upload,upload_time,stu_name FROM upload_list WHERE stu_num=%s AND homework_id=%s
        ''' % (session['stu_num'], hid)
        cursor.execute(sql)
        res = cursor.fetchall()
        cursor.close()
        # end fix
        self.set_header("Content-Type", "application/json; charset=UTF-8")  
        self.write({'data': res, 'code': 200})


class LoginHandle(tornado.web.RequestHandler):
    def post(self):
        ''' 登录逻辑：验证信息通过后，生成MD5密钥作为session_key存到前端cookie '''
        stu_num = self.get_body_argument("stu_num", "")
        stu_name = self.get_body_argument("stu_name", "")
        self.set_header("Content-Type", "application/json; charset=UTF-8")   
        if stu_name and stu_num:
            # start fix
            cursor = conn.cursor()
            sql = '''
                SELECT * FROM students WHERE stu_name='%s' AND stu_num_gdit='%s'
            ''' % (stu_name, stu_num)
            res = cursor.execute(sql)
            cursor.close()
            # end fix
            if res == 1:
                import hashlib 
                md5 = hashlib.md5()
                md5.update(bytes(str(stu_name), encoding="utf-8"))
                cookie = md5.hexdigest()
                self.set_cookie('student_cookie', cookie, expires_days=15)
                stu_sex = cursor.fetchone()
                container[cookie] = { 'stu_num': stu_num, 'stu_name': stu_name, 'sex': stu_sex[8]}
                self.write({'code': 200})
            else:
                self.write({'code': 400})
        else:
            self.write({'code': 400})


class AdminLoginHandle(tornado.web.RequestHandler):
    def post(self):
        code = self.get_body_argument('code', 0)
        # fix me
        if code == "your admin code":
            import hashlib 
            md5 = hashlib.md5()
            md5.update(bytes(str(code), encoding="utf-8"))
            cookie = md5.hexdigest()
            self.set_cookie('admin_cookie', cookie, expires_days=7)
            self.write({'code': 200})
        else:
            self.write({'code': 400})


class AdminHandle(tornado.web.RequestHandler):
    def get(self):
        hq_cookie = self.get_cookie('admin_cookie', None)
        if hq_cookie is None:
            self.render("template/admin-login.html")
        else:
            import hashlib 
            md5 = hashlib.md5()
            # fix me
            md5.update(bytes(str("your admin code"), encoding="utf-8"))
            cookie = md5.hexdigest()
            if cookie == hq_cookie:
                self.render("template/admin.html")
            else:
                self.clear_cookie('admin_cookie')
                self.render("template/admin-login.html")

    def post(self):
        hid = int(self.get_body_argument('hid', 0))
       
        # start fix
        cursor = conn.cursor()
        sql = '''
            DELETE FROM homework WHERE id=%s
        ''' % (hid)
        cursor.execute(sql)
        conn.commit()

        sql = """
            DELETE FROM upload_list WHERE homework_id=%s
        """ % (hid)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        # end fix
        
        self.set_header("Content-Type", "application/json; charset=UTF-8")  
        self.write({'code': 200})


class HomeworkHandle(tornado.web.RequestHandler):
    def get(self):
        now = str(time.time()).split(".")[0]

        page = self.get_query_argument("page", 1)
        limit = self.get_query_argument("limit", 10)
        page = (int(page) - 1) * int(limit)

        # start fix
        cursor = conn.cursor(DictCursor)

        # 检查到期
        sql_1 = '''
            SELECT * FROM homework WHERE deadline != 0 AND status = 1 ORDER BY id DESC LIMIT %s,%s
        ''' % (page, limit)
        cursor.execute(sql_1)
        res1 = cursor.fetchall()
        for i in res1:
            create_time = int(i['create_time'])
            day = int((int(now) - create_time) / (24 * 3600))
            if i['deadline'] < day:
                sql_2 = """
                    UPDATE homework SET status=0 WHERE id=%s
                """ % (i['id'])
                cursor.execute(sql_2)
                conn.commit()

        sql = '''
            SELECT * FROM homework ORDER BY id DESC LIMIT %s,%s
        ''' % (page, limit)

        hq_cookie = self.get_cookie('student_cookie', None)
        session = container.get(hq_cookie, None)
        if session is not None:
            sql = '''
                SELECT * FROM homework AS h LEFT JOIN upload_list AS ul ON ul.homework_id=h.id WHERE ul.stu_num='%s' ORDER BY h.id DESC LIMIT %s,%s
            ''' % (session['stu_num'], page, limit)

        cursor.execute(sql)
        res = cursor.fetchall()

        cursor.close()
        # end fix

        self.set_header("Content-Type", "application/json; charset=UTF-8")  
        if session is not None:
            self.write({'data': res, 'code': 200, 'info': session, 'now': now})
        else:
            self.write({'data': res, 'code': 200})
        

class UploadListHandle(tornado.web.RequestHandler):
    def get(self):
        hid = self.get_query_argument("hid", "")
        self.set_header("Content-Type", "application/json; charset=UTF-8")  
        if hid:
            hid = int(hid)
            # start fix
            cursor = conn.cursor(DictCursor)
            sql = '''
                SELECT * FROM upload_list WHERE homework_id=%s ORDER BY stu_num ASC 
            ''' % (hid)
            cursor.execute(sql)
            res = cursor.fetchall()
            cursor.close()
            # end fix
            self.write({'data': res, 'code': 200})
        else:
            self.write({'code': 400})


class AddHomeworkHandle(tornado.web.RequestHandler):
    def get(self):
        self.render("template/add-homework.html")

    def post(self):
        ''' 提交作业，同时创建一个班级名单，默认设置待提交 '''
        title = self.get_body_argument('title', '')
        deadline = self.get_body_argument('deadline', '')
        addtional_name = self.get_body_argument("addtional_name", '')
        describe = self.get_body_argument("describe", '')
        if title:
             # start fix
            cursor = conn.cursor()
            sql = '''
                INSERT INTO homework (title,deadline,addtional_name,`describe`,create_time) VALUE ('%s', '%s', '%s', '%s', '%s')
            ''' % (title, deadline, addtional_name, describe, str(time.time()).split(".")[0])
            cursor.execute(sql)
            conn.commit()

            homework_id = int(cursor.lastrowid)
            sql_1 = """
                SELECT * FROM students ORDER BY stu_num_gdit ASC
            """
            cursor.execute(sql_1)
            res = list(cursor.fetchall())
            
            sql_2 = "INSERT INTO upload_list (stu_name,stu_num,homework_id) VALUES ('%s', '%s', %s)" % (res[0][2], res[0][11], homework_id)
            for i in res[1:20]:
                sql_2 += ",('%s', '%s', %s)" % (i[2], i[11], homework_id)
            cursor.execute(sql_2)
            conn.commit()

            sql_2 = "INSERT INTO upload_list (stu_name,stu_num,homework_id) VALUES ('%s', '%s', %s)" % (res[20][2], res[20][11], homework_id)
            for i in res[21:]:
                sql_2 += ",('%s', '%s', %s)" % (i[2], i[11], homework_id)
            cursor.execute(sql_2)
            conn.commit()

            cursor.close()
            # end fix

        self.redirect("/admin")


class UploadFileHandle(tornado.web.RequestHandler):
    def get(self):
        ''' 获取七牛云上传的凭证 '''
        # fix me
        auth = qiniuyun.Auth('AccessKey', "SecretKey")
        bucket = auth.upload_token(bucket="gdit")  
        self.write(bucket)

    def post(self):
        ''' 保存上传记录 '''
        url = self.get_body_argument("url", "")
        hid = int(self.get_body_argument("hid", 0))
        hq_cookie = self.get_cookie('student_cookie', None)
        session = container.get(hq_cookie, None) 
        stu_num = session['stu_num']

        import time
        # start fix
        cursor = conn.cursor()
        sql = '''
            UPDATE upload_list SET is_upload=1,upload_time='%s',url='%s' WHERE stu_num='%s' AND homework_id=%s
        ''' % (str(time.time()).split(".")[0], url, stu_num, hid)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        # end fix

        self.set_header("Content-Type", "application/json; charset=UTF-8")    
        self.write({'code': 200})
   

class LogoutHandle(tornado.web.RequestHandler):
    def post(self):
        self.clear_cookie("student_cookie")
        self.set_header("Content-Type", "application/json; charset=UTF-8")  
        self.write({'code': 200})


class EditHomeworkHandle(tornado.web.RequestHandler):
    def get(self):
        self.render("template/edit-homework.html")

    def post(self):
        hid = self.get_body_argument("id", "")
        title = self.get_body_argument("title", "")
        describe = self.get_body_argument("describe", "")

        # start fix
        cursor = conn.cursor(DictCursor)
        sql = '''
            UPDATE homework SET title="%s", `describe`="%s" WHERE id=%s
        ''' % (title, describe, hid)

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        # end fix

        self.redirect("/admin")


class HomeworkStatusHandle(tornado.web.RequestHandler):
    def post(self):
        hid = self.get_body_argument("id", "")
        status = self.get_body_argument("changeS", "")

        # start fix
        cursor = conn.cursor(DictCursor)
        sql = '''
            UPDATE homework SET status=%s WHERE id=%s
        ''' % (int(status), hid)

        cursor.execute(sql)
        conn.commit()
        cursor.close()
        # end fix


# 路由配置
def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r'/admin', AdminHandle),
            (r'/admin/add-homework', AddHomeworkHandle),
            (r'/admin/edit-homework', EditHomeworkHandle),

            (r'/api/v1/login', LoginHandle),
            (r'/api/v1/addHomework', AddHomeworkHandle),
            (r'/api/v1/getHomework', HomeworkHandle),
            (r'/api/v1/getUploadList', UploadListHandle),
            (r'/api/v1/uploadStatus', GetUploadStatus),
            (r"/api/v1/upload", UploadFileHandle),
            (r'/api/v1/getBucket', UploadFileHandle),
            (r'/api/v1/delHomework', AdminHandle),
            (r'/api/v1/adminLogin', AdminLoginHandle),
            (r'/api/v1/logout', LogoutHandle),
            (r'/api/v1/editHomework', EditHomeworkHandle),
            (r'/api/v1/changeStatus', HomeworkStatusHandle),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True
    )


# 启动项目
if __name__ == "__main__":
    print("app run listen on 5003")
    app = make_app()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(5003)
    tornado.ioloop.IOLoop.current().start()
