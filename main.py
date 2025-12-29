import flet as ft
from database import Todo
import datetime
import calendar
import traceback


def main(page: ft.Page):
    # --- 1. 页面基础设置 ---
    page.title = "我的待办"
    page.theme_mode = "light"
    page.padding = 0
    # 窗口设置
    page.window_width = 390
    page.window_height = 844
    page.window_resizable = True

    # 全局状态
    state = {
        "view_year": datetime.datetime.now().year,
        "view_month": datetime.datetime.now().month
    }

    # ==========================================
    #               逻辑功能区
    # ==========================================

    todo_list = ft.ListView(expand=True, spacing=10, padding=20)

    def render_todos():
        """渲染列表"""
        try:
            todo_list.controls.clear()

            # 获取并排序数据
            all_todos = list(Todo.select())
            all_todos.sort(key=lambda t: (
                t.is_completed,
                t.deadline is None,
                t.deadline if t.deadline else datetime.date.max,
                -t.id
            ))

            for task in all_todos:
                date_str = task.deadline.strftime("%m-%d") if task.deadline else "无期限"
                is_overdue = (task.deadline and task.deadline < datetime.date.today() and not task.is_completed)
                date_color = "red" if is_overdue else "grey"
                text_style = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if task.is_completed else None

                todo_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Checkbox(
                                    value=task.is_completed,
                                    on_change=lambda e, t=task: toggle_complete(e, t)
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(task.title, size=16, style=text_style,
                                                color="grey" if task.is_completed else "black"),
                                        ft.Text(f"截止: {date_str}", size=12, color=date_color),
                                    ],
                                    spacing=2, expand=True
                                ),
                                ft.Icon(name=ft.icons.IMAGE, color="blue",
                                        size=16) if task.image_path else ft.Container(),
                                ft.Icon(name=ft.icons.CHEVRON_RIGHT, color="grey")
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=10, bgcolor="white", border_radius=10,
                        ink=True,
                        on_click=lambda e, t_id=task.id: show_edit_page(t_id),
                        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.BLUE_GREY_100),
                    )
                )
            page.update()
        except Exception as e:
            print(f"列表渲染错误: {e}")

    def toggle_complete(e, task):
        task.is_completed = e.control.value
        task.save()
        render_todos()

    # ==========================================
    #            详情编辑页
    # ==========================================

    def show_edit_page(task_id):
        try:
            try:
                task = Todo.get(Todo.id == task_id)
            except Todo.DoesNotExist:
                return

            current_image_path = [task.image_path]
            current_date = [task.deadline]

            # 控件定义
            title_edit = ft.TextField(value=task.title, label="标题", text_size=20)
            content_edit = ft.TextField(
                value=task.content, label="详细笔记", multiline=True, min_lines=5, max_lines=15
            )
            date_btn_text = ft.Text(f"截止日期: {task.deadline}" if task.deadline else "设置期限")
            img_display = ft.Image(
                src=task.image_path if task.image_path else "",
                visible=True if task.image_path else False,
                width=300, height=200, fit=ft.ImageFit.COVER, border_radius=10
            )

            # 事件处理
            def on_date_change(e):
                if e.control.value:
                    current_date[0] = e.control.value.date()
                    date_btn_text.value = f"截止日期: {current_date[0]}"
                    date_btn_text.update()

            def on_file_picked(e: ft.FilePickerResultEvent):
                if e.files:
                    file_path = e.files[0].path
                    img_display.src = file_path
                    img_display.visible = True
                    img_display.update()
                    current_image_path[0] = file_path

            date_picker = ft.DatePicker(
                on_change=on_date_change,
                first_date=datetime.datetime(2023, 1, 1),
                last_date=datetime.datetime(2030, 12, 31),
            )
            file_picker = ft.FilePicker(on_result=on_file_picked)

            # ★ 修复：清理 overlay 防止堆积
            page.overlay.clear()
            page.overlay.extend([date_picker, file_picker])
            page.update()

            def save_changes(e):
                task.title = title_edit.value
                task.content = content_edit.value
                task.image_path = current_image_path[0]
                task.deadline = current_date[0]
                task.save()
                back_to_home()
                page.snack_bar = ft.SnackBar(ft.Text("保存成功！"))
                page.snack_bar.open = True
                page.update()

            def delete_task(e):
                task.delete_instance()
                back_to_home()

            # 编辑页布局
            edit_view = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: back_to_home()),
                                ft.Text("编辑详情", size=20, weight="bold"),
                                ft.Row([
                                    ft.IconButton(icon=ft.icons.DELETE, icon_color="red", on_click=delete_task),
                                    ft.IconButton(icon=ft.icons.SAVE, icon_color="blue", on_click=save_changes)
                                ])
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Divider(),
                        title_edit,
                        ft.Row(controls=[
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.CALENDAR_MONTH), date_btn_text]),
                                              on_click=lambda _: date_picker.pick_date()),
                            ft.ElevatedButton("图片", icon=ft.icons.IMAGE,
                                              on_click=lambda _: file_picker.pick_files(allow_multiple=False,
                                                                                        file_type=ft.FilePickerFileType.IMAGE)),
                        ]),
                        img_display,
                        content_edit,
                    ],
                    scroll=ft.ScrollMode.AUTO
                ),
                padding=20, bgcolor="white", expand=True
            )
            page.controls.clear()
            page.add(edit_view)
            page.update()

        except Exception as e:
            traceback.print_exc()

    def back_to_home():
        page.overlay.clear()
        page.controls.clear()
        page.add(todo_view, nav_bar)
        # ★ 关键：重新挂载一次 Dialog，防止它在页面切换中丢失
        page.dialog = add_dialog
        render_todos()
        page.update()

    # ==========================================
    #            日历逻辑
    # ==========================================
    calendar_grid = ft.Column(scroll=ft.ScrollMode.AUTO)

    def change_month(delta):
        state["view_month"] += delta
        if state["view_month"] > 12:
            state["view_month"] = 1
            state["view_year"] += 1
        elif state["view_month"] < 1:
            state["view_month"] = 12
            state["view_year"] -= 1
        render_calendar()

    def render_calendar():
        calendar_grid.controls.clear()
        year, month = state["view_year"], state["view_month"]
        now = datetime.datetime.now()

        todos = Todo.select().where(Todo.deadline != None)
        tasks_by_date = {}
        for t in todos:
            tasks_by_date.setdefault(str(t.deadline), []).append(t.title)

        # 头部
        header = ft.Row(
            controls=[
                ft.IconButton(icon=ft.icons.CHEVRON_LEFT, on_click=lambda e: change_month(-1)),
                ft.Text(f"{year}年 {month}月", size=20, weight="bold", color="blue"),
                ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, on_click=lambda e: change_month(1)),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        calendar_grid.controls.append(ft.Container(content=header, padding=10))

        # 星期
        week_head = ft.Row([ft.Text(d, weight="bold", width=45, text_align="center") for d in
                            ["一", "二", "三", "四", "五", "六", "日"]], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        calendar_grid.controls.append(week_head)
        calendar_grid.controls.append(ft.Divider())

        # 网格
        for week in calendar.monthcalendar(year, month):
            week_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                              vertical_alignment=ft.CrossAxisAlignment.START)
            for day in week:
                if day == 0:
                    week_row.controls.append(ft.Container(width=48))
                else:
                    date_key = f"{year}-{month:02d}-{day:02d}"
                    day_tasks = tasks_by_date.get(date_key, [])
                    is_today = (day == now.day and month == now.month and year == now.year)

                    task_widgets = [
                        ft.Container(content=ft.Text(t[:4], size=10, color="white", no_wrap=True), bgcolor="blue",
                                     border_radius=4, padding=2, margin=1, alignment=ft.alignment.center) for t in
                        day_tasks]

                    day_con = ft.Container(
                        content=ft.Column(
                            [ft.Text(str(day), color="red" if is_today else "black", weight="bold"), *task_widgets],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        width=48, padding=5, border_radius=5, border=ft.border.all(1, "red") if is_today else None
                    )
                    week_row.controls.append(day_con)
            calendar_grid.controls.append(week_row)
            calendar_grid.controls.append(ft.Container(height=5))
        page.update()

    # ==========================================
    #            【核心修复】新建任务逻辑
    # ==========================================

    # 1. 定义组件 (只定义一次)
    new_task_input = ft.TextField(hint_text="准备做点什么？", autofocus=True)

    def save_new_task(e):
        if not new_task_input.value.strip():
            return
        try:
            Todo.create(title=new_task_input.value, deadline=None)
            new_task_input.value = ""
            add_dialog.open = False  # 只负责关闭开关
            page.update()  # 刷新弹窗状态
            render_todos()  # 刷新列表
        except Exception as ex:
            print(f"创建失败: {ex}")

    def close_dialog(e):
        add_dialog.open = False
        page.update()

    # 2. 创建弹窗对象
    add_dialog = ft.AlertDialog(
        title=ft.Text("新建待办"),
        content=new_task_input,
        actions=[ft.TextButton("取消", on_click=close_dialog), ft.TextButton("保存", on_click=save_new_task)],
    )

    # 3. 这里的函数只负责把 开关 打开
    def open_add_dialog(e):
        new_task_input.value = ""  # 清空输入框
        add_dialog.open = True
        page.update()

    # ==========================================
    #               主界面组装
    # ==========================================

    todo_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("我的待办清单", size=24, weight="bold", color="black"),
                todo_list,
                ft.FloatingActionButton(icon=ft.icons.ADD, tooltip="新建", bgcolor="blue", on_click=open_add_dialog),
            ],
        ),
        padding=20, expand=True
    )

    calendar_view = ft.Container(
        content=calendar_grid, padding=5, expand=True, alignment=ft.alignment.top_center
    )

    def change_tab(e):
        index = e.control.selected_index
        page.controls.clear()
        if index == 0:
            page.add(todo_view)
            # ★ 关键：切回主页时，确保弹窗还在
            page.dialog = add_dialog
            render_todos()
        elif index == 1:
            page.add(calendar_view)
            render_calendar()
        page.add(nav_bar)
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.LIST, label="待办"),
            ft.NavigationDestination(icon=ft.icons.CALENDAR_MONTH, label="日历"),
        ],
        on_change=change_tab,
        selected_index=0
    )

    # ★★★ 核心修复：程序启动时，就把弹窗挂上去，永远不卸载 ★★★
    page.dialog = add_dialog

    page.add(todo_view, nav_bar)
    render_todos()


if __name__ == "__main__":
    ft.app(target=main)
