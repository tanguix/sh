
// src/types.ts
export interface Node {
  id: string;
  label: string;
  completed: boolean;
}

export interface Edge {
  from: string;
  to: string;
}
