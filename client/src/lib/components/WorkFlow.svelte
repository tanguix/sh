

<script lang="ts">
  import { fade } from 'svelte/transition';
  import { onMount, afterUpdate } from 'svelte';
  import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';
  import type { Workflow, Node, Edge, Section, Change } from '$lib/types';
  import { unsavedChanges } from '$lib/utils/vars';
  import { eventBus } from '$lib/utils/eventBus';
  import { WORKFLOW_CHANGE_EVENT } from '$lib/utils/vars'
  // component 
  import Pipeline from './Pipeline.svelte';
  import Loader from '$lib/components/css/Loader.svelte';

  // New prop to receive user information
  export let user: { name: string; role: string } | null;

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

  // Set your fade duration here (in milliseconds)
  const fadeDuration = 700;

  // ----------------------------------------------------- Frontend Interaction Function -----------------------------------------------------

  function handleNodeClick(event: CustomEvent<string>) {
    const nodeId = event.detail;
    const sectionElement = document.getElementById(nodeId);
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth' });
    }
  }

  function getNodeStatus(node: Node): 'Sleep' | 'Active' | 'Completed' | 'Error' {
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
      console.log('Please enter a workflow name:');
      return;
    }
    
    if (!user) {
      console.log('User information is not available');
      return;
    }

    const workflowId = generateUniqueId('workflow', workflowName, workflows);

    const newNodes = ['Sampling', 'Production', 'Delivery', 'Payment'].map(label => {
      const nodeId = generateUniqueId('node', label, []);
      return {
        node_id: nodeId,
        label: label,
        status: 'Sleep',
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
      owner: [user.name, user.role],  // Include owner information
      timestamp: Date.now(),
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
        owner: [user.name, user.role],  // Include owner information in the emitted change
        timestamp: newWorkflow.timestamp
      } 
    });
  }






  function toggleNodeStatus(workflowId: string, nodeId: string) {
    const workflowIndex = workflows.findIndex(w => w.workflow_id === workflowId);
    if (workflowIndex === -1) return;

    workflows = workflows.map((workflow, index) => {
      if (index === workflowIndex) {
        return {
          ...workflow,
          nodes: workflow.nodes.map((node) => {
            if (node.node_id === nodeId) {
              let newStatus: 'Sleep' | 'Active' | 'Completed' | 'Error';
              switch (node.status) {
                case 'Sleep': newStatus = 'Active'; break;
                case 'Active': newStatus = 'Error'; break;
                case 'Error': newStatus = 'Completed'; break;
                case 'Completed': newStatus = 'Sleep'; break;
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
          })
        };
      }
      return workflow;
    });
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
      status: 'Sleep',
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

    workflows = workflows.map(workflow => {
      if (workflow.workflow_id === workflowId) {
        return {
          ...workflow,
          nodes: workflow.nodes.map(node => {
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

              return {
                ...node,
                sections: [...node.sections, newSection]
              };
            }
            return node;
          })
        };
      }
      return workflow;
    });

    addingSectionToNodeId = null;
    newSectionLabel = '';
  }

  function handleFileSelect(event: any, sectionId: any) {
    const input = event.target;
    const fileName = input.files.length > 0 
      ? input.files.length > 1 
        ? `${input.files.length} files selected` 
        : input.files[0].name
      : "No file chosen";
    const fileNameElement = document.querySelector(`#file-upload-${sectionId} + label + .file-name`);
    if (fileNameElement) {
      fileNameElement.textContent = fileName;
    }
  }

  async function uploadFiles(workflowId: string, nodeId: string, sectionId: string, event: Event) {

    handleFileSelect(event, sectionId);

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

  async function fetchLockedWorkflows() {
    isLoading = true;
    hasLockedWorkflows = false;
    try {
      const response = await fetch(API_ENDPOINTS.FETCH_LOCKED_WORKFLOW);
      if (!response.ok) {
        throw new Error(`Failed to fetch locked workflows: ${response.status} ${response.statusText}`);
      }
      const lockedWorkflowIds = await response.json();

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
      console.log('Please enter a workflow ID:');
      return;
    }

    isLoading = true;
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
          owner: workflow.owner || [],
          timestamp: workflow.timestamp || Date.now()  // Add this line
        }].sort((a, b) => a.timestamp - b.timestamp);
      } else if (!id) {
        alert('This workflow is already displayed.');
      }

      if (!id) {
        workflow_id = '';
      }
    } catch (error) {
      console.error('Error fetching workflow:', error);
      if (!id) {
        alert(`Failed to fetch workflow: ${error.message}`);
      }
    } finally {
      isLoading = false;
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

      const contentType = response.headers.get('content-type');

      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);

      window.open(url, '_blank');

      setTimeout(() => window.URL.revokeObjectURL(url), 100);

    } catch (error) {
      console.error('Preview failed:', error);
      alert('Failed to preview file. Please try again later.');
    }
  }

  $: isWorkflowNameValid = workflowName.trim() !== '';
  $: isWorkflowIdValid = workflow_id.trim() !== '';

  function handleCreateWorkflow() {
    if (isWorkflowNameValid) {
      createWorkflow();
    }
  }

  function handleFetchWorkflow() {
    if (isWorkflowIdValid) {
      fetchWorkflow();
    }
  }
</script>



<main>
  <div class="workflow-container">
    <h2>Workflow Section</h2>

    {#if isLoading || !initialLoadComplete}
      <div transition:fade="{{ duration: fadeDuration }}">
        <Loader message="Loading workflows..." />
      </div>
    {:else}
      <div transition:fade="{{ duration: fadeDuration }}">
        <div class="workflow-input-section">
          <div class="input-button-group">
            <input 
              bind:value={workflowName} 
              placeholder="Give it a name" 
              required
              class:invalid={!isWorkflowNameValid && workflowName.length > 0}
            />
            <button 
              class="icon-button" 
              data-text="new" 
              data-icon="+" 
              on:click={handleCreateWorkflow}
              disabled={!isWorkflowNameValid}
            ></button>
          </div>
          <div class="input-button-group">
            <input 
              bind:value={workflow_id} 
              placeholder="Enter workflow ID" 
              required
              class:invalid={!isWorkflowIdValid && workflow_id.length > 0}
            />
            <button 
              class="icon-button" 
              data-text="add" 
              data-icon="+" 
              on:click={handleFetchWorkflow}
              disabled={!isWorkflowIdValid}
            ></button>
          </div>
        </div>

        {#if !hasLockedWorkflows && workflows.length === 0}
          <div class="no-locked-workflows">
            <p>No workflows found. Create a new workflow or add an existing one using the options above.</p>
          </div>
        {:else}
          {#each workflows as workflow (workflow.workflow_id)}
            <hr class="workflow-separator">
            <div class="workflow">
              <div class="workflow-header">
                <div class="workflow-title-container">
                  <h2>{workflow.name}</h2>
                  {#if workflow.owner && workflow.owner[0]}
                    <span class="owner-info">(&nbsp;{workflow.owner[0]}:</span>
                  {/if}
                  <span class="timestamp-info">{new Date(workflow.timestamp).toLocaleString()}&nbsp;)</span>
                </div>
                <button class="toggle-lock-button" on:click={() => toggleLockStatus(workflow.workflow_id)}>
                  {workflow.is_locked ? 'Release' : 'Lock'}
                </button>
              </div>

              <Pipeline nodes={workflow.nodes} edges={workflow.edges} on:nodeClick={handleNodeClick} />


              <div class="nodes-grid">
                {#each sortNodesByEdges(workflow.nodes, workflow.edges) as node}
                  <section id={node.node_id} class="node-card">
                    <div class="node-header">
                      <h3>{node.label}</h3>
                      <button on:click={() => toggleNodeStatus(workflow.workflow_id, node.node_id)} disabled={workflow.is_locked}>
                        {getNodeStatus(node)}
                      </button>
                    </div>

                    {#each node.sections as section}
                      <div>
                        <h4>{section.label}</h4>
                        {#if node.status === 'Active' && workflow.status !== 'created' }
                          <div class="file-upload">
                            <input 
                              type="file" 
                              id="file-upload-{section.section_id}"
                              multiple
                              on:change={(event) => uploadFiles(workflow.workflow_id, node.node_id, section.section_id, event)} 
                              disabled={workflow.is_locked}
                              class="file-input"
                            />
                            <label for="file-upload-{section.section_id}" class="file-input-label">Browse Files</label>
                            <span class="file-name">No File Selected</span>
                          </div>
                        {/if}

                        {#if section.files && section.files.length > 0}
                          <ul class="file-list">
                            {#each section.files as file}
                              <li class="file-list-item">
                                <p class="file-name">{file.name}</p>
                                <button class="download-button" on:click={() => downloadFile(
                                  workflow.workflow_id, 
                                  node.node_id, 
                                  section.section_id, 
                                  file.file_id, 
                                  file.name
                                )}>
                                  预览
                                </button>
                              </li>
                            {/each}
                          </ul>
                        {/if}
                      </div>
                    {/each}

                    <div class="node-actions">
                      {#if addingSectionToNodeId === node.node_id}
                        <form on:submit|preventDefault={() => addSection(workflow.workflow_id, node.node_id)} class="add-section-form">
                          <input 
                            type="text" 
                            bind:value={newSectionLabel} 
                            placeholder="Enter section label"
                            required
                          />
                          <button type="submit" class="confirm-section-button" disabled={workflow.is_locked}>Add</button>
                          <button type="button" class="cancel-section-button" on:click={cancelAddingSection}>Cancel</button>
                        </form>
                      {/if}
                      <div class="node-action-buttons">
                        <button class="add-section-button" on:click={() => startAddingSection(node.node_id)} disabled={workflow.is_locked}>+ section</button>
                        <button class="remove-node-button" on:click={() => removeNode(workflow.workflow_id, node.node_id)} disabled={workflow.is_locked}>
                          - node
                        </button>
                      </div>
                    </div>
                  </section>
                {/each}
              </div>

              {#if !workflow.is_locked}
                <section>
                  <h3>Add New Node</h3>
                  <form on:submit|preventDefault={() => addNode(workflow.workflow_id)}>
                    <div class="node-adding-section">
                      <div>
                        <label>
                          <input type="text" bind:value={newNodeLabel} placeholder="Node Label:" required />
                        </label>
                      </div>
                      <div>
                        <label>
                          <input type="text" bind:value={newNodePrevLabel} placeholder="Previous Node:"/>
                        </label>
                      </div>
                    </div>
                    <button type="submit">Add Node</button>
                  </form>
                </section>
              {/if}

              <button 
                on:click={() => commitChanges(workflow.workflow_id)} 
                disabled={workflow.status === "saved" || eventBus.getChangesForWorkflow(workflow.workflow_id).length === 0}
              >
                {workflow.status === "saved" ? 'Changes Saved' : `Commit for ${workflow.name}`}
              </button>
            </div>
          {/each}
        {/if}
      </div>
    {/if}
  </div>
</main>





<style>


  .workflow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0 1rem 0;
  }

  .workflow-title-container {
    display: flex;
    align-items: center; /* Changed from baseline to center */
  }

  .workflow-title-container h2 {
    margin: 0;
    margin-right: 10px;
  }


  .owner-info {
    font-family: "Ubuntu";
    font-size: 0.8rem;
    color: #666;
    line-height: 1; /* Ensure single line height */
    display: inline-block; /* Helps with alignment */
    vertical-align: middle; /* Aligns with the middle of the text */
  }


  .timestamp-info {
    font-family: "Ubuntu";
    font-size: 0.8rem;
    color: #666;
    margin-left: 10px;
  }


  .workflow-container {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
  }

  .workflow-separator {
    margin: 1rem 0 2rem 0;
    border: none;
    border-top: 1px solid #e0e0e0;
  }

  .workflow-input-section {
    display: flex;
    justify-content: space-between;
    gap: 40px;
    width: 100%;
    padding: 10px;
    background-color: #f9f9f9;
    border-radius: 10px;
    box-sizing: border-box;
    margin-top: 20px;
  }

  .workflow {
    margin-bottom: 2rem;
  }

  .workflow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0 1rem 0;
  }

  .toggle-lock-button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    background-color: #f0f0f0;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .toggle-lock-button:hover {
    background-color: #e0e0e0;
  }

  .node-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    border-bottom: solid #e0e0e0;
    padding: 4px 0 5px 0;
  }

  .node-header h3 {
    margin: 0;
    flex-grow: 1;
  }

  .node-header button {
    padding: 0.5rem 1rem;
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .node-header button:hover {
    background-color: #e0e0e0;
  }

  .node-header button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .nodes-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1rem;
  }

  .node-card {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 1rem;
    background-color: #f9f9f9;
    min-width: 230px;
  }

  .node-actions {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .add-section-form .confirm-section-button,
  .add-section-form .cancel-section-button {
    background-color: #e0e0e0;
    color: #333;
    border: none;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 12px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.3s;
  }

  .add-section-form .confirm-section-button:hover,
  .add-section-form .cancel-section-button:hover {
    background-color: #d0d0d0;
  }

  .add-section-form .confirm-section-button:disabled {
    background-color: #cccccc;
    color: #666666;
    cursor: not-allowed;
  }

  .node-action-buttons {
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
    gap: 0.5rem;
  }

  .node-action-buttons button {
    padding: 0.5rem 1rem;
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    font-size: 12px;
  }

  .node-action-buttons button:hover {
    background-color: #e0e0e0;
  }

  .node-action-buttons button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .add-section-button {
    background-color: #ffebee;
    color: var(--color-hyperlink);
  }

  .add-section-button:hover {
    background-color: #ffcdd2;
  }

  .remove-node-button {
    background-color: #ffebee;
    color: #c62828;
  }

  .remove-node-button:hover {
    background-color: #ffcdd2;
  }

  .add-section-form {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .add-section-form input {
    padding: 0.5rem;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 12px;
    flex-grow: 1;
  }

  .add-section-form button {
    padding: 0.5rem 1rem;
    font-size: 12px;
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .add-section-form button:hover {
    background-color: #e0e0e0;
  }

  .add-section-form button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .input-button-group {
    display: flex;
    align-items: center;
    flex: 1;
    gap: 10px;
  }

  .input-button-group input {
    flex-grow: 1;
    height: 40px;
    padding: 0 12px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.3s ease;
  }

  .input-button-group input:focus {
    outline: none;
    border-color: #4CAF50;
  }

  .input-button-group input.invalid {
    border-color: #f44336;
  }

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

  .icon-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .file-upload {
    margin: 10px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f0f0f0;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px;
    text-align: center;
  }

  .file-input {
    display: none;
  }

  .file-input-label {
    font-family: "Ubuntu";
    font-size: 12px;
    padding: 8px 12px;
    background-color: #e0e0e0;
    color: #333;
    cursor: pointer;
    transition: background-color 0.3s;
    border-radius: 4px;
    margin-right: 8px;
  }

  .file-input-label:hover {
    background-color: #d0d0d0;
  }

  .file-upload:has(.file-input:disabled) {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .file-upload:has(.file-input:disabled) .file-input-label {
    pointer-events: none;
  }

  .file-list {
    list-style-type: none;
    padding: 0;
    margin: 8px 0;
  }

  .file-list-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2px;
    padding: 2px 8px;
    background-color: #f9f9f9;
    border-radius: 4px;
  }

  .file-name {
    font-family: "Ubuntu";
    flex-grow: 1;
    margin-right: 8px;
    font-size: 12px;
    color: #333;
  }

  button.download-button {
    padding: 4px 8px;
    background-color: #f0f0f0;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    cursor: pointer;
    font-family: Arial, sans-serif;
    font-size: 12px;
    transition: background-color 0.3s;
  }

  button.download-button:hover {
    background-color: #e0e0e0;
  }

  .node-adding-section {
    display: flex;
    justify-content: space-between;
    gap: 40px; /* Adjust this value to increase or decrease the gap */
    width: 100%; /* Ensure the main div takes full width of its container */

  }

  .node-adding-section > div {
    flex: 1; /* This makes both child divs grow equally */
  }

</style>
