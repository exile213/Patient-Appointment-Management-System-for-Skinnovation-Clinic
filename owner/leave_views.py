"""
Leave management views removed.

This module is kept as a stub that returns 404 for any leave-management routes.
The leave-request feature has been deprecated; owners should manage attendant availability manually.
"""
from django.http import Http404


def _raise_not_found(*args, **kwargs):
    raise Http404("Leave request management has been removed")


list_leave_requests = _raise_not_found
approve_leave_request = _raise_not_found
reject_leave_request = _raise_not_found
leave_request_detail = _raise_not_found
