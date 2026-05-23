"""
Base repository providing common CRUD operations.
Implements the Repository pattern for data access abstraction.
"""
from typing import Optional, List, Dict, Any
from django.db.models import Model, QuerySet


class BaseRepository:
    """
    Abstract base repository with common CRUD operations.
    Follows the Repository pattern to separate data access from business logic.
    """
    
    def __init__(self, model: type[Model]):
        """
        Initialize repository with a Django model.
        
        Args:
            model: Django model class to perform operations on
        """
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[Model]:
        """
        Retrieve a single record by primary key.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            return self.model.objects.get(pk=id)
        except self.model.DoesNotExist:
            return None
    
    def get_all(self) -> QuerySet:
        """
        Retrieve all records.
        
        Returns:
            QuerySet of all model instances
        """
        return self.model.objects.all()
    
    def filter(self, **kwargs) -> QuerySet:
        """
        Filter records by field values.
        
        Args:
            **kwargs: Field name and value pairs for filtering
            
        Returns:
            QuerySet of matching instances
        """
        return self.model.objects.filter(**kwargs)
    
    def create(self, **kwargs) -> Model:
        """
        Create a new record.
        
        Args:
            **kwargs: Field name and value pairs for the new instance
            
        Returns:
            Created model instance
        """
        return self.model.objects.create(**kwargs)
    
    def update(self, id: int, **kwargs) -> Optional[Model]:
        """
        Update an existing record.
        
        Args:
            id: Primary key of the record to update
            **kwargs: Field name and value pairs to update
            
        Returns:
            Updated model instance if found, None otherwise
        """
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
        return instance
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by primary key.
        
        Args:
            id: Primary key of the record to delete
            
        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if instance:
            instance.delete()
            return True
        return False
    
    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists matching the given criteria.
        
        Args:
            **kwargs: Field name and value pairs for filtering
            
        Returns:
            True if at least one matching record exists, False otherwise
        """
        return self.model.objects.filter(**kwargs).exists()
    
    def count(self, **kwargs) -> int:
        """
        Count records matching the given criteria.
        
        Args:
            **kwargs: Field name and value pairs for filtering
            
        Returns:
            Number of matching records
        """
        if kwargs:
            return self.model.objects.filter(**kwargs).count()
        return self.model.objects.count()
