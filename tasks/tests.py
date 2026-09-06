from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tasks.models import TaskTemplate, TaskStage, ShopTask, TaskComment, TaskHistory

User = get_user_model()

class TaskCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='task_worker',
            password='password123',
            role='ADMIN'
        )
        self.other_user = User.objects.create_user(
            username='other_worker',
            password='password123',
            role='SALES'
        )
        self.client = Client()
        self.client.login(username='task_worker', password='password123')

        self.template = TaskTemplate.objects.create(name='Inspection', prefix='INSP')
        self.stage = TaskStage.objects.create(template=self.template, name='Initial Check')
        self.task = ShopTask.objects.create(
            template=self.template,
            task_number='INSP-1',
            title='Battery Wiring Check',
            description='Check wiring harness',
            current_stage=self.stage,
            assigned_to=self.user
        )

    def test_add_comment_to_task(self):
        url = reverse('add_task_comment', args=[self.task.id])
        response = self.client.post(url, {'content': 'Inspected harness, looks good.'})
        self.assertEqual(response.status_code, 302)

        # Verify comment created
        self.assertEqual(TaskComment.objects.filter(task=self.task).count(), 1)
        comment = TaskComment.objects.first()
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'Inspected harness, looks good.')

        # Verify history entry created
        history = TaskHistory.objects.filter(task=self.task, action_type='COMMENT_ADDED').first()
        self.assertIsNotNone(history)
        self.assertIn('Inspected harness', history.details)

    def test_comment_renders_on_task_detail(self):
        TaskComment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment for rendering.'
        )
        url = reverse('task_detail', args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test comment for rendering.')
        self.assertContains(response, 'task_worker')

    def test_cannot_comment_on_soft_deleted_task(self):
        self.task.delete()
        self.assertTrue(self.task.is_deleted)

        url = reverse('add_task_comment', args=[self.task.id])
        response = self.client.post(url, {'content': 'Should fail comment.'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TaskComment.objects.filter(task=self.task).count(), 0)

    def test_author_can_edit_own_comment(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user, content='Original comment')
        url = reverse('edit_task_comment', args=[comment.id])
        response = self.client.post(url, {'content': 'Updated comment text'})
        self.assertEqual(response.status_code, 302)

        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment text')

    def test_other_user_cannot_edit_comment(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user, content='Original comment')
        self.client.login(username='other_worker', password='password123')

        url = reverse('edit_task_comment', args=[comment.id])
        response = self.client.post(url, {'content': 'Malicious edit attempt'})
        self.assertEqual(response.status_code, 302)

        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Original comment')

    def test_author_can_delete_own_comment(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user, content='Comment to delete')
        url = reverse('delete_task_comment', args=[comment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(TaskComment.objects.filter(id=comment.id).exists())

    def test_other_user_cannot_delete_comment(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user, content='Protected comment')
        self.client.login(username='other_worker', password='password123')

        url = reverse('delete_task_comment', args=[comment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(TaskComment.objects.filter(id=comment.id).exists())
