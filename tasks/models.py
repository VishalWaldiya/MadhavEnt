from django.db import models
from django.conf import settings

class TaskTemplate(models.Model):
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=10, default="TASK")
    next_number = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TaskStage(models.Model):
    STAGE_TYPES = [
        ('START', 'Start'),
        ('MIDDLE', 'Ongoing'),
        ('END', 'End'),
    ]
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    stage_type = models.CharField(max_length=10, choices=STAGE_TYPES, default='MIDDLE')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"

class ShopTask(models.Model):
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE)
    task_number = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    current_stage = models.ForeignKey(TaskStage, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_assigned')
    external_assignee = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.task_number}] {self.title}"

class TaskPhoto(models.Model):
    task = models.ForeignKey(ShopTask, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='task_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.task.task_number}"

class TaskHistory(models.Model):
    ACTION_TYPES = [
        ('CREATED', 'Task Created'),
        ('STAGE_MOVE', 'Stage Changed'),
        ('EDITED', 'Task Details Updated'),
        ('PHOTO_ADDED', 'Photo Added'),
    ]
    task = models.ForeignKey(ShopTask, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='STAGE_MOVE')
    from_stage = models.ForeignKey(TaskStage, on_delete=models.SET_NULL, null=True, related_name='history_from')
    to_stage = models.ForeignKey(TaskStage, on_delete=models.SET_NULL, null=True, related_name='history_to')
    details = models.TextField(blank=True, null=True)
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-moved_at']

    def __str__(self):
        return f"{self.task.task_number}: {self.from_stage} -> {self.to_stage}"
