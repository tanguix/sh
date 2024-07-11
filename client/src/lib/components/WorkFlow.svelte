<script lang="ts">
  import { onMount } from 'svelte';
  import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';
  import Pipeline from './Pipeline.svelte';
  import type { Workflow, Node, Edge, Section, Change } from '$lib/types';
  import { unsavedChanges } from '$lib/utils/vars';
  import { eventBus } from '$lib/utils/eventBus';
  import { WORKFLOW_CHANGE_EVENT } from '$lib/utils/vars'
  // css component 
  import Loader from '$lib/components/css/Loader.svelte';



  // ----------------------------------------------------- Variable Declaration -----------------------------------------------------
  let workflows: Workflow[] = [];                       // array of workflow object
  let workflowName = '';                                // workflowName used when creating workflow
  let workflow_id = '';                                 // 
  let isWorkflowLocked = false;                         // lock status TODO: later use for modification permission (now is reactive component)
  let newNodeLabel = '';                                // newly added node's label (name)  (coming from html)
  let newNodePrevLabel = '';                            // placeholder for previous node label (coming from html)
  let newSectionLabel = '';                             // same
  let addingSectionToNodeId: string | null = null;      // catch the section parent node id


  // New variables for loading state and locked workflows
  let isLoading = false;
  let hasLockedWorkflows = false;
  let initialLoadComplete = false;                      // backend fetch loading, this is separated from workflow loading

  // ----------------------------------------------------- Frontend Interaction Function -----------------------------------------------------


  // "CustomEvent" type is for event that parent send(dispatch 派遣) to child component for communication
  // <Pipeline /> is created inside <WorkFlow />, so former is the parent, latter is the child
  function handleNodeClick(event: CustomEvent<string>) {
    const nodeId = event.detail;
    const sectionElement = document.getElementById(nodeId);       // get the HTML element in the document with an ID matching nodeID
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth' });      // js built-in method, scroll to tag contains id=nodeID
    }                                                             // scroll smoothly, rather than instantly
  }

  // strings after semi-colon ensure function will return one of the string (type safety)
  // like the python def xxx() -> str:
  function getNodeStatus(node: Node): 'Completed' | 'In Progress' | 'Not Started' | 'Error' {
    return node.status;
  }

  // assign values for rendering and backend record if add
  function startAddingSection(nodeId: string) {
    addingSectionToNodeId = nodeId;
    newSectionLabel = '';
  }

  // reset value for rendering and backend (set to null)
  function cancelAddingSection() {
    addingSectionToNodeId = null;
    newSectionLabel = '';
  }

  // ----------------------------------------------------- State Status Management eventBus -----------------------------------------------------


  // constantly listen to changes happening across the web application, when changes found 
  // add to listeners variable in eventBus.ts for execution
  onMount(() => {
    eventBus.on(WORKFLOW_CHANGE_EVENT, ({ workflowId, change }) => {
      console.log(`Change in workflow ${workflowId}:`, change);
    });
    fetchLockedWorkflows();
  });


  // fire the instruction when this function is called 
  // it must have the same name (string type) as the on: method in eventBus (you can name it anything)
  // that's for eventBus to indentify which instruction should related to which action
  // please refer to the above one
  function emitChange(workflowId: string, change: Change) {
    eventBus.emit(WORKFLOW_CHANGE_EVENT, { workflowId, change });
    unsavedChanges.set(true);

    // Set the workflow status to "unsaved" when a change is made
    workflows = workflows.map(workflow => 
      workflow.workflow_id === workflowId 
        ? { ...workflow, status: "unsaved" }
        : workflow
    );
  }

  // ----------------------------------------------------- Workflow Helper Function -----------------------------------------------------


  // 1)
  // checking existing ID, pass in obj_type and label to create unique ID
  // parameters => obj_type: (again, for type safety)
  function generateUniqueId(obj_type: 'workflow' | 'node' | 'section' | 'file', label: string, existingItems: any[]): string {
    // const prefix is like a json, obj_tyoe are keys, each key stand for a prefix string
    // basically you access the prefix using obj_type(key) passed in as parameter:  prefix = {json}[key]
    const prefix = { 'workflow': 'wf-', 'node': 'node-', 'section': 'section-', 'file': 'file-' }[obj_type];
    // concatenation: prefix + label TODO: do I have to make it case sensitive?

    const baseId = `${prefix}${label.toLowerCase().replace(/\s+/g, '_')}`;
    let uniqueId = baseId;
    let counter = 1;

    // Check for uniqueness based on the object type, passed in an array
    while (existingItems.some(item => 
      item.id === uniqueId || 
      item.workflow_id === uniqueId || 
      item.node_id === uniqueId || 
      item.section_id === uniqueId
    )) {
      uniqueId = `${baseId}-${counter}`;
      counter++;
    }

    // TODO: remember to get the user from locals: 
    // 1) pass user as key for workflow 
    // 2) use users to set permission of lock button 
    // 3) append the username to the end of (unique_id + timestemp) => workflow, node, section, file?

    // Append the current timestamp
    return `${uniqueId}-${Date.now()}`;
  }


  // 2)
  // create default array of section type json: Section[], but leave it empty for now
  // assume every node will have expense section
  function createDefaultSections(): Section[] {
    const sectionId = generateUniqueId('section', 'expense', []);
    return [
      {
        section_id: sectionId,
        label: 'Expense',
        files: []
      },
    ];
  }

  // ------------------------------------------ Main WorkFlow Instruction (modify data sent to backend) ------------------------------------------

  // 1) 
  // create default workflow array 
  function createWorkflow() {
    if (!workflowName) {
      alert('Please enter a workflow name');
      return;
    }
    
    // HACK: properly not needed to check if ID is unique from database because (prefix + timestamp + username)
    // generate unique workflow id: 
    const workflowId = generateUniqueId('workflow', workflowName, workflows);

    // Create nodes with unique IDs and sections
    // here newNodes is the label we initialize for default nodes, map() function iterate over each label in newNodes
    // passing them to generated unique ID
    const newNodes = ['Sampling', 'Production', 'Delivery', 'Payment'].map(label => {
      const nodeId = generateUniqueId('node', label, []);
      return {
        node_id: nodeId,
        label: label,
        status: 'Not Started',
        sections: createDefaultSections()
      };
    });

    // iterate nodes and their corresponding indexes, create a new edge array
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

    /* 
    "..." operator mean spread the element in the array after it (workflows)
    after spreading adding the item or array(newWorkflow) after comma to it and create a new array
    this method does not modify the original array directly, 
    and js will free up memory when original one is not referred anymore
    */
    workflows = [...workflows, newWorkflow];

    emitChange(workflowId, { 
      type: 'create_workflow', 
      data: { 
        name: workflowName, 
        workflow_id: workflowId, 
        is_locked: isWorkflowLocked,
        nodes: newWorkflow.nodes, 
        edges: newWorkflow.edges,
        status: newWorkflow.status,
      } 
    });
  }


  // 2)
  // toggle the status of a node
  function toggleNodeStatus(workflowId: string, nodeId: string) {
    // findIndex is an array method built-in: (for w in workflow) {return w (w.workflow_id = workflowId)}
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1) return;

    /* 
    .map is a built-in array method
        - create new array by calling a provided function (callback function) on every element
        - map() iterate over each node in the original array
        - "() => {}": this is an arrow function, ( parameters ) => { operation } 
        - map to an node -> check the node id in callback -> modify the node status associated with that node_id
        - assign new status -> 
    */
    workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.map((node) => {
      if (node.node_id === nodeId) {
        let newStatus: 'Not Started' | 'In Progress' | 'Completed' | 'Error';
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
          case 'Completed':
            newStatus = 'Not Started';
            break;
        }

        emitChange(workflowId, { 
          type: 'update_node_status',
          data: { 
            workflow_id: workflowId,
            node_id: node.node_id,
            status: newStatus
          } 
        });

        return {...node, status: newStatus};
      }
      return node;
    });
    workflows = [...workflows];
  }


  // 3)
  // lock the workflow, prevent users that don't have authorization to modify
  // not lock = release, so original release function is removed
  function toggleLockStatus(workflowId: string) {
    const workflow = workflows.find(w => w.workflow_id === workflowId);

    if (workflow) {
      const newLockStatus = !workflow.is_locked;
      workflow.is_locked = newLockStatus;
      workflows = [...workflows];

      emitChange(workflowId, { 
        type: 'update_lock_status', 
        data: { 
          workflow_id: workflowId, 
          is_locked: newLockStatus 
        } 
      });
    } else {
      alert("Workflow not found")
      return;
    }
  }


  // 4)
  // adding node to existing workflow array
  function addNode(workflowId: string) {
    // you are dealing with array of workflow, so you always need to find the
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
      alert('Cannot add node. Workflow is locked or not found.');
      return;
    }

    // generate a unique ID for new node you entered (label is the name, and index use to find workflows)
    const newNodeId = generateUniqueId('node', newNodeLabel, workflows[workflowIndex].nodes);
    const newNode: Node = {
      node_id: newNodeId,
      label: newNodeLabel,
      status: 'Not Started',
      sections: createDefaultSections()
    };
      
    // HACK: usually, there would be nodes with the same name in a workflow, so this method don't check with dupliate label name 
    // assuming label are unique in every workflow.
    // it find the previous node solely on the label name entered by user (matching the elements in the array)
    const prevNode = workflows[workflowIndex].nodes.find(node => node.label.toLowerCase() === newNodePrevLabel.toLowerCase());
    // create a copy of current edges data structure, temp array for newly edges updating
    let updatedEdges = [...workflows[workflowIndex].edges];

    if (prevNode) {
      // Connect the new node to the previous node
      updatedEdges.push({ from: prevNode.node_id, to: newNode.node_id });

      // Check if the previous node has any outgoing edges
      // two conditions: 
      // 1) exist "from" property, which has previous node 
      // 2) don't have "to" property == newNode
      // these condition make sure you found a valid place to add node to existing workflow
      const nextEdge = updatedEdges.find(edge => edge.from === prevNode.node_id && edge.to !== newNode.node_id);

      /* 
      if has nextEdge (identify it using previous node, meaning an edge after a previous node)
        FULL LOGIC:
          1) Originally: A -> B 
          2) Imtermediately: A -> B, A -> NewNode (done right after if statement), NewNode -> B
          3) finally: A -> NewNode, NewNode -> B (below line replace the A -> B, break the links directly), maybe it's now how do in C++
      */
      if (nextEdge) {
        nextEdge.from = newNode.node_id;
      }
    } else {
      console.log("Creating a new branch or starting node");
      // No need to add any edges when creating a new branch, also handle the situation when no edge found
    }

    // update nodes, edge, and use ...workflow to trigger reative rendering
    workflows[workflowIndex].nodes = [...workflows[workflowIndex].nodes, newNode];
    workflows[workflowIndex].edges = updatedEdges;
    workflows = [...workflows];

    emitChange(workflowId, { 
      type: 'add_node', 
      data: { 
        workflow_id: workflowId,
        node: newNode,
        edges: updatedEdges
      } 
    });

    // used to have this: unsavedChanges.set(true);
    // because whenever you made changes, you should notify the system 
    // now this is handled inside emitChange(), so you just need to reset the Node and prevNode
    newNodeLabel = '';
    newNodePrevLabel = '';
  }

  // 5) 
  // remove node
  function removeNode(workflowId: string, nodeId: string) {

    // First: again locate the workflow and check it status
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
      alert('Cannot remove node. Workflow is locked or not found.');
      return;
    }

    // Second: located the nodes in the given workflow
    const nodeToRemove = workflows[workflowIndex].nodes.find(node => node.node_id === nodeId);
    if (!nodeToRemove) {
      console.error(`Node with id ${nodeId} not found`);
      return;
    }

    // keep all other nodes that id's do not equal to selected one for removal
    workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.filter(node => node.node_id !== nodeId);
      
    // same logic, keep all the edge without "from" and "to" properties doesn't equal to nodeId (the one intended to remove)
    // A -> B -> C -> D: say if you want to remove C, you exclude edges B -to- C and C -to- D 
    let updatedEdges = workflows[workflowIndex].edges.filter(edge => edge.from !== nodeId && edge.to !== nodeId);

    // find edge's to == C, and edge's from == C, kind of the reverse finding compared to above "updatedEdge" finding
    const incomingEdge = workflows[workflowIndex].edges.find(edge => edge.to === nodeId);
    const outgoingEdge = workflows[workflowIndex].edges.find(edge => edge.from === nodeId);
    if (incomingEdge && outgoingEdge) {
      updatedEdges.push({ from: incomingEdge.from, to: outgoingEdge.to });
    }

    // replace the original set of edge with updateEdges
    workflows[workflowIndex].edges = updatedEdges;
    // trigger reactive
    workflows = [...workflows];

    emitChange(workflowId, { 
      type: 'remove_node', 
      data: { 
        workflow_id: workflowId,
        node_id: nodeToRemove.node_id,
        edges: updatedEdges
      } 
    });
  }


  // 6) given workflowId and nodeId, locate the place for section adding
  function addSection(workflowId: string, nodeId: string) {
    // always, first find the workflow using unique ID
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1 || workflows[workflowIndex].is_locked) {
      alert('Cannot add section. Workflow is locked or not found.');
      return;
    }

    // prevent button clicking if not section label entered
    if (!newSectionLabel) {
      alert('Please enter a section label.');
      return;
    }

    // grab the section label name, and generated unique ID
    const newSectionId = generateUniqueId('section', newSectionLabel.toLowerCase(), []);

    // find the corresponding node
    workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.map(node => {
      if (node.node_id === nodeId) {
        const newSection = {
          section_id: newSectionId,
          label: newSectionLabel,
          files: []
        };

        // update the instruction
        emitChange(workflowId, { 
          type: 'add_section', 
          data: { 
            workflow_id: workflowId,
            node_id: node.node_id,
            section: newSection 
          } 
        });

        return {...node, sections: [...node.sections, newSection]};
      }
      return node;
    });

    workflows = [...workflows];
    addingSectionToNodeId = null;
    newSectionLabel = '';
  }


  // 7)
  // quiet complicate function for updating the files immediately (aside from instruction operation)
  async function uploadFiles(workflowId: string, nodeId: string, sectionId: string, event: Event) {

    // because this function is separated from instructions, it execute the upload directory 
    // so first need to catch the event when user click button to browser files
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) {
      // catch cancel upload behavior, so it won't become alart or error 
      console.error('No files selected');
      return;
    }

    // convert file into array, because we allow multiple files upload at the same time 
    // TODO: later you might need to add check here, for restricting the total file size trying to upload 
    // use helper function, this function is already long and complex
    const files = Array.from(target.files);
    // create form data and workflow_id, node_id, section_id for securing the spot that files are gonna uploaded
    const formData = new FormData();
    formData.append('workflow_id', workflowId);
    formData.append('node_id', nodeId);
    formData.append('section_id', sectionId);


    // create the unique id and key properties for the each file inside the array
    const fileDataArray = files.map(file => ({
      file_id: generateUniqueId('file', file.name, []),
      name: file.name,
      type: file.type,
      size: file.size
    }));


    // when you can upload multiple files to some components, you catch them together 
    // but in the end, you have to send them in form data, which means one by one added to formdata
    // below is doing the one by one adding by loop with key = "files" indicating this is file to send
    files.forEach((file, index) => {
      formData.append('files', file);
    });
    // this is the array of all meta data of the files
    formData.append('file_data', JSON.stringify(fileDataArray));

    try {
      const response = await fetch(API_ENDPOINTS.UPLOAD_FILE, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();

      // basically you upload files to backend, and backend receive files and send response back 
      // you use the workflow_id, node_id, section_id to located the correct section where you loaded files 
      // flitering out unsuccessful file uploads using message received from backend, and reflect to frontend
      workflows = workflows.map(workflow => {
        if (workflow.workflow_id === workflowId) {
          workflow.nodes = workflow.nodes.map(node => {
            if (node.node_id === nodeId) {
              node.sections = node.sections.map(section => {
                if (section.section_id === sectionId) {
                  // r: response, this is a json object received from backend, so { message: string, file_id: string}
                  // to fix type warnings, you have to declare and (r: UploadFileResponse) to surpress, so leave it alone right now
                  const successfulUploads = result.results.filter(r => r.message === "File uploaded successfully");
                  const newFiles = successfulUploads.map(upload => {
                    // same for f
                    const fileData = fileDataArray.find(f => f.file_id === upload.file_id);
                    return fileData ? fileData : null;
                  }).filter(Boolean);
                      
                  // update the section files
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
      alert('Failed to upload files. Please try again later.');
    }
  }


  // trigger eventBus's method, getChangesForWorkflow()
  async function commitChanges(workflowId: string) {
    const changes = eventBus.getChangesForWorkflow(workflowId);
    if (changes.length === 0) {
      console.log('No changes to commit for workflow:', workflowId);
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.WORKFLOW_COMMIT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ changes }),
      });

      if (!response.ok) {
        throw new Error('Failed to commit changes');
      }

      const result = await response.json();
      console.log('Changes committed successfully:', result);

      eventBus.clearChanges(workflowId);
      unsavedChanges.set(false);


      // Update the workflow's status to "saved" whenever changes had made to workflow
      workflows = workflows.map(workflow => 
        workflow.workflow_id === workflowId 
          ? { ...workflow, status: "saved" }
          : workflow
      );


    } catch (error) {
      console.error('Error committing changes:', error);
      alert('Failed to commit changes. Please try again.');
    }
  }

  // ------------------------------------------ Retrieve Workflow Data ------------------------------------------


  async function fetchLockedWorkflows() {
    isLoading = true;
    hasLockedWorkflows = false;
    try {
      const response = await fetch(API_ENDPOINTS.FETCH_LOCKED_WORKFLOW);
      if (!response.ok) {
        throw new Error(`Failed to fetch locked workflows: ${response.status} ${response.statusText}`);
      }
      const lockedWorkflowIds = await response.json();


      // Add half seconds for delay
      await new Promise(resolve => setTimeout(resolve, 500));

      
      if (lockedWorkflowIds.length > 0) {
        hasLockedWorkflows = true;
        for (const id of lockedWorkflowIds) {
          await fetchWorkflow(id);
        }
      }
    } catch (error) {
      console.error('Error fetching locked workflows:', error);
      alert('Failed to fetch locked workflows. Please try again later.');
    } finally {
      isLoading = false;
      initialLoadComplete = true;
    }
  }



  async function fetchWorkflow(id?: string) {
    const workflowIdToFetch = id || workflow_id;
    if (!workflowIdToFetch) {
      alert('Please enter a workflow ID');
      return;
    }

    isLoading = true;  // Set loading state to true
    try {
      const url = constructUrl(API_ENDPOINTS.FETCH_ALL_WORKFLOW, {
        workflow_id: workflowIdToFetch,
      });
      console.log(`Fetching workflow with URL: ${url}`);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch workflow: ${response.status} ${response.statusText}`);
      }

      const workflow = await response.json();
      
      // Add a 1-second delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Fetched workflow:', workflow);

      // guess a unordered json array mixed with section and nodes is received, 
      // so first spreading them into category
      const processedNodes = workflow.nodes.map((node: Node) => ({
        ...node,
        sections: (node.sections || []).map(section => ({
          ...section,
          files: section.files || []
        }))
      }));

      // check if the workflow is display or not
      if (!workflows.some(w => w.workflow_id === workflow.workflow_id)) {
        workflows = [...workflows, {
          workflow_id: workflow.workflow_id,
          name: workflow.name,
          is_locked: workflow.is_locked,
          nodes: sortNodesByEdges(processedNodes, workflow.edges),
          edges: workflow.edges,
          status: workflow.status || 'saved',
        }];
      } else if (!id) {  // Only alert if it's a manual fetch
        alert('This workflow is already displayed.');
      }

      if (!id) {  // Only reset if it's a manual fetch
        workflow_id = '';
      }
    } catch (error) {
      console.error('Error fetching workflow:', error);
      if (!id) {  // Only alert if it's a manual fetch
        alert(`Failed to fetch workflow: ${error.message}`);
      }
    } finally {
      isLoading = false;  // Set loading state to false when done
    }
  }




  // sorting with nodes with dfs based edges
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


  // open routes for download, independent from instructions
  async function downloadFile(workflowId: string, nodeId: string, sectionId: string, fileId: string, fileName: string) {
    const downloadUrl = `${API_ENDPOINTS.DOWNLOAD_FILE}/${workflowId}/${nodeId}/${sectionId}/${fileId}`;
    
    try {
      const response = await fetch(downloadUrl);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('File not found in the specified section');
        }
        throw new Error('Network response was not ok');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download file. Please try again later.');
    }
  }
</script>



<main>

  <h2>Workflow Section</h2>

  {#if isLoading || !initialLoadComplete}
    <Loader message="Loading workflows..." />
  {:else if !hasLockedWorkflows && workflows.length === 0}
    <div class="no-locked-workflows">
      <p>No locked workflows found.</p>
    </div>
  {/if}


  <div class="workflow-input-section">

    <div class="input-button-group">
      <input bind:value={workflowName} placeholder="Give it a name" />
      <button class="icon-button" data-text="new" data-icon="+" on:click={createWorkflow}></button>
    </div>

    <div class="input-button-group">
      <input bind:value={workflow_id} placeholder="Enter workflow ID" />
      <button class="icon-button" data-text="add" data-icon="+" on:click={() => fetchWorkflow()}></button>
    </div>

  </div>


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
              {#if node.status === 'In Progress' && workflow.status !== 'created' }
                <input 
                  type="file" 
                  multiple
                  on:change={(event) => uploadFiles(workflow.workflow_id, node.node_id, section.section_id, event)} 
                  disabled={workflow.is_locked}
                />
              {/if}
              {#if section.files && section.files.length > 0}
                <ul class="list-unstyled">
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
                <input type="text" bind:value={newNodePrevLabel} />
              </label>
            </div>
            <button type="submit">Add Node</button>
          </form>
        </section>
      {/if}

      <button 
        on:click={() => commitChanges(workflow.workflow_id)} 
        disabled={workflow.status === "saved" || eventBus.getChangesForWorkflow(workflow.workflow_id).length === 0}
      >
        {workflow.status === "saved" ? 'Changes Saved' : `Commit Changes for ${workflow.name}`}
      </button>

    </div>
  {/each}
</main>


<style>

  /* if you want to override some global style, just re-define here, it will automatically be done */


  .workflow-input-section {
    display: flex;
    justify-content: space-between;
    gap: 20px; /* Adds space between the two groups */
    width: 100%; /* Ensures the section takes full width */
  }

  .input-button-group {
    display: flex;
    align-items: center;
    flex: 1; /* Makes each group grow equally */
  }

  .input-button-group input {
    flex-grow: 1;
    height: 40px;
    padding: 0 12px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 14px;
    margin-right: 10px;
  }


  /* Unified styles for icon buttons with spinning effect */
  .icon-button {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background-color: #ffffff;
    color: #333333;
    font-size: 13px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin: 0 10px;
    position: relative;
    overflow: hidden;
  }

  .icon-button:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }

  .icon-button:active {
    background-color: rgba(0, 0, 0, 0.1);
  }

  .icon-button::before,
  .icon-button::after {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    transition: all 0.3s ease;
  }

  .icon-button::before {
    content: attr(data-text);
  }

  .icon-button::after {
    content: attr(data-icon);
    font-size: 24px;
    opacity: 0;
  }

  .icon-button:hover::before {
    opacity: 0;
    transform: translate(-50%, -50%) translateY(20px);
  }

  .icon-button:hover::after {
    opacity: 1;
    transform: translate(-50%, -50%) rotate(90deg);
  }

  
</style>
