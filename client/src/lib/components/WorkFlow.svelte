<script lang="ts">
  import { onMount } from 'svelte';
  import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';
  import Pipeline from './Pipeline.svelte';
  import type { Workflow, Node, Edge, Section, Change } from '$lib/types';
  import { unsavedChanges } from '$lib/utils/vars';
  import { eventBus } from '$lib/utils/eventBus';
  import { WORKFLOW_CHANGE_EVENT } from '$lib/utils/vars'

  // ----------------------------------------------------- Variable Declaration -----------------------------------------------------
  let workflows: Workflow[] = [];
  let workflowName = '';
  let workflow_id = '';
  let isWorkflowLocked = false;
  let newNodeLabel = '';
  let newNodePrevLabel = '';
  let newSectionLabel = '';
  let addingSectionToNodeId: string | null = null;


  // New variables for loading state and locked workflows
  let isLoading = false;
  let hasLockedWorkflows = false;

  // ----------------------------------------------------- Frontend Interaction Function -----------------------------------------------------

  function handleNodeClick(event: CustomEvent<string>) {
    const nodeId = event.detail;
    const sectionElement = document.getElementById(nodeId);
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth' });
    }
  }

  function getNodeStatus(node: Node): 'Completed' | 'In Progress' | 'Not Started' | 'Error' {
    return node.status;
  }

  function startAddingSection(nodeId: string) {
    addingSectionToNodeId = nodeId;
    newSectionLabel = '';
  }

  function cancelAddingSection() {
    addingSectionToNodeId = null;
    newSectionLabel = '';
  }

  // ----------------------------------------------------- State Status Management eventBus -----------------------------------------------------


  onMount(() => {
    eventBus.on(WORKFLOW_CHANGE_EVENT, ({ workflowId, change }) => {
      console.log(`Change in workflow ${workflowId}:`, change);
    });
    fetchLockedWorkflows();
  });




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

  function generateUniqueId(obj_type: 'workflow' | 'node' | 'section' | 'file', label: string, existingItems: any[]): string {
    const prefix = { 'workflow': 'wf-', 'node': 'node-', 'section': 'section-', 'file': 'file-' }[obj_type];
    const baseId = `${prefix}${label.toLowerCase().replace(/\s+/g, '_')}`;
    let uniqueId = baseId;
    let counter = 1;

    while (existingItems.some(item => 
      item.id === uniqueId || 
      item.workflow_id === uniqueId || 
      item.node_id === uniqueId || 
      item.section_id === uniqueId
    )) {
      uniqueId = `${baseId}-${counter}`;
      counter++;
    }

    return `${uniqueId}-${Date.now()}`;
  }

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

  function createWorkflow() {
    if (!workflowName) {
      alert('Please enter a workflow name');
      return;
    }
    
    const workflowId = generateUniqueId('workflow', workflowName, workflows);

    const newNodes = ['Sampling', 'Production', 'Delivery', 'Payment'].map(label => {
      const nodeId = generateUniqueId('node', label, []);
      return {
        node_id: nodeId,
        label: label,
        status: 'Not Started',
        sections: createDefaultSections()
      };
    });

    const newEdges = newNodes.slice(0, -1).map((node, index) => ({
      from: node.node_id,
      to: newNodes[index + 1].node_id
    }));

    const newWorkflow: Workflow = { 
      workflow_id: workflowId, 
      name: workflowName, 
      is_locked: isWorkflowLocked,
      nodes: newNodes,
      edges: newEdges,
      status: 'created',
    };

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

  function toggleNodeStatus(workflowId: string, nodeId: string) {
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1) return;

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
      
    const prevNode = workflows[workflowIndex].nodes.find(node => node.label.toLowerCase() === newNodePrevLabel.toLowerCase());
    let updatedEdges = [...workflows[workflowIndex].edges];

    if (prevNode) {
      updatedEdges.push({ from: prevNode.node_id, to: newNode.node_id });
      const nextEdge = updatedEdges.find(edge => edge.from === prevNode.node_id && edge.to !== newNode.node_id);
      if (nextEdge) {
        nextEdge.from = newNode.node_id;
      }
    } else {
      console.log("Creating a new branch or starting node");
    }

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

    newNodeLabel = '';
    newNodePrevLabel = '';
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

    emitChange(workflowId, { 
      type: 'remove_node', 
      data: { 
        workflow_id: workflowId,
        node_id: nodeToRemove.node_id,
        edges: updatedEdges
      } 
    });
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

    const newSectionId = generateUniqueId('section', newSectionLabel.toLowerCase(), []);

    workflows[workflowIndex].nodes = workflows[workflowIndex].nodes.map(node => {
      if (node.node_id === nodeId) {
        const newSection = {
          section_id: newSectionId,
          label: newSectionLabel,
          files: []
        };

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

  async function uploadFiles(workflowId: string, nodeId: string, sectionId: string, event: Event) {
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
      const response = await fetch(API_ENDPOINTS.UPLOAD_FILE, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      workflows = workflows.map(workflow => {
        if (workflow.workflow_id === workflowId) {
          workflow.nodes = workflow.nodes.map(node => {
            if (node.node_id === nodeId) {
              node.sections = node.sections.map(section => {
                if (section.section_id === sectionId) {
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
      alert('Failed to upload files. Please try again later.');
    }
  }

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


      // Update the workflow's status to "saved"
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


      // Add a 1-second delay
      // await new Promise(resolve => setTimeout(resolve, 500));

      
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

      const processedNodes = workflow.nodes.map((node: Node) => ({
        ...node,
        sections: (node.sections || []).map(section => ({
          ...section,
          files: section.files || []
        }))
      }));

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

  {#if isLoading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading workflows...</p>
    </div>
  {:else if !hasLockedWorkflows && workflows.length === 0}
    <div class="no-locked-workflows">
      <p>No locked workflows found.</p>
    </div>
  {/if}


  <div>
    <input bind:value={workflow_id} placeholder="Enter workflow ID to fetch" />
    <button on:click={() => fetchWorkflow()}>Add Workflow</button>
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
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .loading {
    text-align: center;
    padding: 20px;
    font-size: 18px;
    color: #666;
  }

  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
  }
</style>
