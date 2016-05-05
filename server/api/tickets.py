from flask import Blueprint, request, session
from flask import current_app as app
from decorators import api_wrapper, login_required, WebException
from models import db, Tickets, TicketReplies

import datetime
import user
import utils
blueprint = Blueprint("tickets", __name__)

@blueprint.route("/create", methods=["POST"])
@login_required
@api_wrapper
def create_ticket():
	params = utils.flat_multi(request.form)

	title = params.get("title")
	body = params.get("body")
	username = session.get("username")

	result = user.get_user(username=username)
	if result is None:
		raise WebException("User does not exist.")

	_user = result.first()

	ticket = Tickets(title, body, _user.uid)
	with app.app_context():
		db.session.add(ticket)
		db.session.commit()

	return { "success": 1, "message": "Ticket created." }

@blueprint.route("/close", methods=["POST"])
@login_required
@api_wrapper
def close_ticket():
	params = utils.flat_multi(request.form)

	htid = params.get("htid")

	result = get_ticket(htid=htid)
	if result is None: raise WebException("Ticket does not exist.")
	ticket = result.first()
	ticket.opened = False
	with app.app_context():
		db.session.add(ticket)
		db.session.commit()

	return { "success": 1, "message": "Ticket closed." }

@blueprint.route("/open", methods=["POST"])
@login_required
@api_wrapper
def open_ticket():
	params = utils.flat_multi(request.form)

	htid = params.get("htid")

	result = get_ticket(htid=htid)
	if result is None:
		raise WebException("Ticket does not exist.")

	ticket = result.first()
	ticket.opened = True
	with app.app_context():
		db.session.add(ticket)
		db.session.commit()

	return { "success": 1, "message": "Ticket opened." }

@blueprint.route("/reply", methods=["POST"])
@login_required
@api_wrapper
def reply_to_ticket():
	params = utils.flat_multi(request.form)

	htid = params.get("htid")
	body = params.get("body")

	_user = user.get_user().first()
	if _user is None:
		raise WebException("User does not exist.")

	reply = TicketReplies(htid, body, _user.uid)
	with app.app_context():
		db.session.add(reply)
		db.session.commit()

	return { "success": 1, "message": "" }

@blueprint.route("/data", methods=["GET"])
@login_required
@api_wrapper
def ticket_data():
	opened = []
	closed = []

	params = utils.flat_multi(request.args)
	htid = params.get("htid")

	if htid is not None:
		result = get_ticket(htid=htid).first()
	elif user.is_admin():
		result = get_ticket().all()
	else:
		_user = user.get_user().first()

		if _user is None:
			raise WebException("User does not exist.")

		result = get_ticket(author=_user.uid).all()

	if result is not None:
		if htid is not None:
			tickets = [result]
		else:
			tickets = result

		for ticket in tickets:
			tmp = user.get_user(uid=ticket.author).first()

			if tmp is not None:
				username = tmp.username
				uid = tmp.uid
			else:
				username = ""
				uid = ""

			d = {
				"htid": ticket.htid,
				"date": datetime.datetime.fromtimestamp(ticket.date).isoformat() + "Z",
				"opened": ticket.opened,
				"username": username,
				"uid": uid,
				"title": ticket.title,
				"body": ticket.body,
				"replies": ticket.get_replies()
			}

			if htid is None:
				if d["opened"] == True:
					opened.append(d)
				else:
					closed.append(d)
			else:
				data = d
	else:
		data = {}

	if htid is None:
		data = [opened, closed]

	return { "success": 1, "data": data }

def get_ticket(htid=None, author=None, opened=None):
	match = {}
	if htid is not None:
		match.update({ "htid": htid })
	if author is not None:
		match.update({ "author": author })
	if opened is not None:
		match.update({ "opened": opened })
	with app.app_context():
		result = Tickets.query.filter_by(**match)
		return result
