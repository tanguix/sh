
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { Node, Edge, Workflow } from '$lib/types';

    export let activeWorkflow: Workflow | null = null;
    export let nodes: Node[] = [];
    export let edges: Edge[] = [];

    // checking nodes
    // console.log('Received edges in Pipeline:', edges);

    const dispatch = createEventDispatcher();

    function handleClick(node: Node) {
      dispatch('nodeClick', node.node_id);
    }

    function getNodeColor(node: Node): string {
      switch (node.status) {
        case 'Completed':
          // return '#00FF7F'; // Green for completed
          return '#33fae8'; // Green for completed, TODO: change better one
        case 'Active':
          return '#FFDE95'; // Amber for in-progress TODO: change better one
          // return '#b1e4fe'; // Amber for in-progress
        case 'Error':
          return '#f88'; // red for problem
        // case 'Not Started':
        default:
          return '#9E9E9E'; // Grey for not started
      }
    }

    function getConnectedNodes(nodeList: Node[], edgeList: Edge[]) {
      const connectedNodes: Node[][] = [];
      const visited = new Set<string>();

      function dfs(nodeId: string, path: Node[]) {
        visited.add(nodeId);
        const node = nodeList.find(n => n.node_id === nodeId);
        if (node) {
          path.push(node);
          const outgoingEdges = edgeList.filter(e => e.from === nodeId);
          if (outgoingEdges.length === 0) {
            connectedNodes.push([...path]);
          } else {
            for (const edge of outgoingEdges) {
              if (!visited.has(edge.to)) {
                dfs(edge.to, [...path]);
              }
            }
          }
        }
      }

      // Find start nodes (nodes with no incoming edges)
      const startNodes = nodeList.filter(node => 
        !edgeList.some(edge => edge.to === node.node_id)
      );

      for (const startNode of startNodes) {
        if (!visited.has(startNode.node_id)) {
          dfs(startNode.node_id, []);
        }
      }

      return connectedNodes;
    }

    $: activeNodes = activeWorkflow ? activeWorkflow.nodes : nodes;
    $: activeEdges = activeWorkflow ? activeWorkflow.edges : edges;
    $: connectedNodes = getConnectedNodes(activeNodes, activeEdges);

    // Debug logging
    $: {
        console.log('Active Nodes:', activeNodes);
        console.log('Active Edges:', activeEdges);
        console.log('Connected Nodes:', connectedNodes);
    }

</script>


<div class="pipeline-container">
  <div class="pipeline">
    {#if activeNodes.length > 0}
      {#each connectedNodes as path}
        <div class="path">
          {#each path as node, index (node.node_id)}
            <div class="node-container">
              <button
                type="button"
                class="node"
                on:click={() => handleClick(node)}
                style="background-color: {getNodeColor(node)};"
              >
                {node.label}
              </button>
              {#if index < path.length - 1}
                <div class="edge"></div>
              {/if}
            </div>
          {/each}
        </div>
      {/each}
    {:else}
      <p>No nodes to display.</p>
    {/if}
  </div>
</div>

<style>
  .pipeline-container {
    display: flex;
    justify-content: center;
    width: 100%;
    padding: 20px;
    box-sizing: border-box;
  }

  .pipeline {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    overflow-x: auto;
    max-width: 100%;
  }

  .path {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    flex-shrink: 0;
  }

  .node-container {
    display: flex;
    align-items: center;
    position: relative;
    padding: 3px 0;
  }


  .node {
    font-family: "Ubuntu";
    padding: 10px 12px;
    border: solid 1px #3E3859;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
    min-width: 112px;
    height: 52px;
    margin: 0;
    z-index: 1;
    font-weight: 500;
    font-size: 14px;
    letter-spacing: 0.5px;
    color: #000000;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    position: relative;
    overflow: hidden;
  }

  .node::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .node:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .node:hover::before {
    opacity: 1;
  }

  .node:active {
    transform: translateY(1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .edge {
    width: 40px;
    height: 3px; /* Increased thickness for better visibility */
    background: linear-gradient(to right, rgba(0,0,0,0.1), rgba(0,0,0,0.3));
    position: relative;
    z-index: 0;
    margin: 0 -1px;
  }

  .edge::after {
    content: '';
    position: absolute;
    right: 0px; /* Slightly adjust to right overlap with the next node */
    top: 50%;   /* Center vertically */
    transform: translateY(-50%);  /* Ensure perfect centering */
    width: 0;
    height: 0;
    border-left: 10px solid rgba(0,0,0,0.3);  /* Increased size */
    border-top: 7px solid transparent;        /* Increased size */
    border-bottom: 7px solid transparent;     /* Increased size */
  }


</style>

