from flask_restx import Namespace, Resource, abort
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import (
    training_summary_model, training_detail_model,
    training_input, training_update_input,
)
from bcource.admin_api.api import api
from bcource.models import Training, TrainingType, TrainingEvent, Trainer, Location, Practice
from bcource import db

ns = Namespace('trainings', description='Training management')
api.add_namespace(ns)

list_parser = ns.parser()
list_parser.add_argument('active', type=str, choices=('true', 'false'), help='Filter by active status', location='args')
list_parser.add_argument('q', type=str, help='Search by name', location='args')
list_parser.add_argument('trainingtype_id', type=int, help='Filter by training type', location='args')


@ns.route('/')
class TrainingList(Resource):
    @ns.doc('list_trainings')
    @ns.expect(list_parser)
    @ns.marshal_list_with(training_summary_model)
    @admin_required
    def get(self):
        """List trainings with optional filters."""
        args = list_parser.parse_args()
        practice = Practice.default_row()

        query = Training.query.filter_by(practice_id=practice.id)

        if args.get('active') == 'true':
            query = query.filter_by(active=True)
        elif args.get('active') == 'false':
            query = query.filter_by(active=False)

        if args.get('q'):
            query = query.filter(Training.name.ilike(f'%{args["q"]}%'))

        if args.get('trainingtype_id'):
            query = query.filter_by(trainingtype_id=args['trainingtype_id'])

        return query.order_by(Training.id.desc()).all()

    @ns.doc('create_training')
    @ns.expect(training_input)
    @ns.marshal_with(training_detail_model, code=201)
    @admin_required
    def post(self):
        """Create a new training with optional events and trainer assignments."""
        data = api.payload
        practice = Practice.default_row()

        # Validate training type
        tt = TrainingType.query.get(data['trainingtype_id'])
        if not tt or tt.practice_id != practice.id:
            abort(400, 'Invalid trainingtype_id')

        training = Training()
        training.name = data['name']
        training.trainingtype = tt
        training.practice = practice
        training.max_participants = data['max_participants']
        training.active = data.get('active', True)
        training.apply_policies = data.get('apply_policies', True)

        # Assign trainers
        for tid in data.get('trainer_ids', []):
            trainer = Trainer.query.get(tid)
            if trainer and trainer.practice_id == practice.id:
                training.trainers.append(trainer)

        db.session.add(training)
        db.session.flush()  # get training.id for events

        # Create events
        for ev in data.get('events', []):
            loc = Location.query.get(ev['location_id'])
            if not loc or loc.practice_id != practice.id:
                abort(400, f'Invalid location_id: {ev["location_id"]}')

            event = TrainingEvent(
                start_time=ev['start_time'],
                end_time=ev['end_time'],
                location_id=ev['location_id'],
                training_id=training.id,
            )
            db.session.add(event)

        db.session.commit()
        return training, 201


@ns.route('/<int:id>')
@ns.param('id', 'Training ID')
class TrainingDetail(Resource):
    @ns.doc('get_training')
    @ns.marshal_with(training_detail_model)
    @admin_required
    def get(self, id):
        """Get training detail with events and enrollment counts."""
        training = Training.query.get_or_404(id)
        return training

    @ns.doc('update_training')
    @ns.expect(training_update_input)
    @ns.marshal_with(training_detail_model)
    @admin_required
    def put(self, id):
        """Update a training."""
        training = Training.query.get_or_404(id)
        data = api.payload
        practice = Practice.default_row()

        if 'name' in data:
            training.name = data['name']

        if 'trainingtype_id' in data:
            tt = TrainingType.query.get(data['trainingtype_id'])
            if not tt or tt.practice_id != practice.id:
                abort(400, 'Invalid trainingtype_id')
            training.trainingtype = tt

        if 'max_participants' in data:
            training.max_participants = data['max_participants']

        if 'active' in data:
            training.active = data['active']

        if 'apply_policies' in data:
            training.apply_policies = data['apply_policies']

        if 'trainer_ids' in data:
            training.trainers.clear()
            for tid in data['trainer_ids']:
                trainer = Trainer.query.get(tid)
                if trainer and trainer.practice_id == practice.id:
                    training.trainers.append(trainer)

        db.session.commit()
        return training


@ns.route('/<int:id>/deactivate')
@ns.param('id', 'Training ID')
class TrainingDeactivate(Resource):
    @ns.doc('deactivate_training')
    @ns.marshal_with(training_detail_model)
    @admin_required
    def patch(self, id):
        """Deactivate a training."""
        training = Training.query.get_or_404(id)
        training.active = False
        db.session.commit()
        return training
