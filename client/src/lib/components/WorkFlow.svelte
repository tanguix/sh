<script lang="ts">

  import { onMount } from 'svelte';
  import { writable, derived, get } from 'svelte/store';
  import { API_ENDPOINTS, constructUrl } from '../utils/api';
  import Pipeline from './Pipeline.svelte';
  import type { Workflow, Node, Edge, Section, File } from '$lib/types';
  import { unsavedChanges } from '$lib/stores/unsavedChanges';


  // ----------------------------------------------------- "Type" specific to WorkFlow object -----------------------------------------------------
  // "Change" type: used for keep track of instructions given by frontend
  interface Change {
    type: 
      'create_workflow' | 
      'confirm_workflow' | 
      'add_node' | 
      'remove_node' | 
      'add_section' | 
      'upload_file' | 
      'update_lock_status';
    data: any;
  }


  // ----------------------------------------------------- Variable Declaration -----------------------------------------------------

  let workflows: Workflow[] = [];           // an array of workflow object
  let workflowName = '';                    // the name of certain workflow object
  let workflow_id = '';                     // workflow id, unique identifier generated
  const changes = writable<Change[]>([]);   // svelte reactive array of an array of "Change" type, 
                                            // because needed to be constantly updated 

  let isWorkflowLocked = false;             // Lock status of workflow, TODO: later use for modification permission (now is reactive component)
  let newNodeLabel = '';                    // newly added node label
  let newNodePrevId = '';                   // node's previous node's id in workflow data strcuture
  let recentChange: Change | null = null;   // for tracking changes
 


    // const nodes = writable<Node[]>([]);
    // const edges = writable<Edge[]>([]);
    // const workflowStatus = writable('');
    // const workflowState = writable<'draft' | 'confirmed'>('draft');






  // TODO: remember to get the user from locals: 
  // 1) pass user as key for workflow 
  // 2) use users to set permission of lock button 
  // 3) append the username to the end of (unique_id + timestemp) => workflow, node, section, file?




  // ----------------------------------------------------- Debugging/Logging Function -----------------------------------------------------
  // automatically track changes in "changes" variable
  onMount(() => {
    const unsubscribe = changes.subscribe(value => {
      console.log('Current changes:', value);
    });
    return unsubscribe;
  });


  // not sure if this is necessary
  function logChange(newChange: Change) {
    console.log('Recent change:', newChange);
    recentChange = newChange;
  }





  // ----------------------------------------------------- Frontend Interaction Function -----------------------------------------------------

  // "CustomEvent" type is for event that parent send(dispatch 派遣) to child component for communication
  // <Pipeline /> is created inside <WorkFlow />, so former is the parent, latter is the child
  function handleNodeClick(event: CustomEvent<string>) {
    const nodeId = event.detail;                                      // extract the data(detail) in the event
    const sectionElement = document.getElementById(nodeId);           // get the HTML element in the document with an ID matching nodeID
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth' });          // js built-in method, scroll to tag contains id=nodeID
    }                                                                 // scroll smoothly, random than instantly
  }

  // strings after semi-colon ensure function will return one of the string (type safety)
  // like the python def xxx() -> str:
  function getNodeStatus(node: Node): 'Completed' | 'In Progress' | 'Not Started' | 'Error' {
    return node.status;
  }















  // ----------------------------------------------------- Workflow Helper Function -----------------------------------------------------




  // 1)
  // parameters => obj_type: (again, for type safety)  |  label: name of node  |  existingItems: existing workflow objects with workflow_id
  function generateUniqueId(
    obj_type: 'workflow' | 'node' | 'section' | 'file',
    label: string,
    existingItems: { id?: string; workflow_id?: string; node_id?: string; section_id?: string }[] 
  ): string 
  {
    const prefix = {
      'workflow': 'wf-',
      'node': 'node-',
      'section': 'section-',
      'file': 'file-'
    }[obj_type];

    const baseId = `${prefix}${label.toLowerCase().replace(/\s+/g, '_')}`;
    let uniqueId = baseId;
    let counter = 1;

    // Check for uniqueness based on the object type
    while (existingItems.some(item => 
      item.id === uniqueId || 
      item.workflow_id === uniqueId || 
      item.node_id === uniqueId || 
      item.section_id === uniqueId
    )) {
      uniqueId = `${baseId}-${counter}`;
      counter++;
    }

    // Append the current timestamp
    return `${uniqueId}-${Date.now()}`;
  }





  // 2)
  // create default array of section type json: Section[]
  function createDefaultSections(): Section[] {
    const sectionId = generateUniqueId('section', 'expense', []);
    console.log(`Creating default section with ID: ${sectionId}`);
    return [
      {
        section_id: sectionId,
        label: 'Expense',
        files: []
      },
    ];
  }







  // ----------------------------------------------------- Main WorkFlow (modify data sent to backend) -----------------------------------------------------

  // @create a default workflow array
  function createWorkflow() {

    if (!workflowName) {
      alert('Please enter a workflow name');
      return;
    }
    
    // HACK: properly not needed to check if ID is unique from database because (prefix + timestamp + username)
    // generate unique workflow id: 
    const workflowId = generateUniqueId('workflow', workflowName, workflows);

    // Create nodes with unique IDs and sections
    // const newNodes = ['Sampling', 'Production', 'Delivery', 'Payment'].map(label => {
    const newNodes = ['TEST_1', 'TEST_2'].map(label => {
      const nodeId = generateUniqueId('node', label, []);
      return {
        node_id: nodeId,
        label: label,
        status: 'Not Started',
        sections: createDefaultSections()
      };
    });


    // Create edges using the node IDs
    const newEdges = newNodes.slice(0, -1).map((node, index) => ({
      from: node.node_id,
      to: newNodes[index + 1].node_id
    }));


    // create workflow object
    const newWorkflow: Workflow = { 
        workflow_id: workflowId, 
        name: workflowName, 
        is_locked: isWorkflowLocked,
        nodes: newNodes,
        edges: newEdges,
        status: 'created',
    };

    // "..." operator mean spread the element in the array after it (workflows)
    // after spreading adding the item or array(newWorkflow) after comma to it and create a new array
    // this method does not modify the original array directly, 
    // and js will free up memory when original one is not referred anymore
    workflows = [...workflows, newWorkflow];

    console.log('Newly created workflow:', newWorkflow); // Log created workflow

    /* 
    Few things to note: 
    1) what's a callback function? 
       - function A that was passed to another function B as an argument, A is intended to execute later
       - executing later can mean: B will decide when to invoke A
    2) svelte store 
       - think of it as a class in python, you can create reactive object in store 
       - here changes.update() is function B, const act => {} is function A, changes store frontend operation
       - currentChange is temp variable hold the current value in changes array (reactive array)
       - is like the "i" in for loop
    3) update 
       - below is updating the empty changes array
    */
    changes.update(act => {
        const newChange = { 
            type: 'create_workflow', 
            data: { 
                name: workflowName, 
                workflow_id: workflowId, 
                is_locked: isWorkflowLocked,
                nodes: newWorkflow.nodes, 
                edges: newWorkflow.edges,
                status: newWorkflow.status,
            } 
        };
        logChange(newChange)
        return [...act, newChange];
    });
    // set the unsavedChange status to true prevent user leaving unexpectedly
    unsavedChanges.set(true);
  }



  // @toggle the status of a node
  function toggleNodeStatus(workflowId: string, nodeId: string) {
    // findIndex is an array method built-in: (for w in workflow) {return w (w.workflow_id = workflowId)}
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1) return;   // return nothing if index = -1

    /* .map is a built-in array method
        - create new array by calling a provided function (callback function) on every element
        - map() iterate over each node in the original array
        - "() => {}": this is an arrow function, ( parameters ) => { operation } 
        - map to an node -> check the node id in callback -> modify the node status associated with that node_id
        - assign new status -> 
    */
    workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.map((node) => {
      if (node.node_id === nodeId) {

        let newStatus: 'Not Started' | 'In Progress' | 'Completed' | 'Error';   // type safety
        switch (node.status) {
          case 'Not Started':
            newStatus = 'In Progress';
            break;
          case 'In Progress':
            newStatus = 'Error';
            break;
          case 'Error':
            newStatus = 'Completed';
            break;
          case 'Error':
            newStatus = 'Not Started';
            break;
        }

        // new status update, update changes to "changes" variable
        changes.update(act => {
          // create new variable for storing new changes
          const newChange = { 
            type: 'update_node_status',     // give it a type
            data: { 
              workflow_id: workflowId,      // workflow_id for identification
              node_id: node.node_id,        // same for node_id
              status: newStatus             // but set the new status
            } 
          };
          logChange(newChange);
          return [...act, newChange];
        });

        unsavedChanges.set(true);
        return {...node, status: newStatus};
      }

      return node;
    });
    workflows = [...workflows];
  }







    function confirmWorkflowCreation(workflowId: string) {
      const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
      if (workflowIndex === -1) {
        alert('Workflow not found');
        return;
      }

      workflows[workflowIndex].is_locked = true;
      workflows = [...workflows];

      changes.update(c => [...c, { 
        type: 'update_lock_status', 
        data: { workflow_id: workflowId, is_locked: true } 
      }]);
      unsavedChanges.set(true);
    }

    function releaseWorkflow(workflowId: string) {
      const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
      if (workflowIndex === -1) return;

      workflows[workflowIndex].is_locked = false;
      workflows = [...workflows];

      changes.update(c => [...c, { 
        type: 'update_lock_status', 
        data: { workflow_id: workflowId, is_locked: false } 
      }]);
      unsavedChanges.set(true);
    }

    function toggleLockStatus(workflowId: string) {
      const workflow = workflows.find(w => w.workflow_id === workflowId);
      if (workflow) {
        if (workflow.is_locked) {
          releaseWorkflow(workflowId);
        } else {
          confirmWorkflowCreation(workflowId);
        }
      }
    }



    function addNode(workflowId: string) {
      const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
      if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
        alert('Cannot add node. Workflow is locked or not found.');
        return;
      }

      const newNodeId = generateUniqueId('node', newNodeLabel, workflows[workflowIndex].nodes);
      const newNode: Node = {
        node_id: newNodeId,
        label: newNodeLabel,
        status: 'Not Started',
        sections: createDefaultSections()
      };
      
      const prevNode = workflows[workflowIndex].nodes.find(node => node.label.toLowerCase() === newNodePrevId.toLowerCase());
      let updatedEdges = [...workflows[workflowIndex].edges];
      
      if (prevNode) {
        updatedEdges.push({ from: prevNode.node_id, to: newNode.node_id });
        
        const nextNodeIndex = workflows[workflowIndex].nodes.findIndex(n => n.node_id === prevNode.node_id) + 1;
        if (nextNodeIndex < workflows[workflowIndex].nodes.length) {
          const nextNode = workflows[workflowIndex].nodes[nextNodeIndex];
          const existingEdgeIndex = updatedEdges.findIndex(edge => edge.from === prevNode.node_id && edge.to === nextNode.node_id);
          
          if (existingEdgeIndex !== -1) {
            updatedEdges[existingEdgeIndex] = { ...updatedEdges[existingEdgeIndex], from: newNode.node_id };
          } else {
            updatedEdges.push({ from: newNode.node_id, to: nextNode.node_id });
          }
        }
      } else if (workflows[workflowIndex].nodes.length > 0) {
        updatedEdges.push({ from: workflows[workflowIndex].nodes[workflows[workflowIndex].nodes.length - 1].node_id, to: newNode.node_id });
      }

      workflows[workflowIndex].nodes = [...workflows[workflowIndex].nodes, newNode];
      workflows[workflowIndex].edges = updatedEdges;
      workflows = [...workflows];

      changes.update(c => {
        const newChange = { 
          type: 'add_node', 
          data: { 
            workflow_id: workflowId,
            node: newNode,
            edges: updatedEdges
          } 
        };
        logChange(newChange);
        return [...c, newChange];
      });

      unsavedChanges.set(true);
      newNodeLabel = '';
      newNodePrevId = '';
    }



    function removeNode(workflowId: string, nodeId: string) {
      const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
      if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
        alert('Cannot remove node. Workflow is locked or not found.');
        return;
      }

      const nodeToRemove = workflows[workflowIndex].nodes.find(node => node.node_id === nodeId);
      if (!nodeToRemove) {
        console.error(`Node with id ${nodeId} not found`);
        return;
      }

      workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.filter(node => node.node_id !== nodeId);
      
      let updatedEdges = workflows[workflowIndex].edges.filter(edge => edge.from !== nodeId && edge.to !== nodeId);
      const incomingEdge = workflows[workflowIndex].edges.find(edge => edge.to === nodeId);
      const outgoingEdge = workflows[workflowIndex].edges.find(edge => edge.from === nodeId);
      if (incomingEdge && outgoingEdge) {
        updatedEdges.push({ from: incomingEdge.from, to: outgoingEdge.to });
      }

      workflows[workflowIndex].edges = updatedEdges;
      workflows = [...workflows];

      changes.update(c => {
        const newChange = { 
          type: 'remove_node', 
          data: { 
            workflow_id: workflowId,
            node_id: nodeToRemove.node_id,
            edges: updatedEdges
          } 
        };
        logChange(newChange);
        return [...c, newChange];
      });
      unsavedChanges.set(true);
    }

    let newSectionLabel = '';
    let addingSectionToNodeId: string | null = null;

    function startAddingSection(nodeId: string) {
      addingSectionToNodeId = nodeId;
      newSectionLabel = '';
    }

    function cancelAddingSection() {
      addingSectionToNodeId = null;
      newSectionLabel = '';
    }





    function addSection(workflowId: string, nodeId: string) {
      const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
      if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
        alert('Cannot add section. Workflow is locked or not found.');
        return;
      }

      if (!newSectionLabel) {
        alert('Please enter a section label.');
        return;
      }

      // const newSectionId = `section-${newSectionLabel.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`;
      const newSectionId = generateUniqueId('section', newSectionLabel.toLowerCase(), []);

      workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.map(node => {
        if (node.node_id === nodeId) {
          const newSection = {
            // id: newSectionId,
            section_id: newSectionId,  // Add this line
            label: newSectionLabel,
            files: []
          };

          changes.update(c => {
            const newChange = { 
              type: 'add_section', 
              data: { 
                workflow_id: workflowId,
                node_id: node.node_id,
                section: newSection 
              } 
            };
            console.log('Section added:', newChange);
            return [...c, newChange];
          });

          unsavedChanges.set(true);
          return {...node, sections: [...node.sections, newSection]};
        }
        return node;
      });

      workflows = [...workflows];
      addingSectionToNodeId = null;
      newSectionLabel = '';
    }






    async function uploadFiles(workflowId: string, nodeId: string, sectionId: string, event: Event) {
        console.log(`uploadFiles called with workflowId: ${workflowId}, nodeId: ${nodeId}, sectionId: ${sectionId}`);
        
        if (!sectionId || sectionId === 'undefined') {
            console.error('Invalid section ID');
            alert('Error: Invalid section ID. Please try again or contact support.');
            return;
        }

        const target = event.target as HTMLInputElement;
        if (!target.files || target.files.length === 0) {
            console.error('No files selected');
            return;
        }

        const files = Array.from(target.files);
        const formData = new FormData();
        formData.append('workflow_id', workflowId);
        formData.append('node_id', nodeId);
        formData.append('section_id', sectionId);

        console.log(`FormData:`, {
            workflow_id: formData.get('workflow_id'),
            node_id: formData.get('node_id'),
            section_id: formData.get('section_id')
        });

        const fileDataArray = files.map(file => ({
            file_id: generateUniqueId('file', file.name, []),
            name: file.name,
            type: file.type,
            size: file.size
        }));

        files.forEach((file, index) => {
            formData.append('files', file);
        });
        formData.append('file_data', JSON.stringify(fileDataArray));

        try {
            console.log('Attempting to upload files to:', API_ENDPOINTS.UPLOAD_FILE);
            const response = await fetch(API_ENDPOINTS.UPLOAD_FILE, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const result = await response.json();
            console.log('Upload response:', result);

            // Update local state to reflect the new files
            workflows = workflows.map(workflow => {
                if (workflow.workflow_id === workflowId) {
                    workflow.nodes = workflow.nodes.map(node => {
                        if (node.node_id === nodeId) {
                            node.sections = node.sections.map(section => {
                                if (section.section_id === sectionId) {  // Changed from section.id to section.section_id
                                    const successfulUploads = result.results.filter(r => r.message === "File uploaded successfully");
                                    const newFiles = successfulUploads.map(upload => {
                                        const fileData = fileDataArray.find(f => f.file_id === upload.file_id);
                                        return fileData ? fileData : null;
                                    }).filter(Boolean);
                                    
                                    section.files = [...(section.files || []), ...newFiles];
                                }
                                return section;
                            });
                        }
                        return node;
                    });
                }
                return workflow;
            });

        } catch (error) {
            console.error('Error uploading files:', error);
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                console.error('Network error: Unable to connect to the server. Please check your internet connection and server status.');
            }
            alert('Failed to upload files. Please try again later.');
        }
    }






    async function commitChanges() {
      const allChanges = get(changes);
    
      try {
        const response = await fetch(API_ENDPOINTS.WORKFLOW_COMMIT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({ changes: allChanges }),
        });

        console.log("see the response:", response);
        if (!response.ok) {
          throw new Error('Failed to commit changes');
        }

        const result = await response.json();
        console.log('Changes committed successfully:', result);

        changes.set([]);
        unsavedChanges.set(false);

      } catch (error) {
        console.error('Error committing changes:', error);
        alert('Failed to commit changes. Please try again.');
      }
    }





    async function fetchWorkflow() {
        if (!workflow_id) {
            alert('Please enter a workflow ID');
            return;
        }

        try {
            const url = constructUrl(API_ENDPOINTS.FETCH_ALL_WORKFLOW, {
                workflow_id: workflow_id,
            });

            console.log(`Fetching workflow with URL: ${url}`);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to fetch workflow: ${response.status} ${response.statusText}`);
            }

            const workflow = await response.json();
            console.log('Fetched workflow:', workflow);


            // Ensure that each node has a sections array and each section has a files array
            const processedNodes = workflow.nodes.map(node => ({
                ...node,
                sections: (node.sections || []).map(section => ({
                    ...section,
                    files: section.files || []
                }))
            }));

            if (!workflows.some(w => w.id === workflow.workflow_id)) {
                workflows = [...workflows, {
                    workflow_id: workflow.workflow_id,
                    name: workflow.name,
                    is_locked: workflow.is_locked,
                    nodes: sortNodesByEdges(processedNodes, workflow.edges),
                    edges: workflow.edges,
                    status: workflow.status || 'saved',  // defaulting to 'saved' if not provided
                }];
            } else {
                alert('This workflow is already displayed.');
            }


            workflow_id = '';

        } catch (error) {
            console.error('Error fetching workflow:', error);
            alert(`Failed to fetch workflow: ${error.message}`);
        }
    }






    function sortNodesByEdges(nodes: Node[], edges: Edge[]): Node[] {
      const nodeMap = new Map(nodes.map(node => [node.node_id, node]));
      const sortedNodes: Node[] = [];
      const visited = new Set<string>();

      function dfs(nodeId: string) {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);
        
        const node = nodeMap.get(nodeId);
        if (node) {
          sortedNodes.push(node);
        }

        const outgoingEdges = edges.filter(edge => edge.from === nodeId);
        for (const edge of outgoingEdges) {
          dfs(edge.to);
        }
      }

      const startNodes = nodes.filter(node => 
        !edges.some(edge => edge.to === node.node_id)
      );

      for (const startNode of startNodes) {
        dfs(startNode.node_id);
      }

      for (const node of nodes) {
        if (!visited.has(node.node_id)) {
          sortedNodes.push(node);
        }
      }

      return sortedNodes;
    }





    function downloadFile(workflowId: any, nodeId: any, sectionId: any, fileId: any, fileName: any) {
      const downloadUrl = `${API_ENDPOINTS.DOWNLOAD_FILE}/${workflowId}/${nodeId}/${sectionId}/${fileId}`;
      
      fetch(downloadUrl)
        .then(response => {
          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('File not found in the specified section');
            }
            throw new Error('Network response was not ok');
          }
          const contentDisposition = response.headers.get('Content-Disposition');
          let serverFileName = fileName;
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
            if (filenameMatch) {
              serverFileName = filenameMatch[1];
            }
          }
          return response.blob().then(blob => ({ blob, fileName: serverFileName }));
        })
        .then(({ blob, fileName }) => {
          if ('showSaveFilePicker' in window) {
            return window.showSaveFilePicker({
              suggestedName: fileName,
              types: [{
                description: 'File',
                accept: { [blob.type]: [`.${fileName.split('.').pop()}`] }
              }]
            }).then(handle => handle.createWritable())
              .then(writable => {
                writable.write(blob);
                return writable.close();
              });
          } else {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
          }
        })
        .catch(error => {
          // Check if the error is due to user canceling the download
          if (error.name === 'AbortError') {
            // User canceled the download, do nothing
            console.log('Download canceled by user');
          } else {
            // For other errors, log to console but don't show an alert
            console.error('Download failed:', error);
          }
        });
    }









</script>

<main>
  <div>
    <input bind:value={workflow_id} placeholder="Enter workflow ID to fetch" />
    <button on:click={fetchWorkflow}>Add Workflow</button>
  </div>

  {#if workflows.length === 0}
    <div>
      <input bind:value={workflowName} placeholder="Enter workflow name" />
      <button on:click={createWorkflow}>Create New Workflow</button>
    </div>
  {/if}


  {#each workflows as workflow (workflow.workflow_id)}
    <div class="workflow">
      <h2>{workflow.name}</h2>
      <button on:click={() => toggleLockStatus(workflow.workflow_id)}>
        {workflow.is_locked ? 'Release' : 'Lock'}
      </button>

      <Pipeline nodes={workflow.nodes} edges={workflow.edges} on:nodeClick={handleNodeClick} />

      {#each sortNodesByEdges(workflow.nodes, workflow.edges) as node}
        <section id={node.node_id}>
          <h3>{node.label}</h3>
          <p>Status: {getNodeStatus(node)}</p>
          <button on:click={() => toggleNodeStatus(workflow.workflow_id, node.node_id)} disabled={workflow.is_locked}>
            {#if node.status === 'Not Started'}
              Start Node
            {:else if node.status === 'In Progress'}
              Error
            {:else if node.status === 'Error'}
              Mark as Completed
            {:else}
              Reset to Not Started
            {/if}
          </button>

          <p>Details about {node.label.toLowerCase()}...</p>

          {#if addingSectionToNodeId === node.node_id}
            <form on:submit|preventDefault={() => addSection(workflow.workflow_id, node.node_id)}>
              <input 
                type="text" 
                bind:value={newSectionLabel} 
                placeholder="Enter section label"
                required
              />
              <button type="submit" disabled={workflow.is_locked}>Add</button>
              <button type="button" on:click={cancelAddingSection}>Cancel</button>
            </form>
          {:else}
            <button on:click={() => startAddingSection(node.node_id)} disabled={workflow.is_locked}>Add Section</button>
          {/if}
          



          {#each node.sections as section}


              <div>
                <h4>{section.label}</h4>
                <p>Debug: section.section_id = {section.section_id}</p>
                {#if node.status === 'In Progress' && workflow.status === 'saved'}
                  <input 
                    type="file" 
                    multiple
                    on:change={(event) => uploadFiles(workflow.workflow_id, node.node_id, section.section_id, event)} 
                    disabled={workflow.is_locked}
                  />
                {/if}
                {#if section.files && section.files.length > 0}
                  <ul>
                    {#each section.files as file}
                      <li>
                        {file.name} ({file.type})
                        <button on:click={() => downloadFile(workflow.workflow_id, node.node_id, section.section_id, file.file_id, file.name)}>
                            Download
                        </button>
                      </li>
                    {/each}
                  </ul>
                {/if}
              </div>

 
          {/each}
          <button on:click={() => removeNode(workflow.workflow_id, node.node_id)} disabled={workflow.is_locked}>Remove Node</button>
        </section>
      {/each}




      {#if !workflow.is_locked}
        <section>
          <h3>Add New Node</h3>
          <form on:submit|preventDefault={() => addNode(workflow.workflow_id)}>
            <div>
              <label>
                Label:
                <input type="text" bind:value={newNodeLabel} required />
              </label>
            </div>
            <div>
              <label>
                Connect after node (enter node label):
                <input type="text" bind:value={newNodePrevId} />
              </label>
            </div>
            <button type="submit">Add Node</button>
          </form>
        </section>
      {/if}
    </div>
  {/each}

  <button on:click={commitChanges} disabled={!$unsavedChanges}>Commit All Changes</button>
</main>
