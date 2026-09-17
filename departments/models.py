from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255) # e.g. BCA, MCA
    
    class Meta:
        unique_together = ('department', 'name')
        
    def __str__(self):
        return f"{self.department.name} - {self.name}"

class Semester(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=100) # e.g., "Semester 1", "Semester 2"
    
    class Meta:
        unique_together = ('course', 'number')
        ordering = ['number']
        
    def __str__(self):
        return f"{self.course.name} - {self.name}"
