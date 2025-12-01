from datetime import datetime

from flask import (
    Blueprint,
    Response,
    jsonify,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import current_app
from flask_login import current_user, login_required
from sqlalchemy import or_, text

from .models import Task, User, Message, TaskCompletionRequest, db
import csv
import io


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    return redirect(url_for("main.tasks"))


@main_bp.route("/tasks")
@login_required
def tasks():
    status = request.args.get("status", "").strip()
    assignee_id = request.args.get("assignee", "").strip()
    q = request.args.get("q", "").strip()

    if current_user.is_owner():
        query = Task.query
    else:
        query = Task.query.filter(Task.assignee_id == current_user.id)

    if status in {"todo", "in_progress", "done"}:
        query = query.filter(Task.status == status)

    if assignee_id.isdigit() and current_user.is_owner():
        query = query.filter(Task.assignee_id == int(assignee_id))

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))

    query = query.order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.priority.desc())

    tasks_list = query.all()
    users = User.query.order_by(User.username.asc()).all()

    # For UI: pending completion requests per task (dict)
    pending_map = {}
    if current_user.is_owner():
        pendings = TaskCompletionRequest.query.filter_by(status="pending").all()
    else:
        pendings = TaskCompletionRequest.query.filter_by(
            status="pending", requested_by_id=current_user.id
        ).all()
    # Only show pending badge if the task is not already done
    for r in pendings:
        try:
            t = Task.query.get(r.task_id)
            if t and t.status != "done":
                pending_map[r.task_id] = True
        except Exception:
            continue

    # Owner id for workers to open chat with owner from task cards
    owner_id = None
    if not current_user.is_owner():
        try:
            owner = _get_owner()
            owner_id = owner.id if owner else None
        except Exception:
            owner_id = None

    return render_template(
        "tasks.html",
        tasks=tasks_list,
        users=users,
        is_owner=current_user.is_owner(),
        pending_map=pending_map,
        owner_id=owner_id,
    )


@main_bp.route("/users")
@login_required
def users():
    if not current_user.is_owner():
        flash("Only the owner can view users")
        return redirect(url_for("main.tasks"))
    users_list = User.query.order_by(User.username.asc()).all()
    return render_template("users.html", users=users_list)


@main_bp.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():
    if not current_user.is_owner():
        flash("Only the owner can create tasks")
        return redirect(url_for("main.tasks"))
    users = User.query.order_by(User.username.asc()).all()
    error = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "todo")
        priority = request.form.get("priority", "medium")
        due_date_raw = request.form.get("due_date", "").strip()
        assignee_id = request.form.get("assignee_id", "").strip()

        if not title:
            error = "Title is required"

        # Determine assignee (owner must choose a valid one)
        try:
            assignee = (
                User.query.get(int(assignee_id)) if assignee_id.isdigit() else None
            )
        except Exception:
            assignee = None
        if assignee is None:
            error = error or "Valid assignee is required"

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
            except ValueError:
                error = error or "Invalid due date format"

        if error is None and assignee is not None:
            task = Task(
                title=title,
                description=description,
                status=status if status in {"todo", "in_progress", "done"} else "todo",
                priority=priority if priority in {"low", "medium", "high"} else "medium",
                due_date=due_date,
                assignee_id=assignee.id,
                created_by_id=current_user.id,
            )
            db.session.add(task)
            db.session.commit()
            flash("Task created")
            return redirect(url_for("main.tasks"))

    return render_template(
        "task_form.html",
        users=users,
        is_owner=current_user.is_owner(),
        task=None,
    )


def _can_edit(task: Task) -> bool:
    # Only owner can modify tasks
    return current_user.is_owner()


@main_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if not _can_edit(task):
        flash("Only the owner can edit tasks")
        return redirect(url_for("main.tasks"))

    users = User.query.order_by(User.username.asc()).all()
    error = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", task.status)
        priority = request.form.get("priority", task.priority)
        due_date_raw = request.form.get("due_date", "").strip()
        assignee_id = request.form.get("assignee_id", "").strip()

        if not title:
            error = "Title is required"

        if current_user.is_owner():
            if assignee_id.isdigit():
                assignee = User.query.get(int(assignee_id))
                if assignee is None:
                    error = error or "Invalid assignee"
            else:
                error = error or "Assignee is required"
        else:
            assignee = current_user

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
            except ValueError:
                error = error or "Invalid due date format"

        if error is None:
            task.title = title
            task.description = description
            task.status = status if status in {"todo", "in_progress", "done"} else task.status
            task.priority = (
                priority if priority in {"low", "medium", "high"} else task.priority
            )
            task.due_date = due_date
            task.assignee_id = assignee.id
            db.session.commit()
            flash("Task updated")
            return redirect(url_for("main.tasks"))

    return render_template(
        "task_form.html",
        users=users,
        is_owner=current_user.is_owner(),
        task=task,
    )


@main_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"]) 
@login_required
def toggle_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if not _can_edit(task):
        flash("Only the owner can modify tasks")
        return redirect(url_for("main.tasks"))
    new_status = "done" if task.status != "done" else "todo"
    task.status = new_status

    # If reopening to TODO, reject any pending completion requests and notify requester
    if new_status == "todo":
        pendings = TaskCompletionRequest.query.filter_by(
            task_id=task.id, status="pending"
        ).all()
        for req in pendings:
            req.status = "rejected"
            req.decision_by_id = current_user.id
            req.decision_at = datetime.utcnow()
            req.decision_note = "Reopened by owner"
            try:
                if req.requested_by_id and req.requested_by_id != current_user.id:
                    db.session.add(
                        Message(
                            sender_id=current_user.id,
                            receiver_id=req.requested_by_id,
                            body=f"Task #{task.id} '{task.title}' was reopened by owner.",
                        )
                    )
            except Exception:
                pass

    else:
        # Mark any pending requests as approved when owner marks done directly
        pendings = TaskCompletionRequest.query.filter_by(
            task_id=task.id, status="pending"
        ).all()
        had_pending = bool(pendings)
        for req in pendings:
            req.status = "approved"
            req.decision_by_id = current_user.id
            req.decision_at = datetime.utcnow()
            try:
                if req.requested_by_id and req.requested_by_id != current_user.id:
                    db.session.add(
                        Message(
                            sender_id=current_user.id,
                            receiver_id=req.requested_by_id,
                            body=f"Your request to mark task #{task.id} '{task.title}' was approved.",
                        )
                    )
            except Exception:
                pass
        # If no pending request existed, still notify the assignee that the owner marked it done
        if not had_pending and task.assignee_id and task.assignee_id != current_user.id:
            try:
                db.session.add(
                    Message(
                        sender_id=current_user.id,
                        receiver_id=task.assignee_id,
                        body=f"Task #{task.id} '{task.title}' was marked done by owner.",
                    )
                )
            except Exception:
                pass

    db.session.commit()
    return redirect(url_for("main.tasks"))


@main_bp.route("/tasks/<int:task_id>/progress", methods=["POST"])
@login_required
def progress_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    # Owner or assigned worker can update between todo <-> in_progress
    if not (current_user.is_owner() or task.assignee_id == current_user.id):
        flash("You do not have permission to update this task")
        return redirect(url_for("main.tasks"))

    # Workers cannot change tasks that are already done
    if task.status == "done" and not current_user.is_owner():
        flash("Only the owner can modify completed tasks")
        return redirect(url_for("main.tasks"))

    state = (request.form.get("state") or "").strip()
    if state not in ("todo", "in_progress"):
        state = "in_progress" if task.status == "todo" else "todo"
    task.status = state
    db.session.commit()
    return redirect(url_for("main.tasks"))


@main_bp.route("/tasks/<int:task_id>/delete", methods=["POST"]) 
@login_required
def delete_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_owner():
        flash("Only the owner can delete tasks")
        return redirect(url_for("main.tasks"))
    # Clean up related completion requests to avoid FK issues
    try:
        TaskCompletionRequest.query.filter_by(task_id=task.id).delete()
    except Exception:
        pass
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted")
    return redirect(url_for("main.tasks"))


@main_bp.route("/tasks/export")
@login_required
def export_csv():
    # Owner exports all; workers export own tasks
    if current_user.is_owner():
        query = Task.query
    else:
        query = Task.query.filter(Task.assignee_id == current_user.id)

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "id",
        "title",
        "description",
        "status",
        "priority",
        "due_date",
        "assignee",
        "created_at",
        "updated_at",
    ])
    for t in query.order_by(Task.id.asc()).all():
        writer.writerow([
            t.id,
            t.title or "",
            (t.description or "").replace("\r", " ").replace("\n", " "),
            t.status or "",
            t.priority or "",
            t.due_date.isoformat() if t.due_date else "",
            t.assignee.username if t.assignee else "",
            t.created_at.isoformat(timespec="seconds"),
            t.updated_at.isoformat(timespec="seconds"),
        ])

    # Choose inline vs attachment based on query param
    inline = request.args.get("open") == "1"
    data = output.getvalue()
    if not inline:
        # Prepend UTF-8 BOM for better Excel compatibility on Windows when downloading
        data = "\ufeff" + data

    disposition = ("inline" if inline else "attachment") + "; filename=tasks.csv"
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": disposition},
    )


@main_bp.route("/tasks/import", methods=["GET", "POST"])
@login_required
def import_csv():
    if not current_user.is_owner():
        flash("Only the owner can import tasks")
        return redirect(url_for("main.tasks"))
    results = None
    errors = []
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a CSV file to upload.")
            return render_template("import.html", results=None)

        # Read content as text with robust decoding and delimiter sniffing
        try:
            try:
                file.stream.seek(0)
            except Exception:
                pass

            raw = file.read()
            if isinstance(raw, str):
                text = raw
            else:
                try:
                    text = raw.decode("utf-8-sig")
                except Exception:
                    try:
                        text = raw.decode("utf-8", errors="replace")
                    except Exception:
                        text = raw.decode("latin1", errors="replace")

            # Normalize line endings
            text = text.replace("\r\n", "\n").replace("\r", "\n")

            sample = text[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ","

            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            if not reader.fieldnames:
                raise ValueError("No header row detected")
        except Exception:
            flash("Could not read the CSV file. Ensure it is a valid text CSV.")
            return render_template("import.html", results=None)

        created = 0
        skipped = 0

        for i, row in enumerate(reader, start=2):  # start at 2 to account for header row
            # Normalize header keys to lowercase and trim values
            norm = { (k or "").strip().lower(): (v or "").strip() for k, v in row.items() }

            # Skip completely empty rows
            if not any(norm.values()):
                continue

            title = norm.get("title", "")
            description = norm.get("description", "")
            status = norm.get("status", "todo")
            priority = norm.get("priority", "medium")
            due_date_str = norm.get("due_date", "")
            assignee_name = norm.get("assignee", "")

            if not title:
                skipped += 1
                errors.append(f"Row {i}: missing title")
                continue

            if status not in {"todo", "in_progress", "done"}:
                status = "todo"

            if priority not in {"low", "medium", "high"}:
                priority = "medium"

            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    errors.append(
                        f"Row {i}: invalid due_date '{due_date_str}' (use YYYY-MM-DD)"
                    )

            # Determine assignee respecting roles
            if current_user.is_owner():
                assignee = None
                if assignee_name:
                    assignee = User.query.filter_by(username=assignee_name).first()
                    if not assignee and assignee_name.lower() in {"owner"}:
                        assignee = User.query.filter_by(role="owner").first()
                    if not assignee:
                        skipped += 1
                        errors.append(f"Row {i}: unknown assignee '{assignee_name}'")
                        continue
                else:
                    assignee = current_user
            else:
                assignee = current_user  # workers can only import for themselves

            task = Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                assignee_id=assignee.id,
                created_by_id=current_user.id,
            )
            db.session.add(task)
            created += 1

        db.session.commit()
        results = {"created": created, "skipped": skipped, "errors": errors[:20]}

    return render_template("import.html", results=results)


@main_bp.route("/health")
def health():
    ok = True
    db_ok = False
    db_error = None
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        ok = False
        db_ok = False
        db_error = type(e).__name__

    uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    scheme = uri.split(":", 1)[0] if uri else ""

    return jsonify(
        status="ok" if ok and db_ok else "error",
        db=db_ok,
        db_scheme=scheme,
        instance_path=current_app.instance_path,
        db_error=db_error,
    )


@main_bp.route("/notifications/poll")
@login_required
def notifications_poll():
    # Unread messages for current user
    try:
        msg_count = (
            Message.query.filter_by(receiver_id=current_user.id, read_at=None).count()
        )
    except Exception:
        msg_count = 0

    # Approvals count
    try:
        if current_user.is_owner():
            appr_count = TaskCompletionRequest.query.filter_by(status="pending").count()
        else:
            appr_count = TaskCompletionRequest.query.filter_by(
                status="pending", requested_by_id=current_user.id
            ).count()
    except Exception:
        appr_count = 0

    # Pending tasks for attention (exclude ones already done)
    pending_ids = []
    try:
        if current_user.is_owner():
            pendings = TaskCompletionRequest.query.filter_by(status="pending").all()
        else:
            pendings = TaskCompletionRequest.query.filter_by(
                status="pending", requested_by_id=current_user.id
            ).all()
        for r in pendings:
            t = Task.query.get(r.task_id)
            if t and t.status != "done":
                pending_ids.append(t.id)
    except Exception:
        pass

    # Also highlight task cards if there are unread chat messages
    try:
        # Collect senders that have unread messages for the current user
        unread_msgs = Message.query.filter_by(receiver_id=current_user.id, read_at=None).all()
        unread_senders = {m.sender_id for m in unread_msgs}
        msg_task_ids = []
        if unread_senders:
            if current_user.is_owner():
                # Owner: highlight tasks assigned to workers who have unread messages
                try:
                    rows = (
                        Task.query
                        .with_entities(Task.id)
                        .filter(Task.assignee_id.in_(list(unread_senders)))
                        .filter(Task.status != "done")
                        .all()
                    )
                    msg_task_ids = [r[0] if isinstance(r, tuple) else r.id for r in rows]
                except Exception:
                    msg_task_ids = []
            else:
                # Worker: highlight own active tasks if there are unread messages from owner
                owner = _get_owner()
                if owner and (owner.id in unread_senders):
                    try:
                        rows = (
                            Task.query
                            .with_entities(Task.id)
                            .filter(Task.assignee_id == current_user.id)
                            .filter(Task.status != "done")
                            .all()
                        )
                        msg_task_ids = [r[0] if isinstance(r, tuple) else r.id for r in rows]
                    except Exception:
                        msg_task_ids = []
        # Merge with existing pending ids (unique)
        pending_ids = list({*pending_ids, *msg_task_ids})
    except Exception:
        pass

    return jsonify(messages=msg_count, approvals=appr_count, pending_task_ids=pending_ids)


# Messaging (Owner <-> Worker)

def _get_owner() -> User | None:
    return User.query.filter_by(role="owner").first()


@main_bp.route("/messages")
@login_required
def messages_root():
    if current_user.is_owner():
        # Prefer the most recent unread conversation, if any
        try:
            recent_unread = (
                Message.query.filter_by(receiver_id=current_user.id, read_at=None)
                .order_by(Message.created_at.desc())
                .first()
            )
            if recent_unread:
                u = User.query.get(recent_unread.sender_id)
                if u and u.role == "worker":
                    return redirect(url_for("main.messages_with", user_id=u.id))
        except Exception:
            pass

        user = User.query.filter(User.role == "worker").order_by(User.username.asc()).first()
        if not user:
            flash("No workers yet. Create one to start messaging.")
            return redirect(url_for("main.tasks"))
        return redirect(url_for("main.messages_with", user_id=user.id))
    else:
        owner = _get_owner()
        if not owner:
            flash("Owner account not found")
            return redirect(url_for("main.tasks"))
        return redirect(url_for("main.messages_with", user_id=owner.id))


@main_bp.route("/messages/<int:user_id>", methods=["GET", "POST"])
@login_required
def messages_with(user_id: int):
    other = User.query.get_or_404(user_id)

    # Permissions: workers may only talk with owner; owner may message any worker
    if current_user.is_owner():
        if other.role != "worker":
            flash("Owners can only open conversations with workers")
            return redirect(url_for("main.messages_root"))
    else:
        owner = _get_owner()
        if other.id != (owner.id if owner else -1):
            flash("Workers can only message the owner")
            return redirect(url_for("main.messages_root"))

    if request.method == "POST":
        body = (request.form.get("body") or "").strip()
        if not body:
            flash("Message cannot be empty")
        else:
            msg = Message(sender_id=current_user.id, receiver_id=other.id, body=body)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for("main.messages_with", user_id=other.id))

    # Load thread
    thread = (
        Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id))
            | ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    # Mark incoming as read and optionally notify sender (read receipt)
    unread_incoming = [m for m in thread if m.receiver_id == current_user.id and m.read_at is None]
    if unread_incoming:
        now = datetime.utcnow()
        for m in unread_incoming:
            m.read_at = now
        # If a worker just read owner's messages, inform the owner
        try:
            if current_user.role == "worker" and other.role == "owner":
                last_ts = max((m.created_at for m in unread_incoming), default=now)
                body = f"I have read your message(s). Latest at {last_ts.strftime('%Y-%m-%d %H:%M')}."
                db.session.add(Message(sender_id=current_user.id, receiver_id=other.id, body=body))
        except Exception:
            pass
        db.session.commit()
    else:
        db.session.commit()

    # Owner list of workers for quick switching
    workers = []
    if current_user.is_owner():
        workers = User.query.filter(User.role == "worker").order_by(User.username.asc()).all()

    pending_reqs = []
    if current_user.is_owner():
        pending_reqs = (
            TaskCompletionRequest.query.filter_by(status="pending", requested_by_id=other.id)
            .order_by(TaskCompletionRequest.created_at.asc())
            .all()
        )

    return render_template("messages.html", other=other, thread=thread, workers=workers, pending_reqs=pending_reqs)


@main_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if not current_user.is_owner():
        flash("Only the owner can delete users")
        return redirect(url_for("main.messages_root"))
    if user.role != "worker":
        flash("You cannot delete the owner account")
        return redirect(url_for("main.messages_root"))

    owner = _get_owner()
    if not owner or owner.id == user.id:
        flash("Owner account not found or invalid target")
        return redirect(url_for("main.messages_root"))

    # Remove messages by/with the user
    try:
        Message.query.filter(
            (Message.sender_id == user.id) | (Message.receiver_id == user.id)
        ).delete(synchronize_session=False)
    except Exception:
        pass

    # Remove pending requests created by the user; null out decisions by the user (if any)
    try:
        TaskCompletionRequest.query.filter_by(requested_by_id=user.id).delete(synchronize_session=False)
    except Exception:
        pass
    try:
        TaskCompletionRequest.query.filter_by(decision_by_id=user.id).update({"decision_by_id": None})
    except Exception:
        pass

    # Reassign tasks to owner where needed
    try:
        for t in Task.query.filter_by(assignee_id=user.id).all():
            t.assignee_id = owner.id
        for t in Task.query.filter_by(created_by_id=user.id).all():
            t.created_by_id = owner.id
    except Exception:
        pass

    db.session.delete(user)
    db.session.commit()
    flash("Worker deleted; tasks reassigned to owner and messages removed")
    return redirect(url_for("main.tasks"))


@main_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id: int):
    msg = Message.query.get_or_404(message_id)
    if not current_user.is_owner():
        flash("Only the owner can delete messages")
        return redirect(url_for("main.messages_root"))
    other_id = msg.sender_id if msg.sender_id != current_user.id else msg.receiver_id
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted")
    return redirect(url_for("main.messages_with", user_id=other_id))


@main_bp.route("/messages/<int:user_id>/delete-thread", methods=["POST"])
@login_required
def delete_thread(user_id: int):
    if not current_user.is_owner():
        flash("Only the owner can delete messages")
        return redirect(url_for("main.messages_root"))
    other = User.query.get_or_404(user_id)
    if other.role != "worker":
        flash("Owners can only manage threads with workers")
        return redirect(url_for("main.messages_root"))
    try:
        Message.query.filter(
            (
                (Message.sender_id == current_user.id) & (Message.receiver_id == other.id)
            )
            | (
                (Message.sender_id == other.id) & (Message.receiver_id == current_user.id)
            )
        ).delete(synchronize_session=False)
        db.session.commit()
        flash("Conversation deleted")
    except Exception:
        db.session.rollback()
        flash("Failed to delete conversation")
    return redirect(url_for("main.messages_with", user_id=other.id))


# Worker: request completion (requires owner approval)
@main_bp.route("/tasks/<int:task_id>/request-complete", methods=["POST"])
@login_required
def request_complete(task_id: int):
    task = Task.query.get_or_404(task_id)
    if current_user.is_owner():
        flash("Owners do not need approval; use Complete instead")
        return redirect(url_for("main.tasks"))
    if task.assignee_id != current_user.id:
        flash("You can only request completion for your own tasks")
        return redirect(url_for("main.tasks"))
    if task.status == "done":
        flash("Task already done")
        return redirect(url_for("main.tasks"))
    if task.status not in ("todo", "in_progress"):
        flash("Invalid task state for completion request")
        return redirect(url_for("main.tasks"))

    # Prevent duplicate pending requests
    exists = TaskCompletionRequest.query.filter_by(
        task_id=task.id, status="pending"
    ).first()
    if exists:
        flash("Request already submitted and pending approval")
        return redirect(url_for("main.tasks"))

    note = (request.form.get("note") or "").strip()
    req = TaskCompletionRequest(
        task_id=task.id, requested_by_id=current_user.id, note=note
    )
    db.session.add(req)

    # Send default message to owner notifying the request
    owner = User.query.filter_by(role="owner").first()
    if owner:
        msg_body = (
            f"Request to mark task #{task.id} '{task.title}' as done."
            + (f" Note: {note}" if note else "")
        )
        db.session.add(
            Message(sender_id=current_user.id, receiver_id=owner.id, body=msg_body)
        )
    db.session.commit()
    flash("Completion request sent to owner")
    return redirect(url_for("main.tasks"))


# Owner: list approvals
@main_bp.route("/approvals")
@login_required
def approvals():
    if not current_user.is_owner():
        flash("Only owner can view approvals")
        return redirect(url_for("main.tasks"))
    pending = (
        TaskCompletionRequest.query.filter_by(status="pending")
        .order_by(TaskCompletionRequest.created_at.asc())
        .all()
    )
    return render_template("approvals.html", requests=pending)


# Owner decision endpoints
@main_bp.route("/approvals/<int:req_id>/approve", methods=["POST"])
@login_required
def approvals_approve(req_id: int):
    if not current_user.is_owner():
        flash("Only owner can approve")
        return redirect(url_for("main.tasks"))
    req = TaskCompletionRequest.query.get_or_404(req_id)
    if req.status != "pending":
        return redirect(url_for("main.approvals"))
    req.status = "approved"
    req.decision_by_id = current_user.id
    req.decision_note = (request.form.get("decision_note") or "").strip()
    req.decision_at = datetime.utcnow()

    # Apply status change
    task = Task.query.get(req.task_id)
    if task:
        task.status = "done"
        # Notify requester
        try:
            if req.requested_by_id and req.requested_by_id != current_user.id:
                note_txt = f" Note: {req.decision_note}" if req.decision_note else ""
                db.session.add(
                    Message(
                        sender_id=current_user.id,
                        receiver_id=req.requested_by_id,
                        body=f"Your request to mark task #{task.id} '{task.title}' as done was approved.{note_txt}",
                    )
                )
        except Exception:
            pass
    db.session.commit()
    flash("Request approved; task marked done")
    return redirect(url_for("main.approvals"))


@main_bp.route("/approvals/<int:req_id>/reject", methods=["POST"])
@login_required
def approvals_reject(req_id: int):
    if not current_user.is_owner():
        flash("Only owner can reject")
        return redirect(url_for("main.tasks"))
    req = TaskCompletionRequest.query.get_or_404(req_id)
    if req.status != "pending":
        return redirect(url_for("main.approvals"))
    req.status = "rejected"
    req.decision_by_id = current_user.id
    req.decision_note = (request.form.get("decision_note") or "").strip()
    req.decision_at = datetime.utcnow()
    # Notify requester
    try:
        task = Task.query.get(req.task_id)
        if req.requested_by_id and req.requested_by_id != current_user.id:
            note_txt = f" Note: {req.decision_note}" if req.decision_note else ""
            db.session.add(
                Message(
                    sender_id=current_user.id,
                    receiver_id=req.requested_by_id,
                    body=f"Your request to mark task #{task.id if task else req.task_id} was rejected.{note_txt}",
                )
            )
    except Exception:
        pass
    db.session.commit()
    flash("Request rejected")
    return redirect(url_for("main.approvals"))
