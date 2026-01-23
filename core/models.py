# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ["-created_at"]


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, default="daily"
    )
    target_count = models.IntegerField(default=1)  # How many times per frequency period
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Streak(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="streaks")
    habit = models.ForeignKey(
        Habit, on_delete=models.CASCADE, related_name="streaks", null=True, blank=True
    )
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.habit:
            return (
                f"{self.user.username} - {self.habit.name} - {self.current_streak} days"
            )
        return f"{self.user.username} - General - {self.current_streak} days"

    class Meta:
        unique_together = ["user", "habit"]


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("task_completed", "Task Completed"),
        ("task_skipped", "Task Skipped"),
        ("habit_completed", "Habit Completed"),
        ("achievement_earned", "Achievement Earned"),
        ("credits_earned", "Credits Earned"),
        ("streak_updated", "Streak Updated"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="activity_logs"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    habit = models.ForeignKey(Habit, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    credits_earned = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp.date()}"

    class Meta:
        ordering = ["-timestamp"]


class SkippedTask(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="skipped_tasks"
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="skips")
    reason = models.TextField(blank=True)
    skipped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.title} - {self.skipped_at.date()}"


class Achievement(models.Model):
    CATEGORY_CHOICES = [
        ("tasks", "Tasks"),
        ("streaks", "Streaks"),
        ("habits", "Habits"),
        ("general", "General"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=50, blank=True)  # emoji or icon name
    credits_reward = models.IntegerField(default=0)
    requirement = models.JSONField()  # Store requirements like {"tasks_completed": 10}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

    class Meta:
        unique_together = ["user", "achievement"]


class UserCredits(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credits")
    total_credits = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.total_credits} credits"


class DailyHeatmap(models.Model):
    """Stores daily statistics for heatmap visualization"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_stats")
    date = models.DateField()
    tasks_completed_count = models.IntegerField(default=0)
    habits_completed_count = models.IntegerField(default=0)
    streak_count = models.IntegerField(default=0)
    achievements_earned_count = models.IntegerField(default=0)
    credits_earned = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    tasks_data = models.JSONField(default=list)  # Store task IDs or details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]


class UserProfile(models.Model):
    """Extended user profile"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    timezone = models.CharField(max_length=50, default="UTC")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"



class SocialAccount(models.Model):
    PROVIDER_CHOICES = [
        ("github", "GitHub"),
        ("google", "Google"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_accounts"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255)
    access_token = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["provider", "provider_user_id"]

    def __str__(self):
        return f"{self.user.username} - {self.provider}"
