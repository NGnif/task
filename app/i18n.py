from flask import Blueprint, redirect, request, session, url_for


LANGUAGES = ["en", "ar"]


# Minimal translations without external libs
_t = {
    "en": {
        "app_name": "Task Manager",
        "login": "Login",
        "logout": "Logout",
        "register": "Register",
        "create_user": "Create User",
        "create_owner": "Create the owner account",
        "username": "Username",
        "password": "Password",
        "change_password": "Change Password",
        "current_password": "Current Password",
        "new_password": "New Password",
        "confirm_password": "Confirm Password",
        "update_password": "Update Password",
        "owner": "Owner",
        "worker": "Worker",
        "admin": "Admin",
        "role": "Role",
        "tasks": "Tasks",
        "dashboard": "Dashboard",
        "my_tasks": "My Tasks",
        "new_task": "New Task",
        "import_csv": "Import CSV",
        "download_csv": "Download CSV",
        "view_csv": "View CSV",
        "search": "Search",
        "status": "Status",
        "priority": "Priority",
        "assignee": "Assignee",
        "due": "Due",
        "due_date": "Due Date",
        "actions": "Actions",
        "title": "Title",
        "description": "Description",
        "edit": "Edit",
        "complete": "Complete",
        "reopen": "Reopen",
        "delete": "Delete",
        "messages": "Messages",
        "send": "Send",
        "type_message": "Type your message",
        "no_messages": "No messages yet.",
        "request_done": "Request Done",
        "pending_approval": "Pending approval",
        "approvals": "Approvals",
        "approve": "Approve",
        "reject": "Reject",
        "note": "Note",
        "decision_note": "Decision note",
        "start": "Start",
        "back_to_todo": "Back to To Do",
        "save": "Save",
        "cancel": "Cancel",
        "no_tasks": "No tasks found.",
        "import_title": "Import Tasks from CSV",
        "import_btn": "Import",
        "choose_file": "Choose File",
        "offline_title": "Offline",
        "offline_msg": "You appear to be offline. Some pages may still be available from cache.",
        # statuses
        "status.todo": "To Do",
        "status.in_progress": "In Progress",
        "status.done": "Done",
        # priorities
        "priority.low": "Low",
        "priority.medium": "Medium",
        "priority.high": "High",
        "users": "Users",
        "no_users": "No users found.",
        "delete_conversation": "Delete Conversation",
        "delete_worker": "Delete Worker",
    },
    "ar": {
        "app_name": "مدير المهام",
        "login": "تسجيل الدخول",
        "logout": "تسجيل الخروج",
        "register": "تسجيل مستخدم",
        "create_user": "إنشاء مستخدم",
        "create_owner": "إنشاء حساب المالك",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "change_password": "تغيير كلمة المرور",
        "current_password": "كلمة المرور الحالية",
        "new_password": "كلمة المرور الجديدة",
        "confirm_password": "تأكيد كلمة المرور",
        "update_password": "تحديث كلمة المرور",
        "owner": "المالك",
        "worker": "موظف",
        "admin": "مشرف",
        "role": "الدور",
        "tasks": "المهام",
        "dashboard": "لوحة التحكم",
        "my_tasks": "مهامي",
        "new_task": "مهمة جديدة",
        "import_csv": "استيراد CSV",
        "download_csv": "تنزيل CSV",
        "view_csv": "عرض CSV",
        "search": "بحث",
        "status": "الحالة",
        "priority": "الأولوية",
        "assignee": "المكلف",
        "due": "الاستحقاق",
        "due_date": "تاريخ الاستحقاق",
        "actions": "إجراءات",
        "title": "العنوان",
        "description": "الوصف",
        "edit": "تعديل",
        "complete": "إنهاء",
        "reopen": "إعادة فتح",
        "delete": "حذف",
        "messages": "الرسائل",
        "send": "إرسال",
        "type_message": "اكتب رسالتك",
        "no_messages": "لا توجد رسائل.",
        "request_done": "طلب إنهاء",
        "pending_approval": "بانتظار الموافقة",
        "approvals": "الموافقات",
        "approve": "موافقة",
        "reject": "رفض",
        "note": "ملاحظة",
        "decision_note": "ملاحظة القرار",
        "start": "بدء",
        "back_to_todo": "عودة إلى غير منجز",
        "save": "حفظ",
        "cancel": "إلغاء",
        "no_tasks": "لا توجد مهام.",
        "import_title": "استيراد المهام من CSV",
        "import_btn": "استيراد",
        "choose_file": "اختر ملف",
        "offline_title": "بدون اتصال",
        "offline_msg": "يبدو أنك غير متصل. قد تتوفر بعض الصفحات من الذاكرة المؤقتة.",
        # statuses
        "status.todo": "غير منجز",
        "status.in_progress": "قيد التنفيذ",
        "status.done": "منجز",
        # priorities
        "priority.low": "منخفض",
        "priority.medium": "متوسط",
        "priority.high": "مرتفع",
        "users": "المستخدمون",
        "no_users": "لا يوجد مستخدمون.",
        "delete_conversation": "حذف المحادثة",
        "delete_worker": "حذف الموظف",
    },
}


def get_locale() -> str:
    loc = session.get("locale", "en")
    return loc if loc in LANGUAGES else "en"


def t(key: str) -> str:
    loc = get_locale()
    return _t.get(loc, {}).get(key, _t["en"].get(key, key))


def status_label(value: str) -> str:
    return t(f"status.{value}")


def priority_label(value: str) -> str:
    return t(f"priority.{value}")


def is_rtl() -> bool:
    return get_locale() == "ar"


i18n_bp = Blueprint("i18n", __name__)


@i18n_bp.route("/lang/<locale>")
def set_lang(locale: str):
    if locale not in LANGUAGES:
        locale = "en"
    session["locale"] = locale
    # go back
    ref = request.headers.get("Referer")
    return redirect(ref or url_for("main.index"))


def init_i18n(app):
    @app.context_processor
    def inject_i18n():  # type: ignore
        return {
            "t": t,
            "status_label": status_label,
            "priority_label": priority_label,
            "locale": get_locale(),
            "dir_rtl": is_rtl(),
        }
