from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Разрешение только для администратора"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Роль хранится в самом пользователе (User.role)
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'


class IsTeacher(permissions.BasePermission):
    """Разрешение только для преподавателя"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'teacher'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'teacher'


class IsStudent(permissions.BasePermission):
    """Разрешение только для студента"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'student'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'student'


class IsAdminOrTeacher(permissions.BasePermission):
    """Разрешение для администратора или преподавателя"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin' or request.user.role == 'teacher'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin' or request.user.role == 'teacher'


class IsAdminOrStudent(permissions.BasePermission):
    """Разрешение для администратора или студента"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin' or request.user.role == 'student'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'admin' or request.user.role == 'student'


class IsTeacherOrAdmin(permissions.BasePermission):
    """Разрешение только если user.role == 'teacher' или 'admin'"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'teacher' or request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'teacher' or request.user.role == 'admin'


class IsHomeworkOwner(permissions.BasePermission):
    """Разрешение только если homework.student == request.user"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Для list/create проверяем на уровне queryset/perform_create
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        # Проверяем, что текущий пользователь - это студент, которому принадлежит ДЗ
        return obj.student == request.user