
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
  id: string;
  section_id: string;  // Add this line
  label: string;
  files: File[];
}


export interface Node {
  node_id: string;
  label: string;
  status: 'Not Started' | 'In Progress' | 'Completed';
  sections: Section[];
}


// TODO: create a new status, warnings for something wrong(marked with color red)
export interface Workflow {
  id: string;
  name: string;
  is_locked: boolean;
  nodes: Node[];
  edges: Edge[];
  status: 'created' | 'saved';
}






