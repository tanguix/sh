# Implementing Role-Based Access Control for Workflows

## Overview

To implement role-based access control for workflows, we need to modify both the frontend and backend components of our application. We'll also need to ensure that user roles are properly managed and authenticated.

## Backend Changes

1. **Update Workflow Model**:
   Add a `allowed_roles` field to the Workflow model to specify which roles can access each workflow.

```python
class Workflow:
    def __init__(self, name, workflow_id, is_locked, status, allowed_roles):
        # ... existing fields ...
        self.allowed_roles = allowed_roles  # List of role names

    def save(self):
        data = {
            # ... existing fields ...
            "allowed_roles": self.allowed_roles
        }
        return db.workflows.insert_one(data)
```

2. **Modify API Endpoints**:
   Update the workflow fetching endpoints to filter based on user roles.

```python
@upload_bp.route('/api/fetch_all_workflow', methods=['GET'])
@jwt_required  # Assuming you're using JWT for authentication
def get_workflow():
    current_user = get_jwt_identity()  # Get the current user's identity
    user_role = get_user_role(current_user)  # Implement this function to get the user's role

    workflow_id = request.args.get('workflow_id')
    
    if workflow_id:
        workflow = Workflow.get_workflow_by_id(workflow_id)
        if workflow and user_role in workflow.allowed_roles:
            return jsonify(workflow), 200
        else:
            return jsonify({"error": "Workflow not found or access denied"}), 403
    else:
        accessible_workflows = Workflow.get_workflows_for_role(user_role)
        return jsonify(accessible_workflows), 200

@upload_bp.route('/api/fetch_locked_workflow', methods=['GET'])
@jwt_required
def get_locked_workflows():
    current_user = get_jwt_identity()
    user_role = get_user_role(current_user)

    locked_workflows = Workflow.get_locked_workflows_for_role(user_role)
    return jsonify(locked_workflows), 200
```

3. **Update Workflow Class Methods**:
   Add methods to filter workflows based on roles.

```python
class Workflow:
    # ... existing methods ...

    @staticmethod
    def get_workflows_for_role(role):
        return list(db.workflows.find({"allowed_roles": role}))

    @staticmethod
    def get_locked_workflows_for_role(role):
        return list(db.workflows.find({"is_locked": True, "allowed_roles": role}))
```

## Frontend Changes

1. **Store User Role**:
   After user login, store the user's role in the application state (e.g., in a Svelte store).

```typescript
// stores.ts
import { writable } from 'svelte/store';

export const userRole = writable<string | null>(null);
```

2. **Update Fetch Functions**:
   Modify the workflow fetching functions to include the user's role in the request (if not already handled by your authentication system).

```typescript
async function fetchLockedWorkflows() {
  isLoading = true;
  hasLockedWorkflows = false;
  try {
    const response = await fetch(API_ENDPOINTS.FETCH_LOCKED_WORKFLOW, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}` // Implement getAuthToken()
      }
    });
    // ... rest of the function ...
  } catch (error) {
    console.error('Error fetching locked workflows:', error);
    alert('Failed to fetch locked workflows. Please try again later.');
  } finally {
    isLoading = false;
  }
}

async function fetchWorkflow(id?: string) {
  // ... existing code ...
  try {
    const url = constructUrl(API_ENDPOINTS.FETCH_ALL_WORKFLOW, {
      workflow_id: workflowIdToFetch,
    });
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    });
    // ... rest of the function ...
  } catch (error) {
    // ... error handling ...
  }
}
```

3. **Handle Unauthorized Access**:
   Update the UI to handle cases where a user doesn't have access to a workflow.

```svelte
{#if workflows.length === 0 && !isLoading}
  <div class="no-workflows">
    {#if hasAttemptedFetch}
      <p>No accessible workflows found or you don't have permission to view any workflows.</p>
    {:else}
      <p>No workflows loaded yet. Use the fetch button to load workflows.</p>
    {/if}
  </div>
{/if}
```

## Authentication and Authorization

1. **Implement User Authentication**:
   If not already in place, implement a robust user authentication system (e.g., using JWT).

2. **Role Management**:
   Create a system to assign and manage user roles. This could be a separate admin interface.

3. **Middleware for Role Checking**:
   Implement middleware on the backend to check user roles for each request.

```python
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            user_role = get_user_role(current_user)
            if user_role not in allowed_roles:
                return jsonify({"error": "Access denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@upload_bp.route('/api/some_protected_route', methods=['GET'])
@jwt_required
@role_required(['admin', 'manager'])
def some_protected_route():
    # ... function implementation ...
```

## Additional Considerations

1. **Frontend Role-Based UI**:
   Adjust the UI to show/hide certain elements based on the user's role.

2. **Audit Logging**:
   Implement audit logging to track who accesses which workflows.

3. **Performance**:
   Consider caching strategies to improve performance, especially if you have many workflows and users.

4. **Testing**:
   Thoroughly test the RBAC system with various user roles and edge cases.

5. **Documentation**:
   Maintain clear documentation on role permissions and workflow access rules.

