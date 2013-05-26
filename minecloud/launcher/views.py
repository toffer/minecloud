import datetime
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.timezone import utc
from django.views.decorators.http import require_POST

from . import tasks
from .models import Instance, Session
from .sseview import SseView, send_event


@login_required
def index(request):
    instance = None
    current_sessions = None
    err_msg = None
    running_instances = Instance.objects.exclude(state__exact='terminated')
    if len(running_instances) == 1: 
        instance = running_instances[0]
        current_sessions = (Session.objects
            .filter(instance_id__exact=instance.id)
            .filter(logout__isnull=True)
        )
    elif len(running_instances) > 1:
        err_msg = "Error: Multiple instances are running at once."
    return render(request, 
                  'launcher/index.html',
                  {'instance': instance,
                   'sessions': current_sessions,
                   'err_msg': err_msg})
    
@login_required
@require_POST
def launch(request):
    # Don't launch new instance, unless all previous
    # instances have been terminated.
    running_instances = Instance.objects.exclude(state__exact='terminated')
    if not running_instances:
        timestamp = datetime.datetime.utcnow().replace(tzinfo=utc)
        instance = Instance(launched_by=request.user,
                            start=timestamp,
                            state='initiating')
        instance.save()
        send_event('reload')
        tasks.launch.delay(instance.id)
    return redirect('mcl_index')

@login_required
@require_POST
def terminate(request):
    instance = Instance.objects.get(pk=request.POST['instance_id'])
    if instance:
        instance.state = 'shutting down'
        instance.save()
        send_event('reload')
        tasks.terminate.delay(instance.id)
    return redirect('mcl_index')


class SSE(SseView):
    pass
