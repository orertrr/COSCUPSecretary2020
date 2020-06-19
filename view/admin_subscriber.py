import csv
import io
from datetime import datetime

from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import render_template
from flask import request

from models.subscriberdb import SubscriberDB
from module.subscriber import Subscriber

VIEW_ADMIN_SUBSCRIBER = Blueprint('admin_subscriber', __name__, url_prefix='/admin/subscriber')


@VIEW_ADMIN_SUBSCRIBER.route('/')
def index():
    return render_template('./admin_subscriber.html')

@VIEW_ADMIN_SUBSCRIBER.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'GET':
        return render_template('./admin_subscriber_add.html')

    elif request.method == 'POST':
        data = io.StringIO(request.files['file'].read().decode('utf-8'))
        csv_data = list(csv.DictReader(data))

        for data in csv_data:
            Subscriber.process_upload(mail=data['mail'], name=data['name'])

        return u'add: %s' % len(csv_data)

@VIEW_ADMIN_SUBSCRIBER.route('/list', methods=('GET', 'POST'))
def lists():
    if request.method == 'GET':
        return render_template('./admin_subscriber_list.html')

    elif request.method == 'POST':
        post_data = request.get_json()

        if 'casename' not in post_data:
            return u'', 401

        if post_data['casename'] == 'get':
            datas = []
            for data in SubscriberDB().find():
                datas.append({
                    '_id': data['_id'],
                    'code': data['code'],
                    'name': data['name'],
                    'mails': data['mails'],
                    'created_at': data['created_at'],
                    'admin_code': '',
                })
            return jsonify({'datas': datas})

        elif post_data['casename'] == 'getcode':
            user = Subscriber(mail=post_data['_id'])
            return jsonify({'code': user.render_admin_code()})

@VIEW_ADMIN_SUBSCRIBER.route('/list/dl')
def dl():
    ''' name, mails[-1] '''
    with io.StringIO() as files:
        csv_writer = csv.writer(files, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(('name', 'mail', 'admin_link'))

        for data in SubscriberDB().find({}, {'_id': 1}):
            user = Subscriber(mail=data['_id'])
            csv_writer.writerow((user.data['name'], user.data['mails'][-1], user.render_admin_code()))

        filename = 'coscup_paper_subscribers_%s.csv' % datetime.now().strftime('%Y%m%d_%H%M%S')

        return Response(
                files.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': 'attachment; filename=%s' % filename,
                         'x-filename': filename,
                })
