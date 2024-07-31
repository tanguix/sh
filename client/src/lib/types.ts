
// path: "src/lib/types.ts"
// ------------------------
// import type { Writable } from 'svelte/store'; // not in use right now


// --------- Workflow type declared here ---------


export interface File {
  file_id: string;
  name: string;
  type: string;
}

export interface Edge {
  from: string;
  to: string;
}


export interface Section {
  // id: string;
  section_id: string;  // Add this line
  label: string;
  files: File[];
}


export interface Node {
  node_id: string;
  label: string;
  status: 'Sleep' | 'Active' | 'Completed' | 'Error';
  sections: Section[];
}


export interface Workflow {
  workflow_id: string;
  name: string;
  is_locked: boolean;
  nodes: Node[];
  edges: Edge[];
  status: 'created' | 'saved' | 'unsaved';
  owner?: [string, string];
  timestamp: number;
}


// ----------------------------------------------------- "Type" specific to WorkFlow object -----------------------------------------------------
// "Change" type: used for keep track of instructions given by frontend
// this is used for event based operation, but specific for WorkFlow object
export interface Change {
  type: 
    'create_workflow' | 
    'confirm_workflow' | 
    'add_node' | 
    'remove_node' | 
    'add_section' | 
    'remove_section' |  // Add this new type
    'upload_file' | 
    'update_lock_status' |
    'update_node_status';
  data: any;
}



