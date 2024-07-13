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
  import '../app.css';


  // for type safety, define the Navlink object for loop the routes
  interface NavLink {
    href: string;
    label: string;
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
                <form class="logout" action="/logout" method="POST">
                    <button type="submit">Log Out</button>
                </form>
          {/if}
      </nav>

      {#if $page.data.user}
          {#if userRole === 'ADMIN' || userRole === 'DATA'}
              <hr>
              <h2>Data Upload</h2>
              <DataUpload />
          {/if}
          {#if ['ADMIN', 'DATA', 'SALE'].includes(userRole)}
              <hr>
              <h2>Search</h2>
              <SearchByValue />
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
      <UserWindow />
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
    display: flex;
    width: 100%;
    max-width: 1500px;
    margin: 0 auto;
    gap: 5rem;
  }

  .left-layout {
    flex: 1;
    min-width: 0; /* This prevents flex items from overflowing */
  }

  .right-layout {
    width: 470px; /* Increased from 450px to allow for shadow */
    flex-shrink: 0;
    box-sizing: border-box;
    position: sticky;
    top: 20px; /* Adjust this value to set how far from the top it sticks */
    height: calc(100vh - 40px); /* Full viewport height minus top and bottom margin */
    overflow-y: auto; /* Allow scrolling within the left layout if content overflows */
  }



  .auth-section {
    display: flex;
    justify-content: left;
    gap: 10px;
    margin: 1rem 0rem;
    padding: 1rem 0 1rem 0;
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
