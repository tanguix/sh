
<script lang="ts">
    import { page } from '$app/stores';                     
    import { writable, derived, get } from 'svelte/store';  
    import { API_ENDPOINTS, constructUrl } from '../utils/api.ts';


    // Reactive variables for toggling each section
    let section1Open = writable(false);
    let section2Open = writable(false);
    let sampleToken = writable(false);

    // Heights for each section when open
    const sectionHeights = {
        section1: 200,
        section2: 200,
        sampleTokenSection: 200
    };

    // Derived store to calculate total height needed
    const totalHeight = derived(
        [section1Open, section2Open, sampleToken],
        ([$section1Open, $section2Open, $sampleToken]) => {
            let height = 0;
            if ($section1Open) height += sectionHeights.section1;
            if ($section2Open) height += sectionHeights.section2;
            if ($sampleToken) height += sectionHeights.sampleTokenSection;
            return height;
        }
    );

    // Functions to toggle each section
    const toggleSection1 = () => {
        section1Open.update(n => !n);
    };
    const toggleSection2 = () => {
        section2Open.update(n => !n);
    };
    const toggleSampleToken = () => {
        sampleToken.update(n => !n);
        if (get(sampleToken) && !get(fetched)) {
            fetchSampleTokens();
        }
    };

    // Reactive variable to store fetched sample tokens
    const fetchedSampleTokens = writable([]);
    let who = writable('');         
    let fetched = writable(false);  // Flag to indicate whether the data has been fetched

    // Function to fetch sample tokens
    async function fetchSampleTokens() {
        const user = get(page).data.user;
        const username = user.name;

        if (!user) {
            console.log("User not defined");
            return;
        }

        const payload = {
            name: user.name,
            role: user.role
        };

        try {
            // create endpoint: API_ENDPOINTS.FETCH_SAMPLE_TOKEN
            const response = await fetch(API_ENDPOINTS.FETCH_SAMPLE_TOKEN, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('Failed to fetch sample tokens');
            }

            const result = await response.json();
            fetchedSampleTokens.set(result.sample_tokens.reverse()); // Reverse the order
            fetched.set(true);  // Set the flag to true after fetching data

            // Assign username for display 
            if (result.username === username) {
                who.set('you');
            } else {
                who.set(result.username);
            }

        } catch (error) {
            console.error("Error fetching sample tokens:", error);
        }
    }

    // Derived store to get the latest 9 tokens and a flag for more tokens
    const latestTokens = derived(fetchedSampleTokens, $fetchedSampleTokens => {
        return $fetchedSampleTokens.slice(0, 9); // Take the first 9 tokens after reversing
    });

    const hasMoreTokens = derived(fetchedSampleTokens, $fetchedSampleTokens => {
        return $fetchedSampleTokens.length > 9;
    });
</script>

{#if $page.data.user}
  <div class="floating-window" style="max-height: {200 + $totalHeight}px;">
    <p>Welcome {$page.data.user.name}!</p>
    <div class="section">
      <button class="header btn" on:click={toggleSection1} aria-expanded={$section1Open}>
        {#if $section1Open}
          Close Section 1
        {:else}
          Open Section 1
        {/if}
      </button>
      <div class={`content ${$section1Open ? 'visible-content opening' : 'hidden-content closing'}`}>
        <br>
        <h3>Section 1</h3>
        <p>Some other content...</p>
      </div>
    </div>
    <div class="section">
      <button class="header btn" on:click={toggleSection2} aria-expanded={$section2Open}>
        {#if $section2Open}
          Close Section 2
        {:else}
          Open Section 2
        {/if}
      </button>
      <div class={`content ${$section2Open ? 'visible-content opening' : 'hidden-content closing'}`}>
        <br>
        <h3>Section 2</h3>
        <p>Some other content...</p>
      </div>
    </div>
    <div class="section">
      <button class="header btn" on:click={toggleSampleToken} aria-expanded={$sampleToken}>
        {#if $sampleToken}
          Close Section
        {:else}
          Sample Token
        {/if}
      </button>
      <div class={`content ${$sampleToken ? 'visible-content opening' : 'hidden-content closing'}`}>
        <br>
        <h3>Sampling Token</h3>
        <ul>
          {#if $hasMoreTokens}
            <li>...</li>
          {/if}
          {#each $latestTokens as token, index}
            <li>{$who}: {token}</li><p>{index === $latestTokens.length - 1  ? ' (latest, some error on ordering)' : ''}</p>
          {/each}
        </ul>
      </div>
    </div>
  </div>
{:else}
  <div class="floating-window">
    <p>User Not Login</p>
  </div>
{/if}

<style>
  .floating-window {
    margin-top: 2rem;
    width: 450px;
    background-color: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    overflow: hidden;
    transition: max-height 0.3s ease, opacity 0.3s ease;
  }

  .header {
    cursor: pointer;
  }

  .content {
    overflow-y: auto;
    transition-property: max-height, opacity;
  }

  .section {
    margin-top: 10px;
    margin-bottom: 10px;
  }

  .hidden-content {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
  }

  .visible-content {
    max-height: 200px; /* Adjust based on content size */
    opacity: 1;
  }

  .opening {
    transition-duration: 0.3s;
    transition-timing-function: ease-in;
  }

  .closing {
    transition-duration: 0.4s;
    transition-timing-function: ease-out;
  }
</style>
