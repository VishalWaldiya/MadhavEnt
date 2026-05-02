from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TaskTemplate, TaskStage, ShopTask, TaskPhoto
from django.http import JsonResponse
from django.db.models import Max

@login_required
def template_list(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    templates = TaskTemplate.objects.all()
    return render(request, 'tasks/template_list.html', {'templates': templates})

@login_required
def add_template(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        stages_raw = request.POST.getlist('stages') # List of stage names
        
        template = TaskTemplate.objects.create(name=name, description=description)
        for i, stage_name in enumerate(stages_raw):
            if stage_name.strip():
                TaskStage.objects.create(template=template, name=stage_name.strip(), order=i)
        
        messages.success(request, 'Template created successfully.')
        return redirect('template_list')
        
    return render(request, 'tasks/template_form.html')

@login_required
def board_view(request):
    template_id = request.GET.get('template')
    templates = TaskTemplate.objects.all()
    
    active_template = None
    stages = []
    tasks_by_stage = {}
    
    if template_id:
        active_template = get_object_or_404(TaskTemplate, id=template_id)
        stages = active_template.stages.all()
        for stage in stages:
            tasks_by_stage[stage.id] = ShopTask.objects.filter(current_stage=stage).select_related('assigned_to')
    elif templates.exists():
        active_template = templates.first()
        return redirect(f"/tasks/board/?template={active_template.id}")

    return render(request, 'tasks/board.html', {
        'templates': templates,
        'active_template': active_template,
        'stages': stages,
        'tasks_by_stage': tasks_by_stage
    })

@login_required
def add_task(request):
    if request.method == 'POST':
        template_id = request.POST.get('template')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        template = get_object_or_404(TaskTemplate, id=template_id)
        first_stage = template.stages.first()
        
        if not first_stage:
            messages.error(request, 'This template has no stages defined.')
            return redirect('board_view')
            
        task = ShopTask.objects.create(
            template=template,
            title=title,
            description=description,
            current_stage=first_stage,
            assigned_to=request.user
        )
        
        # Handle Photos
        photos = request.FILES.getlist('photos')
        for p in photos:
            TaskPhoto.objects.create(task=task, photo=p)
            
        messages.success(request, 'Task created successfully.')
        return redirect(f"/tasks/board/?template={template.id}")
        
    templates = TaskTemplate.objects.all()
    return render(request, 'tasks/task_form.html', {'templates': templates})

@login_required
def update_task_stage(request, task_id):
    task = get_object_or_404(ShopTask, id=task_id)
    new_stage_id = request.POST.get('stage_id')
    
    if new_stage_id:
        new_stage = get_object_or_404(TaskStage, id=new_stage_id)
        if new_stage.template == task.template:
            task.current_stage = new_stage
            task.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            messages.success(request, f'Task moved to {new_stage.name}')
    
    return redirect(f"/tasks/board/?template={task.template.id}")
