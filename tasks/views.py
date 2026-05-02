from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TaskTemplate, TaskStage, ShopTask, TaskPhoto, TaskHistory
from django.http import JsonResponse
from django.db import transaction

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
        prefix = request.POST.get('prefix', 'TASK').upper()
        description = request.POST.get('description')
        stages_names = request.POST.getlist('stages')
        stages_types = request.POST.getlist('stage_types') # Expected to match indices
        
        template = TaskTemplate.objects.create(name=name, prefix=prefix, description=description)
        
        # Filter out empty names and their corresponding types
        valid_stages = [(n, t) for n, t in zip(stages_names, stages_types) if n.strip()]
        
        for i, (stage_name, s_type) in enumerate(valid_stages):
            # Default to END for the last stage if no END stage is defined
            final_type = s_type
            if i == len(valid_stages) - 1 and 'END' not in [x[1] for x in valid_stages]:
                final_type = 'END'
            elif i == 0 and 'START' not in [x[1] for x in valid_stages]:
                 final_type = 'START'

            TaskStage.objects.create(
                template=template, 
                name=stage_name.strip(), 
                order=i,
                stage_type=final_type
            )
        
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
        external_assignee = request.POST.get('external_assignee')
        
        with transaction.atomic():
            template = get_object_or_404(TaskTemplate, id=template_id)
            first_stage = template.stages.first()
            
            if not first_stage:
                messages.error(request, 'This template has no stages defined.')
                return redirect('board_view')
            
            task_number = f"{template.prefix}-{template.next_number}"
            template.next_number += 1
            template.save()
            
            task = ShopTask.objects.create(
                template=template,
                task_number=task_number,
                title=title,
                description=description,
                current_stage=first_stage,
                assigned_to=request.user,
                external_assignee=external_assignee
            )
            
            # Initial history record
            TaskHistory.objects.create(
                task=task,
                action_type='CREATED',
                to_stage=first_stage,
                moved_by=request.user,
                details=f"Task created with title: {task.title}"
            )
            
            # Handle Photos
            photos = request.FILES.getlist('photos')
            for p in photos:
                TaskPhoto.objects.create(task=task, photo=p)
            if photos:
                TaskHistory.objects.create(
                    task=task,
                    action_type='PHOTO_ADDED',
                    moved_by=request.user,
                    details=f"Uploaded {len(photos)} initial photos."
                )
            
        messages.success(request, f'Task {task_number} created successfully.')
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
            old_stage = task.current_stage
            if old_stage != new_stage:
                task.current_stage = new_stage
                task.save()
                
                # Record History
                TaskHistory.objects.create(
                    task=task,
                    action_type='STAGE_MOVE',
                    from_stage=old_stage,
                    to_stage=new_stage,
                    moved_by=request.user,
                    details=f"Moved from {old_stage.name} to {new_stage.name}"
                )
                
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            messages.success(request, f'Task moved to {new_stage.name}')
    
    return redirect(f"/tasks/board/?template={task.template.id}")

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(ShopTask, id=task_id)
    return render(request, 'tasks/task_detail.html', {'task': task})

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(ShopTask, id=task_id)
    if request.method == 'POST':
        old_title = task.title
        old_desc = task.description
        old_assignee = task.external_assignee
        
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.external_assignee = request.POST.get('external_assignee')
        task.save()
        
        # Log changes
        changes = []
        if old_title != task.title: changes.append(f"Title changed from '{old_title}' to '{task.title}'")
        if old_desc != task.description: changes.append("Description was updated")
        if old_assignee != task.external_assignee: changes.append(f"Assignee changed from '{old_assignee}' to '{task.external_assignee}'")
        
        if changes:
            TaskHistory.objects.create(
                task=task,
                action_type='EDITED',
                moved_by=request.user,
                details="; ".join(changes)
            )
            
        messages.success(request, 'Task updated successfully.')
        return redirect('task_detail', task_id=task.id)
    
    templates = TaskTemplate.objects.all()
    return render(request, 'tasks/task_form.html', {'task': task, 'templates': templates})

@login_required
def add_task_photo(request, task_id):
    if request.method == 'POST' and request.FILES.getlist('photos'):
        task = get_object_or_404(ShopTask, id=task_id)
        photos = request.FILES.getlist('photos')
        for p in photos:
            TaskPhoto.objects.create(task=task, photo=p)
        
        TaskHistory.objects.create(
            task=task,
            action_type='PHOTO_ADDED',
            moved_by=request.user,
            details=f"Added {len(photos)} new photos to the task."
        )
        messages.success(request, f'Added {len(photos)} photos.')
    return redirect('task_detail', task_id=task_id)
