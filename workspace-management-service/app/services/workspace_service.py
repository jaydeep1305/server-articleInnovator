"""
Workspace Service Module

This module contains business logic for workspace management operations.
It handles workspace creation, member management, permissions, and workspace-related
business rules with comprehensive validation and error handling.

Author: AI Assistant
Date: 2024
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.workspace import Workspace, WorkspaceRole, WorkspaceStatus
from app import db


class WorkspaceService:
    """
    Service class for workspace management operations.
    
    This class encapsulates all business logic related to workspace operations
    including creation, member management, permissions, and workspace settings.
    Implements cognitive patterns for collaborative workspace management.
    """
    
    def __init__(self, session: Session = None):
        """
        Initialize the workspace service.
        
        Args:
            session: SQLAlchemy session (optional)
        """
        self.session = session or db.session
    
    def create_workspace(self, name: str, owner_id: uuid.UUID, 
                        description: str = None, **kwargs) -> Tuple[Workspace, bool, List[str]]:
        """
        Create a new workspace with validation and business rules.
        
        Args:
            name: Workspace name
            owner_id: UUID of the workspace owner
            description: Workspace description (optional)
            **kwargs: Additional workspace attributes
            
        Returns:
            tuple[Workspace, bool, List[str]]: (workspace_instance, success, error_messages)
        """
        try:
            # Check if user has reached workspace limit
            existing_workspaces = self.get_user_workspaces(owner_id)
            max_workspaces = kwargs.get('max_workspaces', 10)  # Get from config
            
            if len(existing_workspaces) >= max_workspaces:
                return None, False, [f"User has reached maximum workspace limit of {max_workspaces}"]
            
            # Check for duplicate workspace names for the same owner
            existing_workspace = self.session.query(Workspace).filter(
                Workspace.name == name.strip(),
                Workspace.owner_id == owner_id,
                Workspace.is_deleted == False
            ).first()
            
            if existing_workspace:
                return None, False, ["Workspace name already exists for this user"]
            
            # Generate unique slug
            base_slug = Workspace._generate_slug(name)
            slug = self._ensure_unique_slug(base_slug)
            
            # Create workspace with validated data
            workspace_data = {
                'name': name.strip(),
                'slug': slug,
                'owner_id': owner_id,
                'description': description.strip() if description else None,
                **kwargs
            }
            
            workspace = Workspace(**workspace_data)
            
            # Validate workspace
            is_valid, errors = workspace.validate()
            if not is_valid:
                return None, False, errors
            
            # Save to database
            self.session.add(workspace)
            self.session.flush()
            
            # Initialize workspace with owner as first member
            workspace.add_member(
                session=self.session,
                user_id=owner_id,
                role=WorkspaceRole.OWNER,
                invited_by=owner_id
            )
            
            self.session.commit()
            
            # TODO: Publish workspace.created event
            # self._publish_event('workspace.created', workspace.to_dict())
            
            return workspace, True, []
            
        except IntegrityError as e:
            self.session.rollback()
            return None, False, ["Database constraint violation occurred"]
        
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Unexpected error occurred: {str(e)}"]
    
    def get_workspace_by_id(self, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        Retrieve workspace by ID.
        
        Args:
            workspace_id: Workspace UUID
            
        Returns:
            Workspace instance or None if not found
        """
        return Workspace.get_by_id(self.session, workspace_id)
    
    def get_workspace_by_slug(self, slug: str) -> Optional[Workspace]:
        """
        Retrieve workspace by slug.
        
        Args:
            slug: Workspace slug
            
        Returns:
            Workspace instance or None if not found
        """
        return Workspace.find_by_slug(self.session, slug)
    
    def get_user_workspaces(self, user_id: uuid.UUID, 
                           include_archived: bool = False) -> List[Workspace]:
        """
        Get all workspaces for a user (owned + member of).
        
        Args:
            user_id: User UUID
            include_archived: Whether to include archived workspaces
            
        Returns:
            List of workspace instances
        """
        # Get owned workspaces
        owned_workspaces = Workspace.find_by_owner(self.session, user_id)
        
        # Get workspaces where user is a member
        from sqlalchemy import and_
        from app.models.workspace import workspace_members
        
        member_workspace_ids = self.session.query(workspace_members.c.workspace_id).filter(
            and_(
                workspace_members.c.user_id == user_id,
                workspace_members.c.is_active == True
            )
        ).subquery()
        
        member_workspaces = self.session.query(Workspace).filter(
            and_(
                Workspace.id.in_(member_workspace_ids),
                Workspace.is_deleted == False
            )
        )
        
        if not include_archived:
            member_workspaces = member_workspaces.filter(
                Workspace.status != WorkspaceStatus.ARCHIVED.value
            )
        
        # Combine and deduplicate
        all_workspaces = list(set(owned_workspaces + member_workspaces.all()))
        
        # Sort by last activity
        return sorted(all_workspaces, key=lambda w: w.last_activity_at, reverse=True)
    
    def update_workspace(self, workspace_id: uuid.UUID, updates: Dict[str, Any],
                        updated_by: uuid.UUID) -> Tuple[Optional[Workspace], bool, List[str]]:
        """
        Update workspace with validation.
        
        Args:
            workspace_id: Workspace UUID
            updates: Dictionary of fields to update
            updated_by: UUID of user making the update
            
        Returns:
            tuple[Workspace, bool, List[str]]: (workspace_instance, success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return None, False, ["Workspace not found"]
            
            # Check permissions (only owner and admins can update)
            user_role = workspace.get_member_role(self.session, updated_by)
            if user_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
                return None, False, ["Insufficient permissions to update workspace"]
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(workspace, field) and field not in ['id', 'created_at', 'owner_id']:
                    setattr(workspace, field, value)
            
            workspace.updated_at = datetime.utcnow()
            workspace.last_activity_at = datetime.utcnow()
            
            # Validate updated workspace
            is_valid, errors = workspace.validate()
            if not is_valid:
                return None, False, errors
            
            self.session.commit()
            
            # TODO: Publish workspace.updated event
            # self._publish_event('workspace.updated', workspace.to_dict())
            
            return workspace, True, []
            
        except Exception as e:
            self.session.rollback()
            return None, False, [f"Error updating workspace: {str(e)}"]
    
    def add_workspace_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID,
                           role: WorkspaceRole = WorkspaceRole.MEMBER,
                           invited_by: uuid.UUID = None) -> Tuple[bool, List[str]]:
        """
        Add a member to a workspace.
        
        Args:
            workspace_id: Workspace UUID
            user_id: User UUID to add
            role: Role to assign to the user
            invited_by: UUID of user who invited this member
            
        Returns:
            tuple[bool, List[str]]: (success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False, ["Workspace not found"]
            
            # Check permissions (only owner and admins can add members)
            if invited_by:
                inviter_role = workspace.get_member_role(self.session, invited_by)
                if inviter_role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
                    return False, ["Insufficient permissions to add members"]
            
            # Add member with validation
            success = workspace.add_member(
                session=self.session,
                user_id=user_id,
                role=role,
                invited_by=invited_by
            )
            
            if success:
                self.session.commit()
                
                # TODO: Publish workspace.member_added event
                # self._publish_event('workspace.member_added', {
                #     'workspace_id': str(workspace_id),
                #     'user_id': str(user_id),
                #     'role': role.value,
                #     'invited_by': str(invited_by) if invited_by else None
                # })
                
                return True, []
            else:
                return False, ["Failed to add member to workspace"]
                
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.session.rollback()
            return False, [f"Error adding member: {str(e)}"]
    
    def remove_workspace_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID,
                              removed_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Remove a member from a workspace.
        
        Args:
            workspace_id: Workspace UUID
            user_id: User UUID to remove
            removed_by: UUID of user performing the removal
            
        Returns:
            tuple[bool, List[str]]: (success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False, ["Workspace not found"]
            
            # Check permissions
            remover_role = workspace.get_member_role(self.session, removed_by)
            target_role = workspace.get_member_role(self.session, user_id)
            
            # Only owners can remove anyone, admins can remove members/guests
            if remover_role == WorkspaceRole.OWNER:
                pass  # Owners can remove anyone except themselves
            elif remover_role == WorkspaceRole.ADMIN:
                if target_role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
                    return False, ["Admins cannot remove owners or other admins"]
            else:
                return False, ["Insufficient permissions to remove members"]
            
            # Cannot remove self if owner
            if user_id == workspace.owner_id and removed_by == user_id:
                return False, ["Workspace owner cannot remove themselves"]
            
            # Remove member
            success = workspace.remove_member(self.session, user_id)
            
            if success:
                self.session.commit()
                
                # TODO: Publish workspace.member_removed event
                # self._publish_event('workspace.member_removed', {
                #     'workspace_id': str(workspace_id),
                #     'user_id': str(user_id),
                #     'removed_by': str(removed_by)
                # })
                
                return True, []
            else:
                return False, ["Member not found in workspace"]
                
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.session.rollback()
            return False, [f"Error removing member: {str(e)}"]
    
    def update_member_role(self, workspace_id: uuid.UUID, user_id: uuid.UUID,
                          new_role: WorkspaceRole, updated_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Update a member's role in a workspace.
        
        Args:
            workspace_id: Workspace UUID
            user_id: User UUID whose role to update
            new_role: New role to assign
            updated_by: UUID of user performing the update
            
        Returns:
            tuple[bool, List[str]]: (success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False, ["Workspace not found"]
            
            # Check permissions (only owners can change roles)
            updater_role = workspace.get_member_role(self.session, updated_by)
            if updater_role != WorkspaceRole.OWNER:
                return False, ["Only workspace owners can update member roles"]
            
            # Cannot change owner role
            if user_id == workspace.owner_id:
                return False, ["Cannot change workspace owner role"]
            
            # Update role
            success = workspace.update_member_role(self.session, user_id, new_role)
            
            if success:
                self.session.commit()
                
                # TODO: Publish workspace.member_role_updated event
                # self._publish_event('workspace.member_role_updated', {
                #     'workspace_id': str(workspace_id),
                #     'user_id': str(user_id),
                #     'new_role': new_role.value,
                #     'updated_by': str(updated_by)
                # })
                
                return True, []
            else:
                return False, ["Member not found in workspace"]
                
        except ValueError as e:
            return False, [str(e)]
        except Exception as e:
            self.session.rollback()
            return False, [f"Error updating member role: {str(e)}"]
    
    def get_workspace_members(self, workspace_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get all members of a workspace.
        
        Args:
            workspace_id: Workspace UUID
            
        Returns:
            List of member dictionaries
        """
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            return []
        
        return workspace.get_members(self.session)
    
    def archive_workspace(self, workspace_id: uuid.UUID, archived_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Archive a workspace.
        
        Args:
            workspace_id: Workspace UUID
            archived_by: UUID of user archiving the workspace
            
        Returns:
            tuple[bool, List[str]]: (success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False, ["Workspace not found"]
            
            # Check permissions (only owner can archive)
            if workspace.owner_id != archived_by:
                return False, ["Only workspace owner can archive workspace"]
            
            workspace.archive()
            self.session.commit()
            
            # TODO: Publish workspace.archived event
            # self._publish_event('workspace.archived', workspace.to_dict())
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error archiving workspace: {str(e)}"]
    
    def restore_workspace(self, workspace_id: uuid.UUID, restored_by: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Restore an archived workspace.
        
        Args:
            workspace_id: Workspace UUID
            restored_by: UUID of user restoring the workspace
            
        Returns:
            tuple[bool, List[str]]: (success, error_messages)
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False, ["Workspace not found"]
            
            # Check permissions (only owner can restore)
            if workspace.owner_id != restored_by:
                return False, ["Only workspace owner can restore workspace"]
            
            workspace.restore()
            self.session.commit()
            
            # TODO: Publish workspace.restored event
            # self._publish_event('workspace.restored', workspace.to_dict())
            
            return True, []
            
        except Exception as e:
            self.session.rollback()
            return False, [f"Error restoring workspace: {str(e)}"]
    
    def update_workspace_storage(self, workspace_id: uuid.UUID, size_mb: int) -> bool:
        """
        Update workspace storage usage.
        
        Args:
            workspace_id: Workspace UUID
            size_mb: Storage size in megabytes to add/subtract
            
        Returns:
            bool: True if updated successfully
        """
        try:
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                return False
            
            workspace.update_storage_usage(self.session, size_mb)
            self.session.commit()
            
            return True
            
        except Exception:
            self.session.rollback()
            return False
    
    def check_workspace_permissions(self, workspace_id: uuid.UUID, user_id: uuid.UUID,
                                  required_role: WorkspaceRole = WorkspaceRole.MEMBER) -> bool:
        """
        Check if user has required permissions in workspace.
        
        Args:
            workspace_id: Workspace UUID
            user_id: User UUID
            required_role: Minimum required role
            
        Returns:
            bool: True if user has sufficient permissions
        """
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            return False
        
        user_role = workspace.get_member_role(self.session, user_id)
        if not user_role:
            return False
        
        # Define role hierarchy
        role_hierarchy = {
            WorkspaceRole.GUEST: 0,
            WorkspaceRole.MEMBER: 1,
            WorkspaceRole.ADMIN: 2,
            WorkspaceRole.OWNER: 3
        }
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
    
    def search_workspaces(self, query: str, user_id: uuid.UUID = None, 
                         limit: int = 20) -> List[Workspace]:
        """
        Search workspaces by name or description.
        
        Args:
            query: Search query string
            user_id: User UUID to filter by user's workspaces (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching workspaces
        """
        from sqlalchemy import or_, func
        
        search_query = self.session.query(Workspace).filter(
            Workspace.is_deleted == False,
            Workspace.status == WorkspaceStatus.ACTIVE.value
        )
        
        if query:
            search_terms = f"%{query}%"
            search_query = search_query.filter(
                or_(
                    func.lower(Workspace.name).like(func.lower(search_terms)),
                    func.lower(Workspace.description).like(func.lower(search_terms))
                )
            )
        
        if user_id:
            # Filter to only workspaces where user is a member
            user_workspaces = self.get_user_workspaces(user_id)
            workspace_ids = [w.id for w in user_workspaces]
            if workspace_ids:
                search_query = search_query.filter(Workspace.id.in_(workspace_ids))
            else:
                return []  # User has no workspaces
        
        return search_query.limit(limit).all()
    
    def _ensure_unique_slug(self, base_slug: str) -> str:
        """
        Ensure workspace slug is unique by appending numbers if needed.
        
        Args:
            base_slug: Base slug to make unique
            
        Returns:
            str: Unique slug
        """
        slug = base_slug
        counter = 1
        
        while True:
            existing = self.session.query(Workspace).filter(
                Workspace.slug == slug,
                Workspace.is_deleted == False
            ).first()
            
            if not existing:
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish workspace events to the event bus.
        
        Args:
            event_type: Type of event to publish
            data: Event data
        """
        # TODO: Implement event publishing with RabbitMQ
        # This would integrate with the event service to publish events
        # for other services to consume
        pass