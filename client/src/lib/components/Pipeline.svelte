
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { Node, Edge, Workflow } from '$lib//types';

    export let activeWorkflow: Workflow | null = null;
    export let nodes: Node[] = [];
    export let edges: Edge[] = [];
    console.log('Received edges in Pipeline:', edges); // Add this line

    const dispatch = createEventDispatcher();

    function handleClick(node: Node) {
      dispatch('nodeClick', node.node_id);
    }

    function getNodeColor(node: Node): string {
      switch (node.status) {
        case 'Completed':
          return '#4CAF50'; // Green for completed
        case 'In Progress':
          return '#FFC107'; // Amber for in-progress
        case 'Error':
          return '#FF0000'; // Amber for in-progress
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

<style>
  .pipeline {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    overflow-x: auto;
    padding: 20px;
  }
  .path {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    min-width: max-content;
  }
  .node-container {
    display: flex;
    align-items: center;
    position: relative;
  }
  .node {
    padding: 10px;
    border: 1px solid black;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 20px;
    transition: all 0.3s ease;
    min-width: 100px;
    height: 40px;
    z-index: 1;
  }
  .node:hover {
    opacity: 0.8;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
  .edge {
    position: absolute;
    top: 50%;
    right: -20px;
    width: 40px;
    height: 2px;
    background-color: #000;
    z-index: 0;
  }
  .edge::after {
    content: '';
    position: absolute;
    right: 0;
    top: -4px;
    width: 0;
    height: 0;
    border-left: 8px solid #000;
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
  }
</style>

<div class="pipeline">
  {#if activeNodes.length > 0}
    {#each connectedNodes as path}
      <div class="path">
        {#each path as node, index}
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
