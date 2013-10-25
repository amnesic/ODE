from cornice.resource import resource, view
from sqlalchemy.orm.exc import NoResultFound
from webob import Response, exc
import json

from ode.models import DBSession, Event
from ode.validation import EventSchema, EventCollectionSchema


class HTTPNotFound(exc.HTTPError):

    def __init__(self, msg='Not Found'):
        body = {'status': 404, 'message': msg}
        Response.__init__(self, json.dumps(body))
        self.status = 404
        self.content_type = 'application/json'


@resource(collection_path='/events', path='/events/{id}')
class EventResource(object):

    def __init__(self, request):
        self.request = request

    @view(schema=EventCollectionSchema)
    def collection_post(self):
        """Add new events"""
        events_data = self.request.validated['events']
        result_data = []
        for event_data in events_data:
            event = Event(**event_data)
            DBSession.add(event)
            DBSession.flush()
            result_data.append({'id': event.id, 'status': 'created'})
        return {'events': result_data}

    @view(schema=EventSchema)
    def put(self):
        """Update existing event by id"""
        event_id = self.request.matchdict['id']
        query = DBSession.query(Event).filter_by(id=event_id)
        if not query.update(self.request.validated):
            raise HTTPNotFound()
        return {'status': 'updated'}

    @view(accept='text/calendar', renderer='ical')
    @view(accept='application/json', renderer='json')
    def collection_get(self):
        """Get list of all events"""
        query = DBSession.query(Event).all()
        events = [event.to_dict() for event in query]
        return {'events': events}

    @view(accept='text/calendar', renderer='ical')
    @view(accept='application/json', renderer='json')
    def get(self):
        """Get a specific event by id"""
        id = self.request.matchdict['id']
        try:
            event = DBSession.query(Event).filter_by(id=id).one()
        except NoResultFound:
            raise HTTPNotFound()
        return {
            'status': 'success',
            'event': event.to_dict(),
        }

    def delete(self):
        """Delete a specific event by id"""
        id = self.request.matchdict['id']
        try:
            event = DBSession.query(Event).filter_by(id=id).one()
        except NoResultFound:
            raise HTTPNotFound()
        DBSession.delete(event)
        return {'status': 'deleted'}
