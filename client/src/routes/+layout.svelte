<!-- 
• writing typescript you need to make extra modification, at least in neovim svelte project 
• select the option that you are going to write typescript, and setup tsconfig.json
    "plugins": [
        {
            "name": "typescript-svelte-plugin"
        }
    ]

-->

<script lang="ts">
  import { userRoles } from "$lib/utils/vars";
  import { page } from '$app/stores';
  import Header from "$lib/components/Header.svelte";
  import UserWindow from '$lib/components/UserWindow.svelte';
  import DataUpload from '../lib/components/DataUpload.svelte';
  import SearchByValue from '../lib/components/SearchByValue.svelte';
  import EstPrice from "$lib/components/EstPrice.svelte";
  import '../app.css';


  // Invoice Generation Step 
  import Invoice from '$lib/components/Invoice.svelte';

  // WorkFlow
  import WorkFlow from '$lib/components/WorkFlow.svelte';

  // excel 
  import SimpleExcel from '$lib/components/SimpleExcel.svelte';


  // for type safety, define the Navlink object for loop the routes
  interface NavLink {
    href: string;
    label: string;
  }


  // whether to show workflow, let user decide 
  let showWorkflow = false;

  function toggleWorkflow() {
    showWorkflow = !showWorkflow;
  }


  // Helper function to capitalize first letter
  const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

  /* 
  Function to check if the current user has access to a specific role's route 
  1) "||" this is a "or" operator 
  2) role variable are strings in roles array, userRole is taken from local.user.role
  3) if the userRole === 'ADMIN', function evaluate to true 
  4) if userRole === role provided, then also true 
  e.g.
      hasAccess('admin', 'ADMIN')  // returns true  (first condition is true)     -- 1
      hasAccess('data', 'ADMIN')   // returns true  (first condition is true)     -- 2
      hasAccess('data', 'DATA')    // returns true  (second condition is true)    -- 3
      hasAccess('admin', 'DATA')   // returns false (both conditions are false)   -- 4
      hasAccess('sale', 'SALE')    // returns true  (second condition is true)    -- 5
      hasAccess('user', 'SALE')    // returns false (both conditions are false)   -- 6
  */
  const hasAccess = (role: string, userRole: string) => 
    userRole === 'ADMIN' || userRole === role.toUpperCase();


  // userRole now become reactive, updates the userRole whenever it changes
  $: userRole = $page.data.user?.role || '';


  // dollars sign($) is a reactive declaration ==> meaning anything of right hand side of the "equation" changes 
  // the entire expression will be re-evaluate
  $: navLinks = userRoles
    .filter(role => hasAccess(role, userRole))      // filter will loop every elements, evaluate them all
    .map(role => ({                                 // create new array keep the evaluation == true
      href: `/${role.toLowerCase()}`,               // parse the role for links
      label: capitalize(role)
    })) as NavLink[];                               // into a NavLink type array
                                                    /* 
                                                        say for example, if you are admin, role has 4 elements inside 
                                                        then you will be evaluated 4 times, like --1 --2 --3, etc above
                                                        only the evaluation = true will be kept in the NavLink[]
                                                    */
</script>




<svelte:head>
    <title>SH System</title>
</svelte:head>



<main>
  <div class="main-layout">
    <div class="left-layout">

      <Header />
      <hr>
      <nav>
          {#if !$page.data.user}
              <div class="auth-section">
                  <!-- this is for authentication route clickable button -->
                  <a href="/login">Login</a>
                  <a href="/register">Register</a>
              </div>
          {:else}
              <div class="auth-section">
                {#each navLinks as { href, label }}
                    <a {href}>{label}</a>
                {/each}
              </div>
              <div class="logout-section">
                <form class="logout" action="/logout" method="POST">
                    <button type="submit">Log Out</button>
                </form>
              </div>
          {/if}
      </nav>

      {#if $page.data.user}
          {#if userRole === 'ADMIN' || userRole === 'DATA'}
              <hr>
              <h2>Data Upload</h2>
              <br>
              <DataUpload />
          {/if}
          {#if ['ADMIN', 'DATA', 'SALE'].includes(userRole)}
              <br>
              <hr>
              <h2>Search</h2>
              <SearchByValue />

              <!-- this is sampling -->
              <SearchByValue searchOption="sampling"/>
              <!-- invoice generation -->
              <Invoice />

              <hr>
              <br>


              <SimpleExcel />

              <hr>
              <br>

              <EstPrice />

              <hr>
              <br>

              <button on:click={toggleWorkflow}>
                {showWorkflow ? 'Hide Workflow' : 'Show Workflow'}
              </button>

              {#if showWorkflow}
                <WorkFlow user={$page.data.user}/>
              {/if}

              <hr>
              <br>
          {/if}
          {#if userRole === 'SALE'}
              <hr>
              <h2>Sampling (Prototype)</h2>
              <!-- Add Sampling component here when it's ready -->
              <hr>
              <h2>Invoice</h2>
              <!-- Add Invoice component here when it's ready -->
          {/if}
      {/if}

      <slot />
    </div>

    <div class="right-layout">
      <div class="user-window-wrapper">
        <UserWindow />
      </div>
    </div>
  </div>
</main>





<style>
 
  /*
  current version have a problem, when whole .right-layout reach the bottom 
  the sticky effect will be gone, so the height of the .right-layout need to be 
  think of
  */


  .main-layout {
    --main-padding: 20px 60px;
    --right-width: 450px;
    --gap: 8rem;

    display: flex;
    width: calc(100% - (var(--main-padding) * 2));
    max-width: 2000px;
    margin: 0 auto;
    padding: var(--main-padding);
    gap: var(--gap);
    box-sizing: border-box;
  }

  .left-layout {
    /* flex: none; */
    /* setting flex = 1 will take up all space after left with .right-layout */
    flex: 1;
    min-width: 0;       /* this prevernt flex items from overflowing */
    width: calc(100% - var(--right-width) - var(--gap)); /* subtract right layout width and gap */
  }


  .right-layout {
    width: var(--right-width);
    flex-shrink: 0;
  }


  .user-window-wrapper {
    position: sticky;
    top: 20px;
    max-height: calc(100vh - 40px);
    overflow-y: auto;
  }

  .auth-section {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 1rem 0rem;
    padding: 1rem 0 1rem 0;
  }

  .logout-section {
    display: flex;
    justify-content: center;
  }

  a {
    font-family: "Ubuntu";
    padding: 10px;
  }

  a:hover {
    color: var(--color-hyperlink);
  }

  h2 {
    margin: 10px 0px;
  }




</style>
