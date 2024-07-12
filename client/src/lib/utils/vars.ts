
// self defined variable for global useage
import { writable } from 'svelte/store';


// roles for registration
// PROCUREMENT 采购 (professional English name)
export const userRoles = ["Admin", "Data", "Sale", "Finance", "Production", "Procurement"]



// for tracking changes through the web application 
export const unsavedChanges = writable(false);


// constants event variable for eventBus to use 
export const WORKFLOW_CHANGE_EVENT = 'workflowChange';
export const NODE_ADDED_EVENT = 'nodeAdded';
export const STATUS_UPDATED_EVENT = 'statusUpdated';
