from peewee import *
import datetime
import os

# --- 关键修改开始 ---
# 检查是否在 Flet 移动端环境
app_data_dir = os.environ.get("FLET_APP_STORAGE_DATA")

if app_data_dir:
    # 如果是手机，存到专属数据文件夹
    db_path = os.path.join(app_data_dir, "todo.db")
else:
    # 如果是电脑本地运行，还存当前目录
    db_path = "todo.db"

print(f"数据库路径: {db_path}")
# --- 关键修改结束 ---

db = SqliteDatabase(db_path)

class Todo(Model):
    title = CharField()
    content = TextField(default="")
    image_path = CharField(null=True)
    deadline = DateField(null=True)
    is_completed = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

def init_db():
    db.connect()
    db.create_tables([Todo])
    if Todo.select().count() == 0:
        Todo.create(title="欢迎使用待办", content="这是测试数据", deadline=datetime.date.today())

if __name__ == '__main__':
    init_db()
    print("数据库初始化成功！")
