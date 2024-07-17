


<script lang="ts">
  import { page } from '$app/stores';
  import { writable, derived, get } from 'svelte/store';
  import { API_ENDPOINTS } from '../utils/api';

  let exchangeRate = writable(false);
  let workflowToken = writable(false);
  let sampleToken = writable(false);

  // New exchange rate related stores
  let exchange_rate = writable(null);
  let error = writable('');

  const sectionHeights = {
    exchangeRateSection: 200,
    workflowTokenSection: 200,
    sampleTokenSection: 200
  };

  const totalHeight = derived(
    [exchangeRate, workflowToken, sampleToken],
    ([$exchangeRate, $workflowToken, $sampleToken]) => {
      let height = 0;
      if ($exchangeRate) height += sectionHeights.exchangeRateSection;
      if ($workflowToken) height += sectionHeights.workflowTokenSection;
      if ($sampleToken) height += sectionHeights.sampleTokenSection;
      return height;
    }
  );

  const toggleExchangeRate = async () => {
    exchangeRate.update(n => !n);
    if (get(exchangeRate) && !get(exchange_rate)) {
      await fetchExchangeRate();
    }
  };
  const toggleWorkflowToken = () => workflowToken.update(n => !n);
  const toggleSampleToken = () => {
    sampleToken.update(n => !n);
    if (get(sampleToken) && !get(fetched)) {
      fetchSampleTokens();
    }
  };

  const fetchedSampleTokens = writable([]);
  let who = writable('');
  let fetched = writable(false);

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
      fetchedSampleTokens.set(result.sample_tokens.reverse());
      fetched.set(true);
      who.set(result.username === user.name ? 'you' : result.username);
    } catch (error) {
      console.error("Error fetching sample tokens:", error);
    }
  }

  const latestTokens = derived(fetchedSampleTokens, $tokens => $tokens.slice(0, 9));
  const hasMoreTokens = derived(fetchedSampleTokens, $tokens => $tokens.length > 9);

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

  function formatTimestamp(timestamp: number): string {
    const date = new Date(timestamp * 1000); // Convert seconds to milliseconds
    return date.toLocaleString(); // Format date and time
  }
</script>

{#if $page.data.user}
  <div class="user-window">
    <h2>Dashboard</h2>
    <p>Welcome, {$page.data.user.name}!</p>
    
    <div class="section">
      <button on:click={toggleExchangeRate}>
        {$exchangeRate ? 'Hide' : 'Show'} Exchange Rate
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
        {$workflowToken ? 'Hide' : 'Show'} Workflow Id
      </button>
      <div class="section-content" class:open={$workflowToken}>
        <h3>Section 2</h3>
        <p>Content for Section 2...</p>
      </div>
    </div>

    <div class="section">
      <button on:click={toggleSampleToken}>
        {$sampleToken ? 'Hide' : 'Show'} Sample Tokens
      </button>
      <div class="section-content" class:open={$sampleToken}>
        <h3>Sample Tokens</h3>
        <ul>
          {#if $hasMoreTokens}<li>...</li>{/if}
          {#each $latestTokens as token, index}
            <li>{$who}: {token}</li>
            {#if index === $latestTokens.length - 1}
              <p>(latest)</p>
            {/if}
          {/each}
        </ul>
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
    width: 85%;
    max-width: 600px;
    margin: 0 auto;
    background-color: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    box-sizing: border-box;
  }

  .section {
    width: 90%;
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

  button {
    width: 100%;
    text-align: left;
    padding: 10px;
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  button:hover {
    background-color: #f0f0f0;
  }

  ul {
    list-style-type: none;
    padding-left: 0;
  }

  li {
    margin-bottom: 5px;
  }

  .ex-card {
    border: 1px solid #ddd;
    padding: 16px;
    margin: 16px 0;
    background-color: #f9f9f9;
  }
</style>
