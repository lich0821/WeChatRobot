import datetime
import os
import signal
import sqlite3
import threading

from flask import Flask, redirect, render_template, request, url_for
from wcferry import Wcf, WxMsg

from configuration import Config


def init_permission(wcf: Wcf, config: Config):
    # permission: 
    # 0->群聊和私聊都不响应
    # 1->群聊不响应，私聊响应
    # 2->群聊响应，私聊不响应
    # 3->群聊和私聊都响应
    user_id = wcf.get_user_info()
    user_id = user_id['wxid']
    
    database_file = "{}_permission.db".format(user_id)
    # 检查数据库是否存在，不存在以user_id为名创建，存在则打开数据库
    if not os.path.exists(database_file):
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE permission
                (wxid text, code text, remark text, name text, country text, province text,city text, gender text, permission int, permission_end_time timestamp)''')
        conn.commit()
        # 将微信通讯录导入数据库，默认permission为2，permission_end_time为2099-12-31 23:59:59
        default_permission = config.PERMISSION
        default_permission_end_time = '2099-12-31 23:59:59'
        wcf.get_contacts()
        contact_list = wcf.contacts
        for contact in contact_list:
            cursor.execute("INSERT INTO permission VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(
                contact['wxid'], contact['code'], contact['remark'], contact['name'], contact['country'], contact['province'], contact['city'], contact['gender'],default_permission, default_permission_end_time))
        conn.commit()
        # 关闭数据库
        conn.close()
    else:
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        # 将更新后的微信通讯录存入数据库
        wcf.get_contacts()
        contact_list = wcf.contacts
        for contact in contact_list:
            cursor.execute("UPDATE permission SET code = ?, remark = ?, name = ?, country = ?,province = ?, city = ?, gender = ? WHERE wxid = ?", (contact['code'], contact['remark'], contact['name'], contact['country'], contact['province'], contact['city'], contact['gender'], contact['wxid']))
        conn.commit()
        # 关闭数据库
        conn.close()

def update_permission(DATABASE_URI):
    app = Flask(__name__)

    @app.route('/')
    def index():
        conn = sqlite3.connect(DATABASE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM permission")
        rows = cursor.fetchall()
        conn.close()
        return render_template('index.html', users=rows)

    @app.route('/update', methods=['POST', 'GET'])
    def update():
        if request.method == 'POST':
            wxid = request.form['wxid_field']
            permission = int(request.form['permission_field'])
            permission_end_time = request.form['permission_end_time_field']
            permission_end_time = permission_end_time.replace('T', ' ') + ":00"
            conn = sqlite3.connect(DATABASE_URI)
            cursor = conn.cursor()
            cursor.execute("UPDATE permission SET permission = ?, permission_end_time = ? WHERE wxid = ?", (permission, permission_end_time, wxid))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return render_template('update.html')

    app.run(debug=False)
        
if __name__ == "__main__":
    config = Config()
    wcf = Wcf(debug=True)
    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    init_permission(wcf, config)
    user_id = wcf.get_user_info()
    user_id = user_id['wxid']   
    database_file = "{}_permission.db".format(user_id)

    # add a threading to run update_permission
    t = threading.Thread(target=update_permission, args=(database_file,))
    t.start()