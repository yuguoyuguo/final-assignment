import os
import json
import logging
from datetime import datetime#时间相关
from functools import wraps #编写装饰器保留原函数信息
from flask import Flask, request, jsonify, session
from flask_session import Session #保存用户的会话信息
import bleach #过滤HTML标签
from werkzeug.security import generate_password_hash, check_password_hash #密码加密
from cryptography.fernet import Fernet #加密工具
from datetime import timedelta #时间间隔
#Flask初始化并配置
app = Flask(__name__)

app.secret_key = "users_session" #密钥
#修改默认配置
app.config["SESSION_TYPE"] = "filesystem" #本地存储
app.config["SESSION_PERMANENT"] = True #持久存储?
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30) #会话过期时间30分钟
app.config["SESSION_FILE_DIR"] = "./sessions" #会话文件存储目录

Session(app) #应用配置/恢复默认

#加密工具的密钥
secret_key = b"GtxU3MYb1gV-_MwZyBUYSl3HZDnCw84gQxOCetCA7Uc="
user_fernet_tool = Fernet(secret_key)


# 获取所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#检查对应文件夹是否存在                           ↓被检查的文件夹名
if not os.path.exists(os.path.join(BASE_DIR, "logs")):  
    os.mkdir(os.path.join(BASE_DIR, "logs"))
if not os.path.exists(os.path.join(BASE_DIR, "sessions")):  
    os.mkdir(os.path.join(BASE_DIR, "sessions"))
if not os.path.exists(os.path.join(BASE_DIR, "data")):  
    os.mkdir(os.path.join(BASE_DIR, "data"))  

"""
日志配置与写入
"""
#创建操作记录器/审计日志（              日志记录器名字）
audit_log = logging.getLogger("user_operation")
audit_log.setLevel(logging.INFO) #设置级别

#创建处理器                                     写入路径
operation_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", "audit.log"),encoding="utf-8")
#设置处理器输出格式                                    时间戳         日志级别        日志消息:自定义信息传入 
operation_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s\n"))
#处理器添加到记录器
audit_log.addHandler(operation_handler)

#同上
error_log = logging.getLogger("user_error")
error_log.setLevel(logging.ERROR)

error_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", "error.log"),encoding="utf-8")
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname) - %(message)s\n (pathname)s:%(lineno)d"))      
error_log.addHandler(error_handler)                                                      # ↑路径         ↑行号                               
# 记录审计日志
def write_audit_log(event, detail=""):
    ip = get_client_ip()
    audit_log.info(f"{ip} | {event} | {detail}")#输出处理器输出格式内容 info中为%(message)s输出内容
def get_client_ip():                                                       
    #先判断是否有代理IP                            有代理IP可能为：真实IP,代理IP
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0]
    return request.remote_addr or "未知"
            #直接输出IP


'''
全局异常处理
'''
#拦截Python异常 try-except
@app.errorhandler(Exception)
def catch_all_error(e):                    #是否记录详细堆栈信息
    error_log.error(f"未捕获异常：{str(e)}", exc_info=True)
    return jsonify({"text":"服务器出错 稍后再试", "code":500}), 500 #内部500：告诉前端出错 外部500：告诉浏览器出错

@app.errorhandler(404)
def page_not_exist(e):
    return jsonify({"text":"接口不存在", "code":404}), 404

@app.errorhandler(403)
def have_no_right(e):
    return jsonify({"text":"无权访问", "code":403}), 403

'''
安全工具
'''
#清理输入内容
def clean_input(content):
    if content is None:
        return ""       #tags：允许的标签。strip：移除无法解析的标签
    clean = bleach.clean(content, tags=[], strip=True)
    clean.strip()   #←去首位和末尾空格
    return clean

#加密文本：输入的手机号：123 为明文   明文转字节：123→ b'123' 字节加密：b'123'→ b'随机字母字符数字组合'
def encrypt_text(text):
    if not text:
        return ""                               
    try:                                  #加密          #转字节
        encrypted_bytes = user_fernet_tool.encrypt(text.encode())
        encrypted_text = encrypted_bytes.decode()
        return encrypted_text
    except Exception as e:
        print(f"加密文本失败：{str(e)}")
        error_log.error(f"加密文本失败：{str(e)}")#记录错误级别日志
        return ""  

#解密文本       上面流程倒着看
def decrypt_text(encrypted_text):
    if not encrypted_text:
        return ""
    try:
        decrypted_bytes = user_fernet_tool.decrypt(encrypted_text.encode())
        decrypted_text = decrypted_bytes.decode()
        return decrypted_text
    except Exception as e:
        print(f"解密文本失败：{str(e)}")
        error_log.error(f"解密文本失败：{str(e)}")
        return ""  




'''
数据存储与计数器
'''
user_data = {}
task_list = []

uid_count = 1
tid_count = 1

#持久化  保存web填的数据 和后台对应对标的数据
def save_data():
    try:
        with open(os.path.join(BASE_DIR, "data", "user.json"), "w", encoding="utf-8") as f:
                #转储  存储的数据 文件对象 转义ASCII？         缩进   非标准类型转字符串
            json.dump(user_data, f, ensure_ascii=False, indent=2, default=str)
        
        with open(os.path.join(BASE_DIR, "data", "task.json"), "w", encoding="utf-8") as f:
            json.dump(task_list, f, ensure_ascii=False, indent=2, default=str)

        counters = {"uid_count": uid_count, "tid_count": tid_count}
        with open(os.path.join(BASE_DIR, "data", "counters.json"), "w", encoding="utf-8") as f:
            json.dump(counters, f, ensure_ascii=False, indent=2)
        print("已保存")
    except Exception as e:
        print(f"保存失败：{str(e)}")
        error_log.error(f"保存失败：{str(e)}")

#加载数据
def load_data():

    global user_data, task_list, uid_count, tid_count

    try:                                     #   ↓要找的文件夹    ↓是否存在该文件
        if os.path.exists(os.path.join(BASE_DIR, "data", "user.json")):
            with open(os.path.join(BASE_DIR, "data", "user.json"), "r", encoding="utf-8") as f:
                user_data = json.load(f)#读取文件解析为python对象
        if os.path.exists(os.path.join(BASE_DIR, "data", "task.json")):#同里
            with open(os.path.join(BASE_DIR, "data", "task.json"), "r", encoding="utf-8") as f:
                task_list = json.load(f) 
        if os.path.exists(os.path.join(BASE_DIR, "data", "counters.json")):
            with open(os.path.join(BASE_DIR, "data", "counters.json"), "r", encoding="utf-8") as f:
                counters = json.load(f) #↓获取对应ID  没有则默认值1
                uid_count = counters.get("uid_count", 1)
                tid_count = counters.get("tid_count", 1)
    except Exception as e:
        print(f"加载数据失败：{str(e)}")
        error_log.error(f"加载数据失败：{str(e)}")
                        
def init_accounts():# 添加内置账号
    global uid_count

    if "admin" in user_data:
        return

    admin_id = uid_count
    user_data["admin"] = { #账号1
        "id": admin_id,
        "username": "admin",               # 加密内容             哈希算法         盐值字节
        "password": generate_password_hash("Admin@123", method="pbkdf2:sha256", salt_length=16),
        "role": "SYSTEM",
        "phone": encrypt_text("13800000000"),
        "create_time": datetime.now()
    }
    uid_count += 1

    user_data["test"] = { #账号2
        "id": uid_count,
        "username": "test",
        "password": generate_password_hash("123456", method="pbkdf2:sha256", salt_length=16),
        "role": "user",
        "phone": encrypt_text("13900000000"),
        "create_time": datetime.now()
    }
    uid_count += 1
    print('已初始化账号')

    load_data()         
    init_accounts()
    save_data()

'''
装饰器：
查看面板时候条件要求
'''
def need_login(func):
    @wraps(func)   #复制所在def函数的元数据 or  
    def check(*args, **kwargs):# *：可以传任意数量的参数 **：可以传任意带变量名参数
                              #check(1,2,3) == args=(1,2,3);check(a=1,b=2) == kwargs={'a':1,'b':2}
        if "user_id" not in session: 
            return jsonify({"text":"先登录", "code":401}), 401
        return func(*args, **kwargs)   # 调用原始函数并返回结果
    return check

def need_admin(func):
    @wraps(func)
    @need_login
    def check(*args, **kwargs):
        current_uid = session["user_id"]
        #用户数据中找当前用户
        now_user = None
        for u in user_data.values():
            if u["id"] == current_uid:
                now_user = u
                break
        # 在循环外检查权限
        if not now_user or now_user["role"] != "SYSTEM":
            return jsonify({"text":"没有权限或用户不存在", "code":403}), 403
        return func(*args, **kwargs)
    return check

'''
前端接口
'''
#用户                   
@app.route("/login", methods=["POST"])
def login():
    username = clean_input(request.form.get("username",""))# 默认值：“”
    password = request.form.get("password","") #密码后端对比不会渲染前端

    user = user_data.get(username)
    if not user or not check_password_hash(user["password"], password):
        # 记录登录操作↓
        write_audit_log("LOGIN_FAILED", f"用户名：{username}")
        return jsonify({"text":"用户名或密码错误", "code":400}), 400
    
    # 登录成功，创建会话
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session.permanent = True
    
    write_audit_log("LOGIN_SUCCESS", f"用户名：{username},角色：{user['role']}")
    return jsonify({"text":"登录成功", "code":200,
                    "data":{"username": user["username"], "role": user["role"]}
    })

@app.route("/register", methods=["POST"])
def register():
    global uid_count

    username = clean_input(request.form.get("username",''))
    password = request.form.get("password", '')
    phone = clean_input(request.form.get("phone", ''))

    if not username or not password:
        return jsonify({"text":"用户名或密码不能为空", "code":400}), 400
    if username in user_data:
        return jsonify({"text":"注册信息无效"})

    user_data[username] = {
        "id": uid_count,
        "username": username,
        "password": generate_password_hash(password, method="pbkdf2:sha256", salt_length=16),
        "role": "user",
        "phone": encrypt_text(phone),
        "create_time": datetime.now()
    }
    uid_count += 1
    save_data()
    write_audit_log("REGISTER_SUCCESS", f"用户名：{username}")
    return jsonify({"text":"注册成功", "code":200})

@app.route("/logout")
@need_login 
def logout():
    username = session.get("username", "未知用户")
    write_audit_log("LOGOUT_SUCCESS", f"用户名：{username}")
    session.clear()
    return jsonify({"text":"退出成功", "code":200})

#任务管理接口
@app.route("/task/list")
@need_login
def my_tasks():
    my_id = session["user_id"]
    my_task = []
    for t in task_list:
        if t["user_id"] == my_id:
            my_task.append({
                "id": t["id"],
                "title": str(t["title"]),
                "create_time": t["create_time"]
            })
    my_task.reverse() #反转列表
    return jsonify({"text":"ok", "code":200, "data":my_task})

@app.route("/task/add", methods=["POST"])
@need_login
def add_task():
    global tid_count

    title = clean_input(request.form.get("title", ''))
    if not title:
        return jsonify({"text":"任务标题不能为空", "code":400}), 400
    
    new_task = {
        "id": tid_count,
        "user_id": session["user_id"],
        "title": title,
        "create_time": datetime.now()
    }
    task_list.append(new_task)
    tid_count += 1
    save_data()
    write_audit_log("TASK_CREATE", f"任务ID用户：{new_task['id']}_{session.get('username')}")
    return jsonify({"text":"ok", "code":200, "data":{"tast_id":new_task["id"]}})

@app.route("/task/delete/<int:task_id>")
@need_login
def delete_task(task_id):
    my_id = session["user_id"]
    target = None  # 

    # 查找任务并验证所有权
    for t in task_list:  
        if t["id"] == task_id and t["user_id"] == my_id:
            target = t
            break  

    if not target:  
        return jsonify({"text": "任务不存在或者你没权限删除", "code": 404}), 404  

    task_list.remove(target)  
    save_data()
    write_audit_log("TASK_DELETE", "任务ID: " + str(task_id) + ", 用户: " + session.get("username"))
    
    return jsonify({"text":"ok", "code":200})

#管理员接口
@app.route("/admin/users")
@need_admin
def admin_user_list(): 
    res = []

    # 遍历所有用户，构建用户信息列表
    for u in user_data.values():  
        res.append({
            "id": u["id"],
            "username": u["username"],
            "role": u["role"],
            "create_time": str(u["create_time"])  # 
        })

    write_audit_log("ADMIN_VIEW_USERS", "管理员: " + session.get("username")) 
    return jsonify({"text": "ok", "code": 200, "data": res})  

@app.route("/admin/delete_user/<username>")  # 
@need_admin
def admin_delete_user(username):  
    username = clean_input(username)  

    if username not in user_data:  
        return jsonify({"text": "用户不存在", "code": 404}), 404  
    if user_data[username]["role"] == "SYSTEM":  
        return jsonify({"text": "不能删除管理员账号", "code": 403}), 403  

    # 删除用户
    del user_data[username]
    save_data()
    write_audit_log("ADMIN_DELETE_USER", "删除用户: " + username + ", 操作者: " + session.get("username")) 

    return jsonify({"text": "删除成功", "code": 200})

@app.route("/admin/tasks")  
@need_admin
def admin_all_tasks():
    res = []

    # 遍历所有任务
    for t in task_list:  
        # 查找创建任务的用户名
        creator = ""  
        for u in user_data.values():  
            if u["id"] == t["user_id"]:  
                creator = u["username"]  
                break  
        
        res.append({
            "id": t["id"],
            "title": t["title"],
            "creator": creator,  # 创建人显示用户名
            "create_time": str(t["create_time"])  
        })

    write_audit_log("ADMIN_VIEW_TASKS", "管理员: " + session.get("username"))  

    return jsonify({"text": "ok", "code": 200, "data": res})
@app.route("/test.html")
def test():
    try:
        # 获取test.html所在目录的绝对路径读取test.html文件
        html_path = os.path.join(os.path.dirname(__file__), "test.html")
        with open(html_path, "r", encoding="utf-8") as f:  # 
            return f.read()  
    except Exception as e:
        print("【错误】读取test.html失败：" + str(e))
        error_log.error("读取test.html失败：" + str(e))
        return "读取失败: " + str(e)

if __name__ == "__main__":
    # 确保数据已初始化
    load_data()
    init_accounts()
    save_data()
    app.run( host= "0.0.0.0",port=6961,debug=True)