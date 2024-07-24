

<script lang="ts">
  import { page } from '$app/stores';
  import { writable, derived, get } from 'svelte/store';
  import { API_ENDPOINTS } from '../utils/api';

  let exchangeRate = writable(false);
  let workflowToken = writable(false);
  let sampleToken = writable(false);

  // Exchange rate related stores
  let exchange_rate = writable(null);
  let error = writable('');


  const toggleExchangeRate = async () => {
    exchangeRate.update(n => !n);
    if (get(exchangeRate) && !get(exchange_rate)) {
      await fetchExchangeRate();
    }
  };

  
  function formatTimestamp(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  }

  

  async function fetchExchangeRate() {
    try {
      const response = await fetch(API_ENDPOINTS.EXCHANGE_RATE);
      if (!response.ok) {
        throw new Error('Failed to fetch exchange rates');
      }
      const data = await response.json();
      exchange_rate.set(data);
    } catch (err) {
      error.set(err.message);
    }
  }


  // Workflow token related stores
  const fetchedWorkflowTokens = writable([]);
  let workflowWho = writable('');
  let workflowFetched = writable(false);


  const toggleWorkflowToken = () => {
    workflowToken.update(n => !n);
    if (get(workflowToken) && !get(workflowFetched)) {
      fetchWorkflowTokens();
    }
  };


  async function fetchWorkflowTokens() {
    const user = get(page).data.user;
    if (!user) {
      console.log("User not defined");
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.FETCH_WORKFLOW_TOKEN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: user.name, role: user.role })
      });

      if (!response.ok) throw new Error('Failed to fetch workflow tokens');

      const result = await response.json();
      fetchedWorkflowTokens.set(result.workflow_tokens);
      workflowFetched.set(true);
      workflowWho.set(result.username === user.name ? 'you' : result.username);
    } catch (error) {
      console.error("Error fetching workflow tokens:", error);
    }
  }





  const latestWorkflowTokens = derived(fetchedWorkflowTokens, $tokens => $tokens.slice(0, 9));
  const hasMoreWorkflowTokens = derived(fetchedWorkflowTokens, $tokens => $tokens.length > 9);



  // Sample token related stores
  const fetchedSampleTokens = writable([]);
  let who = writable('');
  let fetched = writable(false);



  const toggleSampleToken = () => {
    sampleToken.update(n => !n);
    if (get(sampleToken) && !get(fetched)) {
      fetchSampleTokens();
    }
  };


  async function fetchSampleTokens() {
    const user = get(page).data.user;
    if (!user) {
      console.log("User not defined");
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.FETCH_SAMPLE_TOKEN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: user.name, role: user.role })
      });

      if (!response.ok) throw new Error('Failed to fetch sample tokens');

      const result = await response.json();
      fetchedSampleTokens.set(result.sample_tokens);
      fetched.set(true);
      who.set(result.username === user.name ? 'you' : result.username);
    } catch (error) {
      console.error("Error fetching sample tokens:", error);
    }
  }


  // here you set the number of display tokens limit
  const latestTokens = derived(fetchedSampleTokens, $tokens => $tokens.slice(0, 9));
  const hasMoreTokens = derived(fetchedSampleTokens, $tokens => $tokens.length > 9);



  // New stores for category and tag search
  let categoryTagSearch = writable(false);
  let categories = writable([]);
  let tags = writable([]);
  let categoriesTagsFetched = writable(false);


  const toggleCategoryTagSearch = () => {
    categoryTagSearch.update(n => !n);
    if (get(categoryTagSearch) && !get(categoriesTagsFetched)) {
      fetchCategoriesAndTags();
    }
  };

  async function fetchCategoriesAndTags() {
    try {
      const response = await fetch(API_ENDPOINTS.FETCH_CATEGORIES_AND_TAGS);
      if (!response.ok) throw new Error('Failed to fetch categories and tags');

      const result = await response.json();
      categories.set(result.categories);
      tags.set(result.tags);
      categoriesTagsFetched.set(true);
    } catch (error) {
      console.error("Error fetching categories and tags:", error);
    }
  }

  // Limit display to 3 items for each
  const displayedCategories = derived(categories, $cats => $cats.slice(0, 3));
  const displayedTags = derived(tags, $t => $t.slice(0, 3));


</script>




{#if $page.data.user}
  <div class="user-window">
    <h2>Dashboard</h2>
    <p>Welcome, {$page.data.user.name}!</p>
    
    <div class="section">
      <button on:click={toggleExchangeRate}>
        <span class="toggle-text" class:hide={$exchangeRate} class:show={!$exchangeRate}>
          {$exchangeRate ? 'Hide' : 'Show'}
        </span>
        Exchange Rate
      </button>
      <div class="section-content" class:open={$exchangeRate}>
        <h3>Exchange Rates</h3>
        {#if $exchange_rate}
          <div class="ex-card">
            <h4>Date: {$exchange_rate.date}</h4>
            <h4>Time: {formatTimestamp($exchange_rate.timestamp)}</h4>
            <h4>Base Currency: {$exchange_rate.base}</h4>
          </div>
          {#each Object.entries($exchange_rate.rates) as [currency, rate]}
            <div class="ex-card"><h3>{currency}: {rate}</h3></div>
          {/each}
        {:else if $error}
          <p>{$error}</p>
        {:else}
          <p>Loading exchange rates...</p>
        {/if}
      </div>
    </div>

    <div class="section">
      <button on:click={toggleWorkflowToken}>
        <span class="toggle-text" class:hide={$workflowToken} class:show={!$workflowToken}>
          {$workflowToken ? 'Hide' : 'Show'}
        </span>
        Workflow Tokens
      </button>
      <div class="section-content" class:open={$workflowToken}>
        <h3>Workflow Tokens</h3>
        <ul>
          {#if $hasMoreWorkflowTokens}<li>...</li>{/if}
          {#each $latestWorkflowTokens as token, index}
            <li><p>{$workflowWho}: {token}</p></li>
            {#if index === $latestWorkflowTokens.length - 1}
              <p>(latest)</p>
            {/if}
          {/each}
        </ul>
      </div>
    </div>

    <div class="section">
      <button on:click={toggleSampleToken}>
        <span class="toggle-text" class:hide={$sampleToken} class:show={!$sampleToken}>
          {$sampleToken ? 'Hide' : 'Show'}
        </span>
        Sample Tokens
      </button>
      <div class="section-content" class:open={$sampleToken}>
        <h3>Sample Tokens</h3>
        <ul>
          {#if $hasMoreTokens}<li>...</li>{/if}
          {#each $latestTokens as token, index}
            <li><p>{$who}: {token}</p></li>
            {#if index === $latestTokens.length - 1}
              <p>(latest)</p>
            {/if}
          {/each}
        </ul>
      </div>
    </div>

    <div class="section">
      <button on:click={toggleCategoryTagSearch}>
        <span class="toggle-text" class:hide={$categoryTagSearch} class:show={!$categoryTagSearch}>
          {$categoryTagSearch ? 'Hide' : 'Show'}
        </span>
        Category and Tag Search
      </button>
      <div class="section-content" class:open={$categoryTagSearch}>
        <div class="search-options">
          <div class="option-group">
            <h4>Categories:</h4>
            <ul>
              {#each $displayedCategories as category}
                <li>{category}</li>
              {/each}
              {#if $categories.length > 5}
                <li>...</li>
              {/if}
            </ul>
          </div>
          <div class="option-group">
            <h4>Tags:</h4>
            <ul>
              {#each $displayedTags as tag}
                <li>{tag}</li>
              {/each}
              {#if $tags.length > 5}
                <li>...</li>
              {/if}
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="user-window">
    <p>Please log in to view your dashboard.</p>
  </div>
{/if}

<style>
  .user-window {
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    background-color: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    box-sizing: border-box;
  }

  .section {
    width: 100%;
    margin-bottom: 15px;
  }

  .section-content {
    width: 100%;
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transform: translateY(-10px);
    transition: 
      max-height 0.3s cubic-bezier(0, 1, 0, 1),
      opacity 0.3s ease,
      transform 0.3s ease,
      padding 0.3s ease;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-top: none;
    border-radius: 0 0 4px 4px;
    box-sizing: border-box;
  }

  .section-content.open {
    max-height: 1000px;
    opacity: 1;
    transform: translateY(0);
    padding: 10px;
  }

  h2 {
    margin-bottom: 15px;
  }

  .section button {
    width: 100%;
    text-align: left;
    padding: 10px;
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
    display: flex;
    align-items: center;
  }

  .section button:hover {
    background-color: #e0e0e0;
  }

  .toggle-text {
    margin-right: 10px;
    font-weight: bold;
  }

  .toggle-text.show {
    color: #7aa2f7;
  }

  .toggle-text.hide {
    color: #ff757f;
  }

  ul {
    list-style-type: none;
    padding-left: 0;
  }

  li {
    margin-bottom: 5px;
    font-family: "Ubuntu";
  }

  .ex-card {
    border: 1px solid #ddd;
    padding: 16px;
    margin: 16px 0;
    background-color: #f9f9f9;
  }

  .search-options {
    display: flex;
    justify-content: space-between;
  }

  .option-group {
    width: 48%;
  }

  .option-group h4 {
    margin-bottom: 5px;
  }

  .option-group ul {
    list-style-type: none;
    padding-left: 0;
    margin: 0;
  }

  .option-group li {
    margin-bottom: 3px;
    font-size: 0.9em;
  }
</style>



