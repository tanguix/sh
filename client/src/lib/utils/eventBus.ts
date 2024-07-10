
// eventBus on handles the event, other type like Workflow or File is handled 
// invidually by single function
import type { Change } from '$lib/types';

// define a object type workflowId (workflow_id(key) = workflowId(parameter) )
type ChangeEvent = {
  workflowId: string;                   // string type
  change: Change;                       // Change type
};

  /* 
  Typescript way of creating variable object 
    1) Record<string, (() => ())[]>
      - string type is refer to the key type in Record Object 
      - you can think of it creates an json object {key: xxx, value: xxx} with that declaration
      - inside this Record type, key is string, while value is an array of function
      - () => (), remember this represent arrow functions in js
    2) (event: ChangeEvent) => void, same thing in C++, doesn't return anything or things return no in used 
      - for type safety propuse
      - also this function takes in a parameter event, with type ChangeEvent
    3) at the end = {} 
      - assign an empty object to this newly declared Record type {}, otherwise you just create a type without value


    Few things to note: 
    4) what's a callback function? 
       - function A that was passed to another function B as an argument, A is intended to execute later
       - executing later can mean: B will decide when to invoke A
    5) svelte store 
       - think of it as a class in python, you can create reactive object in store 
       - here changes.update() is function B, const act => {} is function A, changes store frontend operation
       - currentChange is temp variable hold the current value in changes array (reactive array)
       - is like the "i" in for loop
  */ 

function createEventBus() {

  const listeners: Record<string, ((event: ChangeEvent) => void)[]> = {};

  // same, declaration here, but simpler ==> basically, listeners are event list (actions), changes are instruction list
  const changes: Record<string, Change[]> = {};

  // perform those behaviors
  return {
    // on is a method in js, this method is to add new event listener
    // callback is a function to be called when event is emitted (fired)
    on: (eventName: string, callback: (event: ChangeEvent) => void) => {
      // if not name provided, assign an empty list
      if (!listeners[eventName]) {
        listeners[eventName] = [];
      }
      // push the function to Record list (as instruction)
      listeners[eventName].push(callback);
    },

    // Trigger the event, and store the changes
    emit: (eventName: string, event: ChangeEvent) => {
      // if there is a listener for this event
      if (listeners[eventName]) {
        // fire the callback function with event info passed to it
        listeners[eventName].forEach(callback => callback(event)); 
      }
      // same, just checking different type object
      if (!changes[event.workflowId]) {
        changes[event.workflowId] = [];
      }
      changes[event.workflowId].push(event.change);
    },
    // Just so you know, this is a built-in method 
    // collect/retrieve all changes for a specific workflow given its workflow id
    getChangesForWorkflow: (workflowId: string) => changes[workflowId] || [],
    // also a built-in method
    // for later usage, clearing all instruction for a specific workflow given id
    clearChanges: (workflowId: string) => {
      changes[workflowId] = [];
    }
  };
}

export const eventBus = createEventBus();
