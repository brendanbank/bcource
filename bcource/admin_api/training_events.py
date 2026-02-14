from flask_restx import Resource, abort
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import training_event_model, training_event_input
from bcource.admin_api.api import api
from bcource.admin_api.trainings import ns
from bcource.models import Training, TrainingEvent, Location, Practice
from bcource import db


@ns.route('/<int:training_id>/events')
@ns.param('training_id', 'Training ID')
class TrainingEventList(Resource):
    @ns.doc('list_training_events')
    @ns.marshal_list_with(training_event_model)
    @admin_required
    def get(self, training_id):
        """List events for a training."""
        Training.query.get_or_404(training_id)
        return TrainingEvent.query.filter_by(training_id=training_id)\
            .order_by(TrainingEvent.start_time).all()

    @ns.doc('create_training_event')
    @ns.expect(training_event_input)
    @ns.marshal_with(training_event_model, code=201)
    @admin_required
    def post(self, training_id):
        """Add an event to a training."""
        Training.query.get_or_404(training_id)
        data = api.payload
        practice = Practice.default_row()

        loc = Location.query.get(data['location_id'])
        if not loc or loc.practice_id != practice.id:
            abort(400, 'Invalid location_id')

        event = TrainingEvent(
            start_time=data['start_time'],
            end_time=data['end_time'],
            location_id=data['location_id'],
            training_id=training_id,
        )
        db.session.add(event)
        db.session.commit()
        return event, 201


@ns.route('/<int:training_id>/events/<int:event_id>')
@ns.param('training_id', 'Training ID')
@ns.param('event_id', 'Event ID')
class TrainingEventDetail(Resource):
    @ns.doc('update_training_event')
    @ns.expect(training_event_input)
    @ns.marshal_with(training_event_model)
    @admin_required
    def put(self, training_id, event_id):
        """Update a training event."""
        Training.query.get_or_404(training_id)
        event = TrainingEvent.query.get_or_404(event_id)

        if event.training_id != training_id:
            abort(404, 'Event does not belong to this training')

        data = api.payload
        practice = Practice.default_row()

        if 'location_id' in data:
            loc = Location.query.get(data['location_id'])
            if not loc or loc.practice_id != practice.id:
                abort(400, 'Invalid location_id')
            event.location_id = data['location_id']

        if 'start_time' in data:
            event.start_time = data['start_time']
        if 'end_time' in data:
            event.end_time = data['end_time']

        db.session.commit()
        return event

    @ns.doc('delete_training_event')
    @admin_required
    def delete(self, training_id, event_id):
        """Delete a training event."""
        Training.query.get_or_404(training_id)
        event = TrainingEvent.query.get_or_404(event_id)

        if event.training_id != training_id:
            abort(404, 'Event does not belong to this training')

        db.session.delete(event)
        db.session.commit()
        return '', 204
